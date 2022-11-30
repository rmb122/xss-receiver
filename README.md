# XSS Receiver

基于 Sanic 的 xss 接收 + payload 管理平台,

主要特点:

* 在特定路由上保存访问历史以及携带数据
* 命中特定路由时发送邮件
* 动态切换路由及其对应的 payload 文件
* 根据设置, 响应可以通过 js 脚本动态生成
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
* `BEHIND_PROXY` 决定是否从 `X-Real-IP` 和 `X-Real-Port` Header 中取值作为客户端 IP, 端口

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

### 动态脚本

如果将规则类型设置为动态脚本, 那么规则所指向的文件会被作为 js 脚本, 使用 duktape 来运行, 语法和相关 API 可以参考[官方文档](https://duktape.org/guide.html),  
需要注意 duktape 语法为 ES5, 不支持 ES6 及其之后的语法, 例如 `let` 声明变量等等, 这里不再对 js 运行时额外进行介绍.  
模版中会被注入常用的变量和函数, 相关实现在 `xss_receiver/script_engine.py`

这里介绍相关 API 的使用方法

#### request

获取请求信息, 需要注意获取请求体时, 因为不同 Content-Type 需要不同解析方式, 所以均使用函数调用.  
另外 bytes 对应 Buffer 或者 Duktape.Buffer.

| 变量名                        | 类型                                | 备注                                                                                                                  |
| ----------------------------- | ----------------------------------- | --------------------------------------------------------------------------------------------------------------------- |
| request.client_ip             | str                                 | 客户端 IP                                                                                                             |
| request.client_port           | int                                 | 客户端端口                                                                                                            |
| request.method                | str                                 | HTTP 方法                                                                                                             |
| request.path                  | str                                 | 访问的路径                                                                                                            |
| request.header                | Dict[str, str]                      | HTTP 请求头, 键名小写                                                                                                 |
| request.header_list           | Dict[str, List[str]]                | HTTP 请求头, 但是重复的不会被丢弃, 而是被保存为列表                                                                   |
| request.arg                   | Dict[str, str]                      | HTTP GET 参数                                                                                                         |
| request.arg_list              | Dict[str, List[str]]                | HTTP GET 参数, 但是重复的不会被丢弃, 而是被保存为列表                                                                 |
| request.get_body              | Callable[[], str]                   | 原始的 body                                                                                                           |
| request.get_raw_body          | Callable[[], bytes]                 | 原始的 body, 但是使用 Duktape.Buffer 返回原始二进制                                                                   |
| request.get_json              | Callable[[], Any]                   | body 解析为 json 后的结果                                                                                             |
| request.get_form              | Callable[[], Dict[str, str]]        | body 解析为 urlencode 后的结果                                                                                        |
| request.get_form_list         | Callable[[], Dict[str, List[str]]]  | body 解析为 urlencode 后的结果, 但是重复的不会被丢弃, 而是被保存为列表                                                |
| request.get_file              | Callable[[], Dict[str, File]        | body 解析为文件后的结果, File 类型的描述 在下方                                                                       |
| request.get_file_list         | Callable[[], Dict[str, List[File]]] | body 解析为文件后的结果, 但是重复的不会被丢弃, 而是被保存为列表                                                       |
| request.get_file_by_name      | Callable[[str], File]               | body 解析为文件后的结果, 额外增加一个参数为键名, 相比获取所有文件, 可能速度更快                                       |
| request.get_file_list_by_name | Callable[[str], List[File]]         | body 解析为文件后的结果, 额外增加一个参数为键名, 相比获取所有文件, 可能速度更快, 且重复的不会被丢弃, 而是被保存为列表 |

```python
class File:
    filename: str
    type: str
    content: str
    raw_content: bytes
```

#### response

发送响应信息

| 变量名                   | 类型                                         | 备注                                                                                                            |
| ------------------------ | -------------------------------------------- | --------------------------------------------------------------------------------------------------------------- |
| response.set_status_code | Callable[[int], None]                        | 设置响应状态代码                                                                                                |
| response.set_header      | Callable[[str, Union[str, List[str]]], None] | 设置响应头, 参数为响应头的 name 和 value, 其中 value 可以为字符串列表, 代表设置多个 header                      |
| response.send            | Callable[[str, Union[str, bytes]], None]     | 设置响应体, 其中参数可以为 Buffer 或者 Duktape.Buffer, 代表直接发送二进制内容. 多次调用此函数, 结果会按顺序拼接 |

#### storage

操作文件管理目录下的文件

| 变量名                   | 类型                                                     | 备注                                                                                                          |
| ------------------------ | -------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------- |
| storage.list_directory   | Callable[[str], List[str]]                               | 列目录                                                                                                        |
| storage.create_directory | Callable[[str], None]                                    | 创建目录                                                                                                      |
| storage.remove_directory | Callable[[str, Optional[bool]], None]                    | 删除目录, 第二个参数代表是否递归删除                                                                          |
| storage.read_file        | Callable[[str, Optional[str]], Union[str, bytes]]        | 读取文件, 第二个参数为读取模式, 如果为 "b", 代表文件内容以二进制形式返回                                      |
| storage.write_file       | Callable[[str, Union[str, bytes], Optional[bool]], None] | 写入文件, 第二个参数可以为 Buffer 或者 Duktape.Buffer, 代表写入二进制. 而第三个参数代表是否以 append 模式写入 |
| storage.remove_file      | Callable[[str], None]                                    | 删除文件                                                                                                      |

#### 其他

| 变量名  | 类型                    | 备注                                                           |
| ------- | ----------------------- | -------------------------------------------------------------- |
| require | Callable[[str], Module] | 类似 node, 可以通过此函数 require 文件管理目录下的其他 js 文件 |

#### 例子

通过脚本引擎功能实现大文件分片上传

```js
var file = request.get_file();
var fileKeys = Object.keys(file);
if (fileKeys.length > 0) {
    var key = fileKeys[0];
    var filename = file[key].filename.split('/');
    filename = filename[filename.length - 1];
    var content = file[key].raw_content;
    storage.write_file(filename, content, true);
}
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

由于前端采用 table 组件, 无法显示一层以上的目录, 所以目前暂不支持一层以上目录的创建. 即使使用 js 脚本创建, 也是无法在前端显示的.  
如果需要往文件夹中写入文件直接在新建的文件名前面添加目录名即可, 例如在 `test` 目录下新建 `123.txt`, 输入的文件名为 `test/123.txt`

### DNS Log

因为很多 Linux 都会在本地启动一个 DNS 服务器, 直接监听 `0.0.0.0:53` 不会成功, 所以默认在 docker-compose 中不启用 DNS Log, 开启这个功能需要解除注释后将 `53:53/udp` 改为 `x.x.x.x:53:53/udp` 
其中 `x.x.x.x` 为除了 `0.0.0.0` 之外的监听的 IP 地址  

目前还实现了一个简易的响应系统, 可以用于 dns rebinding, 响应结果取决于请求的域名中的信息, 格式为  
```
((ipv4_addr|ipv6_addr)\.(time\.)?){1,}xxx\.com
```
其中 `ipv4_addr` 和 `ipv6_addr` 需要将地址中对应的 . 或者 : 替换成下划线, 另外 ipv6 地址不支持通过 :: 缩写.  
例如: 
`1_1_1_1.2.2_2_2_2.ffff_ffff_ffff_ffff_ffff_ffff_ffff_ffff.xxx.dns.sss.com` 前两次查询会返回 `1.1.1.1`, 第三次查询会返回 `2.2.2.2`, 第四次会返回 `ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff`, 而第五次又会重新开始, 返回 `1.1.1.1`

另外可以配置 `DNS_KEY`, 系统会检查请求的域名中是否存在配置的 `DNS_KEY`, 例如配置成 `DNS_KEY=dns` 那么 `1_1_1_1.dns.xx.com` 才会返回结果, `1_1_1_1.xx.com` 是不行的  

用于统计次数的缓存采用 LRU, 大小默认 1024, cache 的 key 是 `qname + "@" + remote_ip`  

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
