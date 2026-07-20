# 贡献指南

## 我能贡献什么

### 1. 装探针自用（最常见）

下载二进制（见 README）→ 配置 → 把 IDE base_url 改成探针地址 → 正常用 7 天。

你贡献的数据越多，榜单越准。

### 2. 提 PR 测试报告

跑完 7 天后，用 `/__ledger__/export` 生成脱敏数据包，提 PR 到 `data/reports/<vendor>/<plan>/`。这是项目的高信任数据层（PR 通道）。

PR 模板见 `.github/PULL_REQUEST_TEMPLATE.md`。导出页会自动生成符合模板的 Markdown。

### 3. 报 bug / 提建议

开 GitHub Issue。**不要**贴完整 token、API key、prompt 内容。

## 数据隐私承诺

探针上报/导出数据严格遵循：

- ❌ **不上传**：prompt 内容、代码上下文、API key、用户 IP、完整 token
- ✅ **只上传**：聚合指标（TTFT/TPS 分布、状态码统计、超时率、缓存命中率）+ token 后 4 位

Token 存在你本机的系统 keychain（Windows Credential Manager / macOS Keychain / Linux Secret Service），不写明文。

## 升 reviewer

5+ 有效 PR 后可申请 reviewer 权限。Reviewer 可以审别人的数据 PR，是项目的核心维护者。

## 代码贡献

代码改完提 PR。**必须**附：
- 改动说明
- 测试方式（手跑命令 + 预期输出）
- 如果改了 schema，附 migration 脚本

不接受：
- 跳过测试直接合并
- 在代码/日志里硬编码 token / key
- 删除安全相关的代码（keychain / 脱敏）
