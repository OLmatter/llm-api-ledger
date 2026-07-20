# Security Policy

## Token 安全（最关键）

本探针处理用户的 LLM API token。**Token 是最敏感的数据**，处理不当会导致用户财产损失。

### 我们的承诺

- Token 只存储在系统 keychain（不写明文 JSON / 不进日志 / 不上传）
- 日志中 token 一律显示为 `***后4位`
- 导出 PR 包只保留 token 后 4 位（provenance 用，不可逆推）
- 探针源码接受社区审计，keychain 调用路径透明

### 用户的责任

- **不要**在任何聊天（TG/QQ/微信）、截图、GitHub issue/PR 里贴完整 token
- 如意外泄漏，立刻去厂商控制台吊销并重新生成
- 不要把 `~/.claude.json` 或环境变量文件 cat 到公开渠道

## 报告漏洞

发现安全漏洞请**不要**开公开 issue。

- 邮件联系维护者（GitHub profile 上的邮箱）
- 或开一个只写 "security issue, please contact privately" 的空 issue，维护者会主动联系

我们会在 72 小时内响应。

## 已知风险

### PyInstaller 二进制

PyInstaller 打包的二进制可能被某些杀毒软件误报。这是 PyInstaller 通病，不是真有病毒。你可以：
- 从源码自行运行（`pip install -r requirements.txt && python -m probe.app`）
- 自行从源码打包（`pyinstaller src/probe/probe.spec`）

### 系统 keychain

- Windows: 使用 Credential Manager。如果系统被入侵，token 会泄漏
- macOS: 使用 Keychain。第一次会弹权限请求
- Linux: 使用 Secret Service（GNOME Keyring / KWallet）。需要桌面环境

如果 keychain 不可用（无桌面 Linux），探针会降级到读环境变量 `LEDGER_TOKEN`（但不会自动写）。
