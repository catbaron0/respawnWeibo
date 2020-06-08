# 备份/克隆微博

## 功能
### 登陆微博
1. 先在`config.py`中设置用户名和密码
    ```
    USERNAME="example@example.com"
    PASSWD="password"
    ```
2. 执行
```
python3 user_info.py
```
脚本会生成`sender.sess`，并会输出`containerID` 和 `uid`

### 备份微博
执行
```
python3 cache.py -cid containerID
```
其中 `CID` 为刚才输出的 `containerID` 。

执行之后微博会被下载到 cached 路径下，每一页(10条微博)缓存为一个json文件。

### 克隆微博
1. 将`config.py`中的用户名和密码更新为目标账号
2. 执行
```
python3 user_info.py
```
3. 执行
```
python3 respawn.py -f cached/8.txt  -u uid -c 9
```
就会自动将缓存到`8.txt`中的微博发布到`config.py`中设置的微博账号中。

对于转发的微博，会优先转发原微博；如果转发失败，则会尝试按照原创微博
的方式将原微博内容一起发布。

`respawn.py`的参数说明如下：
* ` -f JSON_FILE`, 缓存的json文件.
* ` -s SESSION_FILE`, 指定session文件可避免反复登陆
* ` -u UID`, 用户ID，可通过 `user_info.py` 查看
* ` -c CONTINUE` 从文件中的某一条微博开始发布。
* ` -ft`, 强制用原创微博的方式克隆转发微博。

### 说明
1. cache.py 代码修改自 https://github.com/yekingyan/Weibo/blob/master/Weibo.py
2. weibo/ 的代码修改自 https://github.com/chaolongzhang/sinaWeibo
3. 由于微博对发布频率的限制，目前设置为约30s发送一条
4. 本项目不稳定

## License

Published under GNU GPLv3 License. See the LICENSE file for more.

## 捐赠

如果您觉得该工具对你有帮助，欢迎给我一定的捐赠。

**支付宝扫码捐赠**

![](./doc/alipay.jpg)

**微信扫码捐赠**

![](./doc/wechat.jpg)

