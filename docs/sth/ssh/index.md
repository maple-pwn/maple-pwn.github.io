# 一次 WSL2 SSH 远程访问的完整排障过程


## 起点：一个看似简单的需求

故事开始于一个很常见的需求：我想在 WSL2 的 Ubuntu 环境里启动 SSH 服务，让局域网里的 Mac 能够远程连接进来。这听起来应该两分钟就能搞定了——装个 openssh-server，改改配置，启动服务，完事。

但接下来的一个小时里，我经历了从"连接超时"到"连接被拒绝"，再到"连接建立后立即断开"的完整循环，最终发现问题的根源是一个看似无关的 VPN 软件。


## 一：创建启动脚本

我首先创建了一个自动化脚本 `setup-ssh.sh`，它会检查 openssh-server 是否安装，配置 SSH 允许密码认证和公钥认证，然后启动服务。脚本看起来很完美，逻辑也很清晰：检查安装 → 配置文件 → 启动服务 → 显示连接信息。

运行脚本后，一切看起来都很顺利，直到最后一——SSH 服务启动失败了。


### 第一个障碍：端口被占用

错误信息很明确：`Bind to port 22 on 0.0.0.0 failed: Address already in use`。22 端口已经被占用了。

我开始排查是什么占用了 22 端口。用 `ss -tlnp | grep :22` 检查，发现端口确实在监听，但奇怪的是，用 `ps aux | grep sshd` 却找不到 sshd 进程。

这时候我意识到，可能是 systemd 的 `ssh.socket` 的问题：一般来说，Ubuntu 的 SSH 服务有两种启动方式：`ssh.service`（传统的守护进程模式）和 `ssh.socket`（按需激活模式）。如果 `ssh.socket` 已经在监听 22 端口，那么 `ssh.service` 再启动就会失败。

果然，`systemctl status ssh.socket` 显示它正在运行并监听 22 端口。

解决方案：换个端口

既然 22 端口有冲突，最简单的办法就是让 sshd 监听其他端口。我决定用 2222。修改 `/etc/ssh/sshd_config`，把 `Port` 改成 2222，同时禁用 `ssh.socket`：


```
sudo systemctl disable --now ssh.socket
sudo mkdir -p /run/sshd
sudo systemctl restart ssh
```

这次终于成功了。`ss -tlnp | grep :2222` 显示 sshd 正在监听 2222 端口，进程也在运行。


## 二：Windows 端口转发

WSL2 不像 WSL1 那样直接共享 Windows 的网络栈，它运行在一个虚拟网络里，有自己的内部 IP（通常是 `172.x.x.x` 或类似地址）。局域网里的其他设备无法直接访问这个 IP。

要让外部设备能连接，需要在 Windows 上做端口转发。Windows 提供了 `netsh interface portproxy` 命令来实现这个功能。

我在 Windows PowerShell（管理员模式）里运行：


```
$wslIP = (wsl hostname -I).Trim()
netsh interface portproxy add v4tov4 listenport=2222 listenaddress=0.0.0.0 connectport=2222 connectaddress=$wslIP
```

理论上，这样就能把 Windows 的 2222 端口转发到 WSL 的 2222 端口了。


## 三：第一次连接尝试——超时

我在 Mac 上尝试连接：


```
ssh -p 2222 pwn@10.0.0.1
```

结果：`Connection timed out`。

超时通常意味着网络不通或者防火墙阻止了连接。我检查了 Windows 防火墙，添加了允许 2222 端口入站的规则：


```
New-NetFirewallRule -DisplayName "WSL2 SSH" -Direction Inbound -LocalPort 2222 -Protocol TCP -Action Allow
```

再试，还是超时。

这时候我意识到一个问题：`10.0.0.1` 是什么 IP？用 `Get-NetIPAddress` 查看，发现 `10.0.0.1` 是一个叫 `cfw-tap` 的虚拟网卡地址，不是 Windows 的真实局域网 IP。

Windows 的真实局域网 IP 是 `10.138.138.98`（WiFi）和 `10.138.170.117`（有线）。


## 四：用正确的 IP——连接建立但立即断开

我换成正确的 IP 再试：


```
ssh -vvv -p 2222 pwn@10.138.138.98
```

这次有进展了！调试输出显示 `Connection established`，说明 TCP 连接成功了。但紧接着，连接就卡在了 `Local version string SSH-2.0-OpenSSH_10.2`，然后报错：


```
kex_exchange_identification: read: Connection reset by peer
```

这个错误很诡异。TCP 连接建立了，说明网络是通的，但 SSH 握手阶段就被重置了。这通常意味着流量到达了目标主机，但没有到达正确的 SSH 服务。


## 五：排查端口转发

我开始怀疑是 Windows 的端口转发配置有问题。检查转发规则：


```
netsh interface portproxy show all
```

输出显示：


```
侦听 ipv4:                 连接到 ipv4:
地址            端口        地址            端口
0.0.0.0         2222        26.243.2.236    2222
```

`26.243.2.236` 是什么？这个我一直没有注意到，依旧以为是端口的问题，做了很久的尝试

然后我再次检查 Windows 的网卡列表的时候，发现这是 Radmin VPN 的虚拟网卡地址。

问题找到了！当我运行 `wsl hostname -I` 时，它返回的是所有网卡的 IP 地址，而第一个恰好是 Radmin VPN 的地址。端口转发被设置成了转发到 VPN 网卡，而不是 WSL 的真实网络接口。


## 六：尝试修正转发地址

我尝试获取 WSL 的 `eth0` 网卡 IP（这才是真正的 WSL 网络接口）：


```
$wslIP = wsl -e sh -lc "ip -4 addr show eth0 | grep -o 'inet [0-9.]*' | head -n1"
$wslIP = ($wslIP -replace 'inet ', '').Trim()
```

但结果还是 `26.243.2.236`。这说明 Radmin VPN 不仅创建了虚拟网卡，还影响了 WSL 的网络配置。


## 七：改用 localhost 转发

既然直接转发到 WSL IP 有问题，我决定试试转发到 `127.0.0.1`。理论上，Windows 的 localhost 应该能访问到 WSL 的服务（WSL2 有 localhost 转发机制）。


```
netsh interface portproxy delete v4tov4 listenport=2222 listenaddress=0.0.0.0
netsh interface portproxy add v4tov4 listenport=2222 listenaddress=0.0.0.0 connectport=2222 connectaddress=127.0.0.1
```

测试正确的端口后，发现 Windows 本机确实能连到 WSL 的 2222 端口。


## 八：换端口再试

为了彻底避开可能的端口冲突，我决定把对外端口改成 8022：


```
netsh interface portproxy delete v4tov4 listenport=2222 listenaddress=0.0.0.0
netsh interface portproxy add v4tov4 listenport=8022 listenaddress=0.0.0.0 connectport=2222 connectaddress=26.243.2.236
New-NetFirewallRule -DisplayName "WSL2-SSH-8022" -Direction Inbound -LocalPort 8022 -Protocol TCP -Action Allow
```

从 Mac 连接：


```
ssh -vvv -p 8022 pwn@10.138.138.98
```

结果还是一样：`Connection established` 后立即 `Connection reset by peer`。


## 九：验证 WSL 内部服务

这时候我开始怀疑是不是 WSL 里的 sshd 本身有问题。我在 WSL 内部测试本地连接：


```
ssh -p 2222 pwn@127.0.0.1
```

成功了！SSH 握手完成，只是在认证阶段失败（因为本地没有配置密钥）。这证明 sshd 服务本身是正常的，问题确实出在转发链路上。


## 十：深入检查转发配置

我再次检查 Windows 的端口转发配置，发现无论怎么修改，`connectaddress` 总是指向 `26.243.2.236`。即使我明确指定了其他地址，下次查看时又变回了这个 VPN 地址。

这时候我开始意识到，Radmin VPN 可能不仅仅是添加了一个虚拟网卡那么简单，它可能还修改了系统的路由表或者网络优先级，导致所有到 WSL 的流量都被引导到了 VPN 网卡。


## 十一：关键转折点

我决定做一个实验：暂时关闭 Radmin VPN，看看会发生什么。

关闭 VPN 后，我重新设置端口转发：


```
$wslIP = (wsl hostname -I).Trim().Split(' ')[0]
netsh interface portproxy delete v4tov4 listenport=8022 listenaddress=0.0.0.0
netsh interface portproxy add v4tov4 listenport=8022 listenaddress=0.0.0.0 connectport=2222 connectaddress=$wslIP
```

这次，`netsh interface portproxy show all` 显示的转发目标终于不是 `26.243.2.236` 了。

从 Mac 再次尝试连接：


```
ssh -p 8022 pwn@10.138.138.98
```

终于成功了！SSH 提示输入密码，输入后顺利登录到 WSL 环境。


## 解决：VPN 是罪魁祸首

整个问题的根源终于清晰了：

Radmin VPN 在系统中创建了一个虚拟网卡（`26.243.2.236`），这个网卡不仅出现在网络接口列表中，还影响了系统的路由决策。当 Windows 的端口转发尝试连接到 WSL 时，流量被错误地路由到了 VPN 网卡，而不是 WSL 的真实网络接口。

这就解释了为什么会出现那些奇怪的现象：

1. **TCP 连接能建立**：因为 Windows 确实在监听 8022 端口，Mac 能连到 Windows。
2. **SSH 握手失败**：因为流量被转发到了错误的目标（VPN 网卡），没有到达 WSL 里的 sshd。
3. **Connection reset**：VPN 网卡收到了不属于它的流量，直接重置了连接。


## 公钥认证配置

问题解决后，我继续配置公钥认证以实现免密登录。在 WSL 中准备好 SSH 目录：


```
mkdir -p ~/.ssh
chmod 700 ~/.ssh
touch ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
```

然后把 Mac 上的公钥（`~/.ssh/id_rsa.pub`）内容添加到 WSL 的 `authorized_keys` 文件中。之后就可以直接免密登录了。


## 总结

问题的三个层次

1. **服务层（WSL 内部）**
2. `ssh.socket` 和 `ssh.service` 的端口冲突
3. 解决方案：禁用 socket 模式，使用独立端口
4. **转发层（Windows）**
5. `netsh portproxy` 的配置正确性
6. 防火墙规则是否放行
7. 解决方案：确保转发目标地址正确
8. **路由层（网络环境）**
9. VPN 虚拟网卡对路由的影响
10. 多网卡环境下的地址选择
11. 解决方案：识别并排除干扰因素

---

诊断方法

**从内到外，逐层验证**：

1. 先确认服务本身是否正常（WSL 内部测试）
2. 再确认转发配置是否正确（Windows 配置检查）
3. 最后排查网络环境因素（VPN、防火墙等）

如果跳过任何一层直接猜测，很容易走入死胡同。

---

经验教训

1. **VPN 软件的隐藏影响**：VPN 不仅创建虚拟网卡，还会影响系统路由。在排查网络问题时，要考虑所有可能影响网络栈的软件。
2. **WSL2 的网络模型**：WSL2 使用虚拟化网络，不是简单的网络共享。理解这一点对于配置网络服务至关重要。
3. **systemd 的服务管理**：现代 Linux 发行版中，同一个服务可能有多种启动方式（service vs socket）。要了解它们的区别和潜在冲突。
4. **逐层诊断的重要性**：不要一开始就假设问题在某一层。从最底层（服务本身）开始验证，逐步向上排查。
5. **详细日志的价值**：`ssh -vvv` 的详细输出能够精确定位问题发生在握手的哪个阶段，这对诊断至关重要。


## 后记

这次排障花了一个多小时，还挺有意思的，Radmin是当时为了玩mc下载的，结果这个时候坑我一把，属实难蚌

以后看到 `Connection established` 后立即 `reset` 的时候，可能说明问题不在网络连通性，而在数据流的路由路径上。

---

遇到 WSL SSH 连接问题时，按这个顺序检查：

- WSL 内 sshd 是否运行？(`ps -ef | grep sshd`)
- WSL 内端口是否监听？(`ss -tlnp | grep :<port>`)
- WSL 内本地连接是否成功？(`ssh -p <port> user@127.0.0.1`)
- Windows portproxy 规则是否存在？(`netsh interface portproxy show all`)
- Windows 防火墙是否放行？(检查入站规则)
- Windows 是否监听对外端口？(`netstat -ano | findstr :<port>`)
- 是否有 VPN 或虚拟网卡干扰？(检查网卡列表和路由表)
- 客户端能否连接到 Windows IP？(`telnet <ip> <port>`)

每一步都通过后再进入下一步，这样能最快定位问题所在。
