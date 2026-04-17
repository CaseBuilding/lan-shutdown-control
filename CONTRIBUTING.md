# 贡献指南

欢迎为 LanShutdownControl 项目贡献代码！本指南将帮助你开始贡献。

## 🎯 开始之前

### 行为准则
我们致力于为所有人提供友好、尊重和无骚扰的体验。请阅读并遵守我们的行为准则。

### 开发流程
1. **Fork 仓库** - 点击 GitHub 页面的 Fork 按钮
2. **克隆仓库** - `git clone https://github.com/yourusername/lan-shutdown-control.git`
3. **创建分支** - `git checkout -b feature/your-feature-name`
4. **进行修改** - 编写代码和测试
5. **提交更改** - `git commit -m "描述你的变更"`
6. **推送到远程** - `git push origin feature/your-feature-name`
7. **创建 Pull Request** - 在 GitHub 上提交 PR

## 🛠️ 开发环境设置

### 系统要求
- Python 3.10 或更高版本
- Git
- Windows 10/11 (开发环境)

### 安装依赖
```bash
# 克隆仓库
git clone https://github.com/yourusername/lan-shutdown-control.git
cd lan-shutdown-control

# 安装运行依赖
pip install -r requirements.txt

# 安装开发依赖（可选）
pip install -r build_requirements.txt
pip install pytest  # 测试框架
```

### 运行测试
```bash
python -m pytest tests/
```

## 📁 项目结构
```
lan_shutdown_control/
├── main.py              # 程序入口点
├── ui.py                # GUI界面 (PySide6)
├── service.py           # HTTP服务和业务逻辑
├── config.py            # 配置管理
├── startup.py           # 开机自启功能
├── tests/               # 单元测试
│   ├── test_service.py
│   ├── test_startup.py
│   └── test_ui_smoke.py
├── build_exe.ps1        # EXE打包脚本
├── LanShutdownControl.spec  # PyInstaller配置
└── installer.iss        # Inno Setup安装脚本
```

## 💻 代码规范

### Python 代码风格
- 遵循 [PEP 8](https://www.python.org/dev/peps/pep-0008/) 规范
- 使用 **类型注解** 提高代码可读性
- 函数和类使用英文文档字符串

### 提交信息规范
使用约定式提交：
- `feat:` 新功能
- `fix:` bug修复
- `docs:` 文档更新
- `style:` 代码格式调整
- `refactor:` 重构代码
- `test:` 测试相关
- `chore:` 构建过程或辅助工具变动

示例：
```
feat: 添加HTTPS支持
fix: 修复二维码生成失败的问题
docs: 更新安装说明
```

### 测试要求
- 新功能需要包含测试
- 修复bug时需要添加回归测试
- 保持测试覆盖率

## 🐛 报告问题

### 创建 Issue
1. 检查是否已有类似 issue
2. 使用对应的 issue 模板
3. 提供详细的重现步骤
4. 包括环境信息（系统版本、Python版本等）

### Issue 模板
我们提供两种 issue 模板：
- **Bug 报告** - 用于报告程序错误
- **功能请求** - 用于提出新功能建议

## 🔀 Pull Request 流程

### 创建 PR
1. 确保分支基于最新的 `main` 分支
2. 填写 PR 模板中的所有部分
3. 链接相关 issue（如有）
4. 添加测试和文档更新

### PR 审查
- 至少需要一个维护者批准
- 所有测试必须通过
- 代码需要符合项目规范

### PR 合并
- 使用 "Squash and merge" 选项
- 保持提交历史清晰

## 📦 打包和发布

### 本地打包测试
```powershell
# 打包EXE
powershell -ExecutionPolicy Bypass -File .\build_exe.ps1

# 测试打包后的程序
cd dist\LanShutdownControl
.\LanShutdownControl.exe
```

### 版本管理
我们使用语义化版本控制 (SemVer)：
- `MAJOR` - 不兼容的API修改
- `MINOR` - 向下兼容的功能性新增
- `PATCH` - 向下兼容的问题修复

## 🤝 沟通渠道

- **GitHub Issues** - 功能请求和bug报告
- **Pull Requests** - 代码贡献
- **GitHub Discussions** - 一般讨论和问题

## 📄 许可证
贡献的代码将遵循项目的 MIT 许可证。

## 🙏 致谢
感谢你考虑为项目做出贡献！你的每一份贡献都让这个项目变得更好。

---

*有问题？创建一个 issue 或加入讨论！*