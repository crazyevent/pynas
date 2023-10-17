# 高性能http文件共享服务

## 优势
- 单文件服务
- 支持多目录共享
- 支持目录加密
- 多用户并发
- 支持H5在线播放

## 使用前提
	
	最好家里网络有IPV4公网地址，检查是否有公网地址的方式就是看路由器拨号连接获取的 IP 是否可以外网 ping 通, 如果有 DDNS，也可以把 IPV6 地址解析到路由上，然后配置端口转发；

## 使用方法

### Windows 使用方式

- 前往 [https://www.python.org/]() 下载并安装python

- 启动cmd.exe，进入源码目录运行命令
```
	pip install -r requirements.txt
```	
- 安装完依赖后，修改配置文件config.json，使用文本编辑器打开即可
```
	ext_filter: 按文件扩展名过滤，以","分隔，例如".txt,.jpg"，也可以配置在www项的单个目录内
	users: user 用户名, passwd 密码
	listen: 需要开启几个服务就配置几个 addr 和 port，主要给一些多出口用户，通常不需要修改；
	www: 需要分享几个目录就配置几个 name 和 path，其中 name 可以自定义，path 是本机的物理路径，owner 文件夹归属用户，默认为 * 代表所有用户共享，用户名用","分隔;
```
- 双击 run.bat

- 路由器上配置端口转发

### Linux 使用方式

- 参照 Windows 自由发挥

### TODO

- 支持PNP端口映射
- 接入以太坊网络，发布节点
- 网页爬虫并支持m3u8下载
- 接入DHT网络，并支持BT下载
- 支持基于UDP的SCTP下载协议
- 支持webrtc