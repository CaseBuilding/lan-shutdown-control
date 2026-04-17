# 🖥️📱 局域网电脑控制工具 (LanShutdownControl)

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![PySide6](https://img.shields.io/badge/GUI-PySide6-green.svg)](https://doc.qt.io/qt-6/pyside6.html)
[![Windows](https://img.shields.io/badge/platform-Windows-0078D6.svg)](https://www.microsoft.com/windows)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**无需公网，无需手机APP，纯浏览器控制Windows电脑关机/重启/休眠**

> 手机和电脑在同一个局域网？想用手机控制电脑关机？这个工具就是为你设计的！

## ✨ 核心功能

### 🚀 一键控制
- **关机** - 设定倒计时后自动关机
- **重启** - 设定倒计时后自动重启  
- **休眠** - 立即让电脑进入休眠状态
- **取消** - 取消已安排的关机/重启操作

### 📱 手机友好
- **无需安装APP** - 纯浏览器操作
- **扫码快速配置** - 第一次扫码后收藏链接即可
- **响应式界面** - 适配各种手机屏幕
- **添加到主屏幕** - 像原生APP一样使用

### 🛡️ 安全可靠
- **纯局域网** - 不依赖任何外部服务器
- **访问令牌** - 每次生成唯一安全令牌
- **Windows防火墙友好** - 只需一次授权
- **系统托盘运行** - 不干扰正常工作

### ⚙️ 高级特性
- **开机自启** - Windows启动时自动运行
- **后台运行** - 最小化到系统托盘
- **多IP支持** - 自动发现所有本地IP地址
- **配置持久化** - 设置自动保存
- **倒计时自定义** - 每次可设置不同倒计时

## 🖼️ 界面预览

> *截图占位符：后续添加实际界面截图*

## 🚀 快速开始

### 方法一：直接运行（开发模式）
```bash
# 1. 克隆项目
git clone https://github.com/yourusername/lan-shutdown-control.git
cd lan-shutdown-control

# 2. 安装依赖
pip install -r requirements.txt

# 3. 运行程序
python main.py
```

### 方法二：使用预编译EXE（推荐）
1. 从 [Releases](https://github.com/yourusername/lan-shutdown-control/releases) 下载最新版本
2. 运行 `LanShutdownControl.exe`
3. 点击"启动服务"
4. 用手机扫描二维码

### 方法三：安装程序
1. 下载 `LanShutdownControl-Setup.exe`
2. 运行安装向导
3. 选择是否创建桌面快捷方式和开机自启
4. 安装完成后自动启动程序

## 📖 详细使用指南

### 第一步：启动服务
1. 运行程序后，点击"启动服务"按钮
2. 程序会显示二维码和访问链接
3. Windows防火墙可能会弹出提示，选择"允许访问"

### 第二步：手机配置
1. 使用手机相机或微信扫描二维码
2. 手机浏览器会打开控制页面
3. **重要**：将页面加入书签或添加到主屏幕
   - iPhone Safari: 点击分享按钮 → "添加到主屏幕"
   - Android Chrome: 点击菜单 → "添加到主屏幕"

### 第三步：开始控制
- **安排关机/重启**: 输入倒计时秒数 → 点击对应按钮
- **立即休眠**: 直接点击"立即休眠"按钮  
- **取消操作**: 点击"取消关机/重启"按钮

### 第四步：日常使用
以后只要手机和电脑在同一个网络下：
1. 打开收藏的控制页面
2. 直接进行操作
3. 无需重新扫码（除非更改了访问令牌）

## 🔧 进阶配置

### 修改默认设置
在程序界面中可以调整：
- **监听端口**: 默认8765，可修改避免冲突
- **默认倒计时**: 默认15秒，可设置为0-3600秒
- **访问令牌**: 可手动生成新令牌增强安全
- **开机自启**: 开启后Windows启动时自动运行

### 多电脑管理
如需管理多台电脑：
1. 每台电脑安装并运行本程序
2. 为每台电脑设置不同的端口
3. 手机为每台电脑收藏不同的控制链接
4. 通过不同链接控制对应电脑

## 🛠️ 开发者指南

### 项目结构
```
lan_shutdown_control/
├── main.py              # 程序入口
├── ui.py                # PySide6 GUI界面
├── service.py           # HTTP服务和控制逻辑
├── config.py            # 配置管理
├── startup.py           # 开机自启功能
├── tests/               # 单元测试
├── build_exe.ps1        # EXE打包脚本
├── LanShutdownControl.spec  # PyInstaller配置
└── installer.iss        # Inno Setup安装脚本
```

### 开发环境搭建
```bash
# 1. 安装Python 3.10+
# 2. 安装依赖
pip install -r requirements.txt
pip install -r build_requirements.txt

# 3. 运行测试
python -m pytest tests/
```

### 打包EXE
```powershell
# 第一次打包（安装构建依赖）
powershell -ExecutionPolicy Bypass -File .\build_exe.ps1 -InstallBuildDeps

# 后续打包
powershell -ExecutionPolicy Bypass -File .\build_exe.ps1

# 输出目录: dist\LanShutdownControl\
```

### 创建安装包
1. 安装 [Inno Setup](https://jrsoftware.org/isinfo.php)
2. 打开 `installer.iss` 编译，或命令行运行：
```powershell
ISCC .\installer.iss
```
3. 安装包输出到 `dist_installer/`

## ❓ 常见问题

### Q: 手机扫了二维码但打不开页面？
A: 确保手机和电脑连接的是**同一个WiFi网络**，检查Windows防火墙是否允许程序通信。

### Q: 如何更改访问令牌？
A: 点击"重新生成访问口令"按钮，新令牌会立即生效，需要重新扫码。

### Q: 程序可以管理多台电脑吗？
A: 可以！每台电脑运行独立实例，设置不同端口，手机收藏不同链接即可。

### Q: 支持Linux或macOS吗？
A: 当前仅支持Windows，因为使用了Windows特有的关机API。跨平台支持在规划中。

### Q: 安全吗？别人能控制我的电脑吗？
A: 只要不泄露包含令牌的链接就是安全的。链接只在局域网内有效，且每次生成唯一令牌。

### Q: 如何彻底卸载？
A: 1. 关闭程序 2. 删除安装目录 3. 如需删除开机自启，运行一次程序并关闭"开机自启"选项。

## 🤝 贡献指南

我们欢迎各种形式的贡献！

### 报告问题
- 使用 [GitHub Issues](https://github.com/yourusername/lan-shutdown-control/issues) 报告bug或建议功能
- 请提供：操作系统版本、Python版本、错误日志、复现步骤

### 提交代码
1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

### 开发规范
- 遵循现有代码风格
- 添加适当的类型注解
- 为新功能编写测试
- 更新相关文档

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

- [Python](https://www.python.org/) - 编程语言
- [PySide6](https://doc.qt.io/qt-6/pyside6.html) - GUI框架
- [PyInstaller](https://www.pyinstaller.org/) - 应用打包
- [Inno Setup](https://jrsoftware.org/isinfo.php) - 安装程序
- [qrcode](https://github.com/lincolnloop/python-qrcode) - 二维码生成

## 📞 支持与联系

- **GitHub Issues**: [问题反馈](https://github.com/yourusername/lan-shutdown-control/issues)
- **电子邮件**: your.email@example.com
- **讨论区**: [GitHub Discussions](https://github.com/yourusername/lan-shutdown-control/discussions)

---

**提示**: 首次使用建议先设置较长的倒计时（如60秒）测试功能，熟悉后再使用较短倒计时。

*如遇紧急情况需要立即取消关机，可在电脑上运行命令: `shutdown /a`*