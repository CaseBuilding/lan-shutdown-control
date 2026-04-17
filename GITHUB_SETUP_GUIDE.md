# GitHub 仓库设置完整指南

## 📋 准备工作

### 1. 检查环境
确保你的电脑已安装：
- **Git** (版本控制工具)
- **GitHub 账号** (如果没有请先注册)

### 2. 配置 Git（一次性设置）
打开命令行工具（Windows: PowerShell 或 CMD）：

```powershell
# 设置你的GitHub用户名（替换为你的实际用户名）
git config --global user.name "你的GitHub用户名"

# 设置你的邮箱（使用GitHub注册邮箱）
git config --global user.email "你的邮箱@example.com"

# 验证配置
git config --global --list
```

## 🌐 在GitHub网站创建仓库

### 第1步：登录GitHub
1. 打开 [github.com](https://github.com)
2. 点击右上角 "Sign in" 登录你的账号

### 第2步：创建新仓库
1. 点击页面右上角的 "+" 图标
2. 选择 "New repository"

### 第3步：填写仓库信息
**重要设置：**
- **Repository name**: `lan-shutdown-control`
- **Description**: `无需公网，无需手机APP，纯浏览器控制Windows电脑关机/重启/休眠`
- **Visibility**: `Public` (公开，有利于传播)
- **Initialize this repository with**:
  - ☐ 不要勾选 "Add a README file" (我们已有README.md)
  - ☐ 不要勾选 "Add .gitignore" (我们稍后添加)
  - ☐ 不要勾选 "Choose a license" (我们已有LICENSE文件)

3. 点击 "Create repository" 按钮

### 第4步：获取仓库链接
创建成功后，你会看到一个页面，上面有类似这样的命令：
```
git remote add origin https://github.com/你的用户名/lan-shutdown-control.git
```

**记下这个链接**，后面会用到。

## 💻 本地仓库设置（在项目目录操作）

### 第1步：打开命令行进入项目目录
```powershell
# 打开 PowerShell 或 CMD
# 进入项目目录（根据你的实际路径调整）
cd "C:\Users\你的用户名\Desktop\lan_shutdown_control"
# 或者如果你在WSL/Linux环境中：
cd /home/Case/.openclaw/workspace/project/lan_shutdown_control
```

### 第2步：初始化Git仓库
```powershell
# 初始化本地仓库
git init

# 添加所有文件到暂存区
git add .

# 查看将要提交的文件
git status
```

### 第3步：创建 .gitignore 文件（可选但推荐）
在项目根目录创建 `.gitignore` 文件，内容如下：
```
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# PyInstaller
*.spec

# Installer logs
pip-log.txt
pip-delete-this-directory.txt

# Unit test / coverage reports
htmlcov/
.tox/
.coverage
.coverage.*
.cache
nosetests.xml
coverage.xml
*.cover
.hypothesis/
.pytest_cache/

# Translations
*.mo
*.pot

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db
```

然后添加这个文件：
```powershell
git add .gitignore
```

### 第4步：提交代码
```powershell
# 提交所有文件
git commit -m "Initial commit: LanShutdownControl v1.0"

# 重命名主分支为main（GitHub默认）
git branch -M main
```

### 第5步：连接远程仓库并推送
```powershell
# 添加远程仓库（使用你在GitHub页面看到的链接）
git remote add origin https://github.com/你的用户名/lan-shutdown-control.git

# 第一次推送
git push -u origin main
```

**注意**：第一次推送会要求输入GitHub用户名和密码。如果启用了双重验证，需要使用Personal Access Token代替密码。

## 🔐 关于GitHub认证

### 方式1：使用Personal Access Token（推荐）
1. 登录GitHub → Settings → Developer settings → Personal access tokens
2. 点击 "Generate new token"
3. 选择权限（至少需要 `repo` 权限）
4. 生成后复制token，在密码输入时使用这个token

### 方式2：使用SSH密钥（更安全但稍复杂）
```powershell
# 生成SSH密钥
ssh-keygen -t ed25519 -C "你的邮箱@example.com"

# 将公钥添加到GitHub
# 复制 ~/.ssh/id_ed25519.pub 内容到 GitHub → Settings → SSH and GPG keys
```

## ✅ 验证推送成功

### 第1步：检查GitHub页面
刷新你的仓库页面，应该能看到所有文件。

### 第2步：本地验证
```powershell
# 查看远程仓库信息
git remote -v

# 查看提交历史
git log --oneline

# 拉取最新更改（测试连接）
git pull origin main
```

## 🚀 后续开发工作流

### 日常更新代码
```powershell
# 1. 查看修改状态
git status

# 2. 添加修改的文件
git add 文件名
# 或添加所有修改
git add .

# 3. 提交更改
git commit -m "描述你的修改"

# 4. 推送到GitHub
git push origin main
```

### 从GitHub拉取更新
```powershell
# 如果你在其他电脑修改了代码
git pull origin main
```

## 🛠️ 常见问题解决

### Q: 推送时提示 "remote: Invalid username or password"
A: 使用Personal Access Token代替密码，或检查用户名是否正确。

### Q: 提示 "fatal: remote origin already exists"
A: 先删除原有远程仓库：
```powershell
git remote remove origin
git remote add origin https://github.com/你的用户名/lan-shutdown-control.git
```

### Q: 想撤销上次提交
A:
```powershell
# 撤销上次提交但保留修改
git reset --soft HEAD~1

# 完全撤销上次提交和修改
git reset --hard HEAD~1
```

### Q: 提交了错误的文件
A:
```powershell
# 从暂存区移除文件但保留工作区文件
git reset 文件名

# 彻底删除文件（从工作区和Git）
git rm 文件名
```

## 📱 简化方案（如果遇到困难）

如果上述步骤太复杂，可以使用 **GitHub Desktop** 客户端：

1. 下载安装 [GitHub Desktop](https://desktop.github.com/)
2. 登录你的GitHub账号
3. 点击 "File" → "Add local repository"
4. 选择 `lan_shutdown_control` 文件夹
5. 点击 "Publish repository"
6. 填写仓库信息并发布

## 🔗 有用的链接

- [Git 官方文档](https://git-scm.com/doc)
- [GitHub 帮助文档](https://docs.github.com/cn)
- [Git 简明指南](https://rogerdudler.github.io/git-guide/index.zh.html)
- [Git 交互式教程](https://learngitbranching.js.org/)

---

## 🎯 下一步行动

完成GitHub仓库设置后，建议：

1. **设置仓库描述和主题标签**
   - 在仓库页面点击 "Settings"
   - 添加详细描述
   - 添加相关主题：`python` `windows` `lan` `remote-control`

2. **创建第一个Release**
   - 点击 "Releases" → "Create a new release"
   - 版本号：v1.0.0
   - 标题：LanShutdownControl v1.0
   - 描述：第一个稳定版本，包含完整功能

3. **启用 Issues 和 Discussions**
   - 在仓库页面可以看到 Issues 标签
   - 用户可以通过 Issues 反馈问题

## 💡 提示

- 第一次使用Git可能会觉得复杂，但掌握基本命令后会很方便
- 每次修改后及时提交，养成好习惯
- 提交信息要清晰，便于日后查看历史

**遇到问题随时问我！** 🦐