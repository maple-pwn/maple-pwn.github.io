# 04：账号与代码同步——Google、Git、GitHub、SSH

本章让你拥有可恢复的 Google 账号、GitHub 账号和 SSH 登录方式，并把第一个项目同步到 GitHub。不要把密码、验证码、恢复码、订阅链接或 SSH 私钥放进任何聊天和仓库。

## 1. 创建或整理 Google 账号

1. 打开 [Google 账号注册入口](https://accounts.google.com/signup)。如果进入的是登录页，点击登录表单附近的“创建账号” → “个人使用”；如果已经是注册表单，直接填写。
2. 按页面顺序填写姓名、生日等资料，选择邮箱地址并设置密码；点击“下一步”继续。若要求手机或其他验证，使用自己的真实联系方式 (中国手机号比较看运气，有时候可以有时候不行) 按页面完成，不要把验证码发给别人。界面不同可看 [Google 官方创建账号说明](https://support.google.com/accounts/answer/27441?hl=zh-Hans)。
3. 创建完成后，打开 [Google 账号管理](https://myaccount.google.com/)，点击左侧“安全性”（部分界面称“安全性与登录”）。窗口较窄时，先展开左上角导航菜单。
4. 在安全性页面找到恢复方式，分别进入“辅助邮箱”和“辅助电话号码”（也可能显示“恢复邮箱/恢复电话”），按提示重新验证身份、填写联系方式并完成验证。若页面没有同名项目，用账号页面顶部的搜索框搜索“辅助邮箱”或“辅助电话号码”。
5. 将账号密码保存到可信密码管理器，不要保存在 `README.md`、聊天记录或截图中。

**检查成功：** 你能在另一台设备或浏览器隐私窗口登录账号，且恢复联系方式正确。

## 2. 注册 GitHub

1. 打开 [GitHub 注册页](https://github.com/signup)。
2. 用长期可用邮箱注册，完成邮箱验证。
3. 登录后点击网页右上角头像 → **Your profile**（你的个人资料），查看自己的个人主页。
4. 在浏览器地址栏确认地址是 `https://github.com/用户名`，记下最后这段用户名。它不是邮箱，也不一定等于页面显示的昵称。后面写“你的用户名”时都替换成这里的值（注意你的用户名不是很好修改，不要随便起，不然想修改很麻烦）。
5. 需要修改账户资料时，点击右上角头像 → **Settings**（设置）；这指 GitHub 网页的头像，不是浏览器账号头像。

**检查成功：** 打开 `https://github.com/你的用户名` 能看到你的个人主页。

## 3. 注册完成后，再安装 Git

Google 和 GitHub 可以独立注册，注册 GitHub 不要求先有 Google 账号。已经有账号的同学直接登录。

**Windows 路线：** 打开 [Git for Windows 下载页](https://git-scm.com/download/win)，下载 x64 安装程序。运行安装向导，PATH 选项保留 **Git from the command line and also from 3rd-party software**，其余使用默认选项。完成后完全退出并重新打开 VS Code，点击“终端 → 新建终端”，选择 PowerShell。

**WSL 路线：** 在 Ubuntu 终端逐条执行：

```bash
sudo apt update
sudo apt install git openssh-client
```

上面某个路线安装完之后

在你选择的终端执行 `git --version`，看到版本号再继续。Windows 与 WSL 若都使用 Git，需要各自在对应环境中配置署名。

### 设置提交署名

在 PowerShell 或 Ubuntu 终端中执行；把名字和邮箱换成自己的，保留引号：

~~~bash
git config --global user.name "你的名字"
git config --global user.email "你的常用邮箱@example.com"
git config --global init.defaultBranch main
git config --global pull.rebase true
git config --global --list
~~~

**检查成功：** 输出中有正确的 `user.name=` 和 `user.email=`。

## 4. 生成 SSH Key

建议在你平时写代码的终端执行一次。如果主要在 WSL 开发，就在 Ubuntu 执行；如果只在 Windows 开发，就在 PowerShell 执行。

~~~bash
ssh-keygen -t ed25519 -C "你的GitHub邮箱@example.com"
~~~

若提示文件已存在或 `Overwrite (y/n)?`，输入 `n`，保留已有密钥；可先查看已有 `.pub` 公钥再添加到 GitHub。Windows 若找不到 ssh-keygen，从开始菜单打开安装 Git 时附带的 Git Bash，后续密钥生成、测试与仓库推送都使用这个窗口。

1. 出现保存位置时，直接按回车。
2. 出现 passphrase 时，建议设置一个自己记得住的密码；不设置就连续按两次回车。
3. 复制**公钥**：

~~~bash
cat ~/.ssh/id_ed25519.pub
~~~

在 WSL 中也可以执行：

~~~bash
clip.exe < ~/.ssh/id_ed25519.pub
~~~

只复制以 `ssh-ed25519` 开头的一整行。绝不复制或上传没有 `.pub` 后缀的 `id_ed25519` 私钥文件。

## 5. 把公钥添加到 GitHub

1. 打开 [GitHub SSH Key 设置页](https://github.com/settings/keys)。
2. 进入页面后，在 SSH keys 区域右上方点击绿色 **New SSH key**。手动路径是网页右上角头像 → **Settings** → 左侧 **SSH and GPG keys**。
3. Title 填写设备名，例如 `我的笔记本`；Key type 选 **Authentication Key**。
4. 点击标为 **Key** 的大文本框，粘贴刚才复制的完整公钥，再点击表单下方 **Add SSH key**。若 GitHub 要求重新验证身份，按网页提示完成。返回列表后应能看到刚才填写的设备名称。
5. 回到终端测试：

~~~bash
ssh -T git@github.com
~~~

首次连接询问是否继续时，先将显示的指纹与 [GitHub 官方 SSH 指纹](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/githubs-ssh-key-fingerprints)中对应算法的值核对；一致才输入 `yes` 并回车。设置过密钥密码的同学按提示输入该密码。

**检查成功：** 输出出现 `Hi` 和你的 GitHub 用户名；提示不提供 shell access 是正常的。

官方入口：[添加 SSH Key](https://docs.github.com/authentication/connecting-to-github-with-ssh/adding-a-new-ssh-key-to-your-github-account)。

## 6. 推送第一个仓库

1. 在 GitHub 网页右上角点 `+` → **New repository**；找不到菜单时直接打开 [新建仓库页面](https://github.com/new)。
2. **Owner** 选择自己的账号，**Repository name** 输入 `hello-github`。可见性建议先选 **Private**（私有）；确实想让所有人看到练习内容才选 **Public**（公开）。
3. 向下找到初始化选项：**Add a README file** 不勾选（若是开关则关闭），**Add .gitignore** 选 **None**，**Choose a license** 选 **None**。我们稍后从电脑上传文件，这里先建空仓库。
4. 点击 **Create repository**。
5. 先准备一个独立练习目录，避免依赖前面选了哪条开发路线。

Windows：在文件资源管理器“文档 → code”中新建 `hello-github`，用 VS Code 的“文件 → 打开文件夹”打开它，再点击“终端 → 新建终端”。

WSL：在 Ubuntu 输入下面命令，再在打开的 VS Code 中新建终端：

```bash
mkdir -p ~/code/hello-github
cd ~/code/hello-github
code .
```

在 VS Code 按 `Ctrl+Shift+E` 打开左侧资源管理器，在 `HELLO-GITHUB` 文件夹下面的空白处右键 → “新建文件”，输入 `README.md` 并回车。在中间编辑区写入 `# 我的第一个 GitHub 项目`，按 `Ctrl+S` 保存。

再新建 `.gitignore`，注意文件名开头有一个点，写入并保存：

```gitignore
.venv/
__pycache__/
*.exe
.env
```

在项目终端执行 `git init`。然后逐条执行下列命令，将 `你的用户名` 替换为 GitHub 用户名：

~~~bash
git add README.md .gitignore
git commit -m "first commit"
git branch -M main
git remote add origin git@github.com:你的用户名/hello-github.git
git push -u origin main
~~~

**检查成功：** 刷新 GitHub 仓库页面，能看到 `README.md` 和 `first commit`。

若出现 `not a git repository`，先执行 `pwd` 检查终端位置，再确认当前目录已运行 `git init`。若出现 `Permission denied (publickey)`，回到第 5 节，在当前这个终端测试 SSH；不要换用另一个尚未配置密钥的终端。

## 7. 修改一次，再同步一次

在 VS Code 修改 README.md，添加一行 `这是我的第二次更新`，按 Ctrl+S。回到项目终端逐条执行：

```bash
git diff
git add README.md
git commit -m "update README"
git push
```

**检查成功：** 刷新 GitHub 仓库页面，README 显示新增内容。

## 8. 第二台电脑接着写

1. 在第二台电脑完成本章 Git 安装、署名与 SSH 配置。每台设备单独生成密钥并添加公钥到同一个 GitHub 账号。
2. Windows：在 VS Code 点击“文件 → 打开文件夹”，选择“文档”中的 `code`，再点“终端 → 新建终端”。WSL：从开始菜单打开 Ubuntu，在终端执行 `mkdir -p ~/code`，再执行 `cd ~/code`。这个目录中应还没有 `hello-github`；有同名文件夹时先检查内容，不要删除它来腾位置。
3. 将下面用户名改为自己的，再执行：

```bash
git clone git@github.com:你的用户名/hello-github.git
cd hello-github
code .
```

以后每次开始编辑，先在该项目终端运行 `git status`，确认没有尚未提交的修改，再执行 `git pull --ff-only`；结束时按第 7 节提交并推送，然后再换设备。

如果拉取提示无法快进、覆盖本地修改或发生冲突，停止编辑，保留文件，把 `git status` 和报错交给 AI 检查。不要照抄强制推送或清空目录命令。克隆 uv 管理的 Python 项目后，按第三章在当前系统安装 uv，进入项目目录执行 `uv sync --locked`，再用 `uv run python hello.py` 运行。不要复制另一台电脑的 `.venv`。

同步实际 Python 项目时，需要提交源代码、`pyproject.toml`、`uv.lock` 和 `.python-version`；`.venv/` 应继续放在 `.gitignore` 中。先运行 `git status` 核对，再按实际文件名添加，例如：

```bash
git add hello.py pyproject.toml uv.lock .python-version .gitignore
git commit -m "save Python project environment"
git push
```

这个例子在已关联 GitHub 仓库的 Python 项目中执行，不要在只有 README 的 hello-github 练习目录中照抄。

## 完成清单

- [ ] Google 账号有可用恢复方式。
- [ ] GitHub 已完成邮箱验证。
- [ ] Git 署名正确。
- [ ] GitHub 已添加 SSH 公钥，`ssh -T` 成功。
- [ ] 第一个项目已推送到 GitHub。

下一篇：[05 更强的 AI](05-advanced-ai.md)。
