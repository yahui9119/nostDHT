nostDHT:
======
1. 屎上代码最简单的DHT爬虫, 基于twisted/Kademlia, 很适合中级者学习.
2. nostDHT就是no standard DHT的简写, 顾名思义就是相对于[simDHT](https://github.com/laomayi/simDHT)来说, 跟官方协议不标准.
3. 比[simDHT](https://github.com/laomayi/simDHT)好的地方在于不需要维护路由表里的node状态, 因为永远都是最新鲜的, 且代码量更少, 每天收集的infohash数量几乎都是一样的.
4. 在内网环境下, 也许没效果, 可以的话, 尽量放在公网上, 比如买一个VPS.


依赖包:
======
1. [twisted](https://pypi.python.org/pypi/Twisted/13.2.0), twisted依赖[zope.interface](https://pypi.python.org/pypi/zope.interface/4.1.0)
2. [bencode](https://pypi.python.org/pypi/bencode/1.0)


启动*nostDHT*服务:
================
`twistd -y nostDHT.py`


停止*nostDHT*服务:
================
1. `cat twistd.pid`
2. `kill -9 PID`


配置文件:
========
`kademlia/constants.py`


其他:
====
1. 因只实现了DHT协议, 未实现种子下载, 所收集到的**infohash**将会存储在**infohash.log**文件中.
2. 种子下载可去迅雷种子库下载、使用[libtorrent](http://libtorrent.org)、实现种子协议([bep0003](www.bittorrent.org/beps/bep_0003.html), [bep0009](www.bittorrent.org/beps/bep_0009.html), [bep0010](www.bittorrent.org/beps/bep_0010.html))