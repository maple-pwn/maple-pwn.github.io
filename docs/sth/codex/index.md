# Codex CLI 卡死、Ctrl+C 无法终止？一次Codex CLI排查

最近在使用 **Codex CLI** 时遇到一个非常诡异的问题：

- `codex exec` 卡死
- `Ctrl+C` 无法终止
- CLI 没有任何输出

最后发现根本原因其实很简单,也很诡异：

**网络无法直连 chatgpt.com，需要代理。**（为什么网络代理问题会导致 `Ctrl+C` 失败啊）

排查过程涉及 **WebSocket、网络超时、代理配置、SIGINT 信号机制**，还是很值得记录一下。

---


## 一：问题现象

运行 Codex：


```
codex exec --skip-git-repo-check "say hi"
```

终端停在：


```
connecting to websocket:
wss://chatgpt.com/backend-api/codex/responses
```

之后没有任何输出。

尝试终止：


```
Ctrl+C
Ctrl+C
Ctrl+C
```

终端只会打印：


```
^C^C^C
```

但 **进程不会退出**。

---


## 二：排查过程


### 1 先验证基础网络

首先测试 HTTPS：


```bash
curl -I --connect-timeout 5 https://chatgpt.com
```

结果：


```
curl: (28) Failed to connect to chatgpt.com port 443
```

说明：

**当前网络无法直连 chatgpt.com。**

---


### 2 使用 WebSocket 客户端测试

Codex 使用 WebSocket，因此测试：


```bash
websocat -v wss://chatgpt.com/backend-api/codex/responses
```

结果：


```
Failure during connecting TCP: Operation timed out
```

说明：

**TCP 都连不上，更不用说 WebSocket。**

---


### 3 添加代理

本地代理端口：


```
127.0.0.1:7897
```

设置代理：


```
export HTTPS_PROXY=http://127.0.0.1:7897
export HTTP_PROXY=http://127.0.0.1:7897
export ALL_PROXY=http://127.0.0.1:7897
```

再次测试：


```
codex exec --skip-git-repo-check --json "say hi"
```

成功返回：


```json
{"type":"thread.started"}
{"type":"turn.started"}
{"type":"item.completed","text":"hi"}
```

问题解决。

---


## 三：写入 zsh 配置

为了避免每次手动设置代理，可以写入 `~/.zshrc`：


```
# proxy
export HTTP_PROXY="http://127.0.0.1:7897"
export HTTPS_PROXY="http://127.0.0.1:7897"
export ALL_PROXY="http://127.0.0.1:7897"

export http_proxy=$HTTP_PROXY
export https_proxy=$HTTPS_PROXY
export all_proxy=$ALL_PROXY
```

重新加载：


```bash
source ~/.zshrc
```

测试：


```bash
curl -I https://chatgpt.com
```

返回：


```
HTTP/2 403
```

说明代理已经生效（403 来自 Cloudflare）。

---


## 四：关键问题：为什么 Ctrl+C 无法终止？

这其实是 **网络系统调用 + 信号机制** 的经典问题。

按 Ctrl+C 时，终端会发送：


```
SIGINT
```

程序需要：

1. 捕获信号
2. 取消任务
3. 退出

但如果程序正在执行：


```
connect()
```

系统调用可能会 **无法被信号中断**。

例如：


```
codex
  ↓
connect(chatgpt.com:443)
  ↓
网络丢包
  ↓
TCP SYN retry
  ↓
系统等待超时
```

在这种情况下：


```
Ctrl+C → SIGINT
```

信号虽然被收到，但 **connect() 没返回**。

所以程序看起来像：


```
^C
^C
^C
```

但仍然卡住。

---


## 五：为什么代理能解决？

没有代理时：


```
Codex
  ↓
chatgpt.com
  ↓
网络阻断
```

连接失败。

使用代理后：


```
Codex
  ↓
127.0.0.1:7897
  ↓
代理服务器
  ↓
chatgpt.com
```

本地连接：


```
127.0.0.1
```

几乎是瞬间完成。

之后由代理负责访问外网。

因此 Codex 的 WebSocket 能正常建立。

---


## 六：最终验证

代理开启后：


```
codex exec "say hi"
```

输出：


```
codex
hi
```

说明 CLI 已恢复正常。

---


## 结论

这次问题本质是：


```
网络无法直连 chatgpt.com
        ↓
WebSocket 连接卡死
        ↓
connect() 阻塞
        ↓
Ctrl+C 无法终止
        ↓
配置代理解决
```

看似是 **Codex CLI Bug**，其实是 **网络问题**，真难蚌哦。
