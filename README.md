# XSS Receiver

基于 Sanic 的 xss 接收 + payload 管理平台,

主要特点:

* 在特定路由上保存访问历史以及携带数据
* 命中特定路由时发送邮件
* 动态切换路由及其对应的 payload 文件
* 根据设置, 响应可以通过模版动态渲染
* 管理、编辑 payload
* 额外搭载简单的 DNS Log 功能
* 多用户
* Docker 快速部署

## 部署

1. clone

```sh
git clone https://github.com/rmb122/xss-receiver.git
```

2. 安装

修改 docker-compose.yml 里面的 environment 成想要的配置

* `URL_PREFIX` 为管理面板的路径, 建议修改为不易猜出的路径, 例如 `/e7ca70a07ec48cdc74c2217f55d08c383d37e62d`
* `INIT_USER` 为初始的管理员登录帐号和登录密码, 用 `:` 分隔
* `BEHIND_PROXY` 决定是否从 `X-Real-IP` Header 中取值作为客户端 IP

然后

```sh
sudo docker-compose up -d
```

稍等一会等待数据库初始化即可.

注意:

* 访问需要访问完整的路径, 假设设置管理面板路径为 /admin_is_here, 那么需要访问 https://example.com/admin_is_here/index.html.
  访问 https://example.com/test233/ 会返回 404.

3. 快速开始

在`文件管理`中新建或上传一个任意名字的文件, 之后在`HTTP 规则`中创建一个分类, 并在分类中添加一个进行记录的路由, 比如 `/`, 并将映射文件设为刚刚上传的文件.  
然后访问网站根目录, 可以看到返回的是刚刚设置的文件, 并且在`HTTP日志`处记录了访问所携带的数据.

## 注意事项

### 动态模版

如果将规则类型设置为动态模版, 那么规则所指向的文件会被作为 jinja 模版来解析, 语法可以参考[官方文档](https://jinja.palletsprojects.com/en/3.0.x/templates/),
这里不再额外进行介绍  
模版中会被注入常用的变量和函数, 相关实现在 `xss_receiver/utils.py` 的 `generate_dynamic_template_globals` 函数

这里简单介绍变量和函数的使用方法

#### 变量

| 变量名       | 类型                         | 备注                                          |
|-----------|----------------------------|---------------------------------------------|
| client_ip | str                        | 客户端 IP                                      |
| path      | str                        | 访问的路径                                       |
| method    | str                        | HTTP 方法                                     |
| header    | Dict[str, str]             | HTTP 请求头                                    |
| arg       | Dict[str, str]             | HTTP GET 参数                                 |
| body      | str                        | 原始的 body                                    |
| file      | Dict[str, Tuple[str, str]] | 请求中的文件, key 为文件参数名, value 为文件名和临时保存文件名组成的元组 |

#### 函数

| 函数名                     | 类型                                               | 备注                                               |
|-------------------------|--------------------------------------------------|--------------------------------------------------|
| add_header              | [str, str] -> None                               | 参数为添加的 header 的 name 和 value                     |
| pop_header              | [str] -> None                                    | 需要删掉的 header 的 name                              |
| set_status              | [int] -> None                                    | 设置 HTTP status code                              |
| write_output            | [Union[byte, str, list]] -> None                 | 输入的参数会在模版渲染完成后会额外添加到输出中, 可以通过这个方式来输出正常模版无法输出的二进制 |
| list_directory          | [str] -> List[Tuple[str, bool]]                  | 输入文件夹名, 返回文件管理功能下对应的文件夹中的文件列表, 空字符 '' 代表根目录      |
| create_directory        | [str] -> None                                    | 创建的文件夹名                                          |
| delete_directory        | [str] -> None                                    | 删除的文件夹名, 会递归删除其下的文件                              |
| delete_upload_file      | [str] -> None                                    | 删除的文件名                                           |
| read_upload_file        | [str, Optional[bool]] -> Union[str, bytes]       | 读取文件, 第二个参数为是否以 bytes 类型返回文件内容                   |
| write_upload_file       | [str, Union[str, bytes], Optional[bool]] -> None | 写入文件, 第三个参数为是否 append 模式写入                       |
| get_request_upload_file | [str] -> Tuple[str, bytes]                       | 获取当前请求上传的文件内容, 输入为文件的参数名, 返回文件名和文件内容             |
| json_encode             |                                                  | 同  json.dumps                                    |
| json_decode             |                                                  | 同  json.loads                                    |
| url_encode              |                                                  | 同  urllib.parse.quote                            |
| url_decode              |                                                  | 同  urllib.parse.unquote                          |
| url_parse_qs            |                                                  | 同  urllib.parse.parse_qs                         |

#### 例子

通过模版功能实现大文件分片上传

```jinja2
{%- set upload_file = get_request_upload_file('upload') -%}
{%- if upload_file != None -%}
    {%- do write_upload_file('upload/'+upload_file[0].split('/')[-1], upload_file[1],True) -%}
{%- endif -%}
```

配合以下 shell 脚本使用
```shell
TARGETURL=http://127.0.0.1/test 
FILENAME=dump.zip
BLOCKSIZE=102400
FILESIZE=$(stat -c '%s' $FILENAME) 
BLOCKCOUNT=$(( $FILESIZE/$BLOCKSIZE+1 ))
i=0
while [ $i -ne $BLOCKCOUNT ]
do
        dd if=$FILENAME bs=$BLOCKSIZE count=1 skip=$i | curl $TARGETURL -F "upload=@-;filename=$FILENAME"
        i=$(($i+1))
done
```
将会将文件保存在文件管理页面下的 /upload 目录下  

### 文件管理

由于前端采用 table 组件, 无法显示一层以上的目录, 所以目前暂不支持一层以上目录的创建  
如果需要往文件夹中写入文件直接在新建的文件名前面添加目录名即可, 例如在 `test` 目录下新建 `123.txt`, 输入的文件名为 `test/123.txt`

### DNS Log

因为很多 Linux 都会在本地启动一个 DNS 服务器, 直接监听 `0.0.0.0:53` 不会成功, 所以默认在 docker-compose 中不启用 DNS Log, 需要使用这个功能需要将 `53:53/udp` 改为 `x.x.x.x:53:53/udp` 
其中 `x.x.x.x` 为除了 `0.0.0.0` 之外的监听的 IP 地址  

另外目前国内不允许架设私有的 DNS 服务器, 且如果要实现 dns rebinding 等功能相关逻辑过于复杂, 故系统内没有实现响应相关功能, 只实现了对请求进行记录

### 系统日志

其中除了有登录日志外, 系统和模版渲染出现的错误也会记录在其中

### 用户

系统的用户功能只在登录时使用, 没有隔离资源的作用, 只是为了方便共享平台, 避免自己的密码泄漏

### 设置

系统设置的值需要符合 JSON 语法. 如果需要关闭新消息的提醒, 也可以在此处, 需要注意此种设置是保存在 localStorage 中而不是服务端.

## 使用截图

![](https://s2.loli.net/2022/02/01/9vLcgMj4EqJRKYN.png)
![](https://s2.loli.net/2022/02/01/nGtAk1SgdVMc3Ke.png)
![](https://s2.loli.net/2022/02/01/UzJyRP5lxeKp7rX.png)
![](https://s2.loli.net/2022/02/01/JQpLYfkrBA34W1a.png)
![](https://s2.loli.net/2022/02/01/c3Wzvbn6mK4rJtA.png)
