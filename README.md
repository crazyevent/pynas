# 高性能http文件共享服务

## 优势
- 单文件特别小巧
- 支持多目录共享
- 支持目录加密
- 多用户并发

## 使用前提
	
	最好家里网络有IPV4公网地址，检查是否有公网地址的方式就是看路由器拨号连接获取的IP是否可以外网访问, 如果有DDNS，也可以把IPV6地址解析到路由上，然后配置端口转发；

## 使用方法

### Windows 用户

- 前往 [https://www.python.org/]() 下载并安装python

- 启动cmd.exe，进入源码目录运行命令
```
	pip install -r requirements.txt
```	
- 安装完依赖后，修改配置文件config.json，使用文本编辑器打开即可
```
	users: user用户名, passwd密码
	listen: 需要开启几个服务就配置几个addr和port，主要给一些多出口用户，通常不需要修改；
	www: 需要分享几个目录就配置几个name和path，其中name可以自定义，path是本机的物理路径，owner文件夹归属用户，默认为*代表所有用户共享，用户名用,分割;
```
- 双击 run.bat

- 路由器上配置端口转发

### Linux 用户

- 自由发挥