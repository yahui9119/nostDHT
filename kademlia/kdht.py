#encoding: utf-8
import socket
from hashlib import sha1
from time import time

from twisted.internet import reactor
from twisted.application import internet

from krpc import KRPC
from utils import entropy, decodeNodes, encodeNodes, nodeID
from ktable import KNode, KBucket
from constants import *

def timer(step, callback, *args):
    """定时器"""
    s = internet.TimerService(step, callback, *args)
    s.startService()
    return s


class DHTClient(KRPC):
    """
    DHT客户端
    """
    def __init__(self):
        KRPC.__init__(self)
        timer(15 * 60, self.rejoinNetwork) #因为KAD每隔15分就要刷新路由表, 我就每隔15分钟更换自身Node ID. 

    def findNode(self, address):
        """
        DHT爬虫的客户端至少要实现find_node.
        此方法最主要的功能就是不停地让更多人认识自己.
        爬虫只需认识(160-2) * K 个节点即可
        """
        tid = entropy(TID_LENGTH)
        snid = self.table.nid
        msg = {
            "t": tid,
            "y": "q",
            "q": "find_node",
            "a": {"id": snid, "target": snid}
        }
        self.sendQuery(msg, address)

    def findNodeHandle(self, res):
        """
        处理find_node回应数据
        """
        try:
            nodes = decodeNodes(res["r"]["nodes"])
            for node in nodes:
                (nid, ip, port) = node
                if nid == self.table.nid: continue #不存自己
                self.table.append(KNode(nid, ip, port))

                #"等待"NEXT_FIND_NODE_INTERVAL时间后, 进行下一个find_node
                reactor.callLater(NEXT_FIND_NODE_INTERVAL, self.findNode, (ip, port))
        except KeyError:
            pass

    def joinNetwork(self):
        """加入DHT网络"""
        for address in BOOTSTRAP_NODES:
            self.resolve(address[0], address[1])
        reactor.callLater(KRPC_TIMEOUT, self.joinFailHandle)

    def resolve(self, host, port):
        """解析域名"""

        def callback(ip, port):
            """解析成功后, 开始发送find_node"""
            self.findNode((ip, port))

        def errback(failure, host, port):
            """解析失败, 再继续解析, 直到成功为止"""
            self.resolve(host, port)

        d = reactor.resolve(host)
        d.addCallback(callback, port)
        d.addErrback(errback, host, port)

    def joinFailHandle(self):
        """加入DHT网络失败, 再继续加入, 直到加入成功为止"""
        if len(self.table) == 0: self.joinNetwork()

    def rejoinNetwork(self):
        """
        更换自身node ID, 清空路由表, 再重新加入DHT网络.
        """
        self.table.nid = nodeID()
        self.table.buckets = [ KBucket(0, 2**160) ]
        self.joinNetwork()

class DHTServer(DHTClient):
    """
    DHT服务器端

    服务端必须实现回应ping, find_node, get_peers announce_peer请求
    """
    def __init__(self, fastbot):
        self.fastbot = fastbot
        self.table = fastbot.table
        DHTClient.__init__(self)

    def startProtocol(self):
        self.joinNetwork()

    def pingReceived(self, res, address):
        """
        回应ping请求
        """
        try:
            nid = res["a"]["id"]
            msg = {
                "t": res["t"],
                "y": "r",
                "r": {"id": self.table.nid}
            }
            (ip, port) = address
            self.table.append(KNode(nid, ip, port))
            self.sendResponse(msg, address)
        except KeyError:
            pass

    def findNodeReceived(self, res, address):
        """
        回应find_node请求
        """
        try:
            target = res["a"]["target"]
            closeNodes = self.table.findCloseNodes(target, 16)
            if not closeNodes: return

            msg = {
                "t": res["t"],
                "y": "r",
                "r": {"id": self.table.nid, "nodes": encodeNodes(closeNodes)}
            }
            nid = res["a"]["id"]
            (ip, port) = address
            self.table.append(KNode(nid, ip, port))
            self.sendResponse(msg, address)
        except KeyError:
            pass

    def getPeersReceived(self, res, address):
        """
        回应get_peers请求, 差不多跟findNodeReceived一样, 只回复nodes. 懒得维护peer信息
        """
        try:
            infohash = res["a"]["info_hash"]
            closeNodes = self.table.findCloseNodes(infohash, 16)
            if not closeNodes: return

            nid = res["a"]["id"]
            h = sha1()
            h.update(infohash+nid)
            token = h.hexdigest()[:TOKEN_LENGTH]
            msg = {
                "t": res["t"],
                "y": "r",
                "r": {"id": self.table.nid, "nodes": encodeNodes(closeNodes), "token": token}
            }
            (ip, port) = address
            self.table.append(KNode(nid, ip, port))
            self.sendResponse(msg, address)
        except KeyError:
            pass

    def announcePeerReceived(self, res, address):
        """
        回应announce_peer请求
        """
        try:
            infohash = res["a"]["info_hash"]
            token = res["a"]["token"]
            nid = res["a"]["id"]
            h = sha1()
            h.update(infohash+nid)
            if h.hexdigest()[:TOKEN_LENGTH] == token:
                #验证token成功, 开始下载种子
                (ip, port) = address
                port = res["a"]["port"]
                self.fastbot.downloadTorrent(ip, port, infohash)
            msg = {
                "t": res["t"],
                "y": "r",
                "r": {"id": self.table.nid}
            }
            self.sendResponse(msg, address)
        except KeyError:
            pass