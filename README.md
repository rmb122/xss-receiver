# XSS Receiver

基于 Flask 的 xss 接收 + payload 管理平台,  

主要功能:  
* 在特定路由上保存访问历史以及携带数据
* 命中特定路由时发送邮件
* 动态切换路由及其对应的 payload 文件
* 管理、编辑 payload
* Docker 快速部署

## 安装

1. clone

```sh
git clone https://github.com/rmb122/xss-receiver.git
```

2. 安装

修改 docker-compose.yml 里面的 environment 成想要的配置  
* `URL_PREFIX` 为管理面板的路径, 建议修改为不易猜出的路径, 例如 `/e7ca70a07ec48cdc74c2217f55d08c383d37e62d`
* `LOGIN_PASSWORD` 为登录密码, 其他可以不用修改

然后
```sh
sudo docker-compose up -d
```
稍等一会等待数据库初始化即可.

注意: 
* 访问需要访问完整的路径, 假设设置管理面板路径为 /test233, 那么需要访问 https://example.com/test233/index.html. 访问 https://example.com/test233/ 会返回 404. 
* 随意用户名 + 刚刚设置的密码就可以登录. 用户名仅仅只是为了好看 (逃  

3. 快速开始

在`文件`中新建或上传一个任意名字的文件, 之后在`规则`中设置一个进行记录的路由, 比如 `/`, 并将映射文件设为刚刚上传的文件.  
然后访问网站根目录, 可以看到返回的是刚刚设置的文件, 并且记录了访问所携带的数据.

## 使用 Nginx 反代

如果想与其他网站共存, 可以采用 nginx 反代, 修改 docker-compose.yml 里的 BEHIND_PROXY 为 True, 然后将客户端 IP 通过 X-Real-IP 发给后端即可.  
Nginx 配置可参考 `docker/reverse_proxy.conf`.

## 使用截图

![](https://i.loli.net/2019/12/30/eqgI7ZL8TlJ2DsY.png)
![](https://i.loli.net/2019/12/30/zsopwQVHmBiFaxh.png)
![](https://i.loli.net/2019/12/30/FNMr5ZuOiaVgQmx.png)
