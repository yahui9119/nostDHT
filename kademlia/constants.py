#encoding: utf-8

#起始node
BOOTSTRAP_NODES = [("router.bittorrent.com", 6881),("dht.transmissionbt.com", 6881)] 

#网络超时
KRPC_TIMEOUT = 10 #10s

#进行下一个find_node请求前的暂停时间
NEXT_FIND_NODE_INTERVAL = 25 / 1000.0 #25ms

#每bucket最多含多少node
K = 8

#传输ID的长度
TID_LENGTH = 3

#token的长度
TOKEN_LENGTH = 4

#生成多少个node实例, 请根据自身网络状况调试. 默认值是在带宽: 100M, CPU: 单核, 内存: 512M 的Xen VPS运行良好
NODE_COUNT = 5