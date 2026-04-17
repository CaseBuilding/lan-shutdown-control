# GitHub 快速启动命令

## 🔧 环境准备

### 1. 配置Git（第一次使用需要）
```bash
# 设置用户名（替换为你的GitHub用户名）
git config --global user.name "你的用户名"

# 设置邮箱（替换为你的GitHub注册邮箱）
git config --global user.email "你的邮箱@example.com"
```

### 2. 进入项目目录
```bash
# 如果你在WSL/Linux环境
cd /home/Case/.openclaw/workspace/project/lan_shutdown_control

# 如果你在Windows PowerShell
cd "C:\Users\你的用户名\...\lan_shutdown_control"  # 根据实际路径调整
```

## 🚀 一步到位命令（推荐）

复制以下命令，一次性执行所有步骤：

```bash
# 1. 进入项目目录（根据你的环境调整路径）
cd /home/Case/.openclaw/workspace/project/lan_shutdown_control

# 2. 初始化Git仓库
git init

# 3. 添加.gitignore文件（已创建）
# 4. 添加所有文件（除.gitignore中忽略的）
git add .

# 5. 提交代码
git commit -m "Initial commit: LanShutdownControl v1.0"

# 6. 重命名主分支
git branch -M main

# 7. 添加远程仓库（替换为你的GitHub仓库链接）
git remote add origin https://github.com/你的用户名/lan-shutdown-control.git

# 8. 推送到GitHub
git push -u origin main
```

**注意**：执行第8步时，会要求输入GitHub用户名和密码。如果启用了双重验证，请使用Personal Access Token。

## 📝 分步执行说明

### 步骤1：在GitHub网站创建仓库
1. 登录 [github.com](https://github.com)
2. 点击右上角 "+" → "New repository"
3. 填写：
   - Repository name: `lan-shutdown-control`
   - Description: `无需公网，无需手机APP，纯浏览器控制Windows电脑关机/重启/休眠`
   - 选择 Public
   - **不要**勾选 "Add a README file"
4. 点击 "Create repository"
5. 复制生成的仓库链接（类似：`https://github.com/你的用户名/lan-shutdown-control.git`）

### 步骤2：执行本地命令
使用上面的一步到位命令，记得：
1. 替换 `你的用户名` 为你的GitHub用户名
2. 替换仓库链接为你在步骤1复制的链接

## 🔐 认证问题解决

### 如果提示认证失败：
1. **生成Personal Access Token**：
   - 登录GitHub → Settings → Developer settings → Personal access tokens
   - 点击 "Generate new token"
   - 选择 `repo` 权限
   - 生成后复制token

2. **推送时使用token代替密码**：
   - 在要求输入密码时，粘贴刚才复制的token

## ✅ 验证成功

1. 刷新你的GitHub仓库页面
2. 应该能看到所有文件
3. 可以点击文件查看内容

## 🛠️ 后续更新代码

### 日常更新：
```bash
# 1. 查看修改
git status

# 2. 添加修改
git add .  # 或 git add 文件名

# 3. 提交
git commit -m "描述修改内容"

# 4. 推送
git push origin main
```

### 从GitHub拉取更新：
```bash
git pull origin main
```

## 💡 简单方案

如果命令行太复杂，可以使用 **GitHub Desktop**：
1. 下载安装 [GitHub Desktop](https://desktop.github.com/)
2. 登录你的GitHub账号
3. 点击 "File" → "Add local repository"
4. 选择项目文件夹
5. 点击 "Publish repository"

## 🆘 遇到问题？

1. **提示 "remote origin already exists"**：
   ```bash
   git remote remove origin
   git remote add origin https://github.com/你的用户名/lan-shutdown-control.git
   ```

2. **想重新开始**：
   ```bash
   rm -rf .git
   git init
   # 然后重新执行上面的命令
   ```

3. **忘记仓库链接**：
   ```bash
   git remote -v  # 查看当前远程仓库
   ```

## 📞 需要帮助？

如果执行中遇到问题，请提供：
1. 你执行的命令
2. 完整的错误信息
3. 你的操作系统环境（Windows/Linux）

我会帮你解决！ 🦐