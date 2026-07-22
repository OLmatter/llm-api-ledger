# LLM API Ledger

> LLM API 领域的可信数据账本 — 集齐主流厂商的真实用量与性能

**[📊 看完整榜单 →](https://OLmatter.github.io/llm-api-ledger/)** ｜ **[🔧 装探针自用核账 →](https://OLmatter.github.io/llm-api-ledger/probe)**

---

汇集主流 LLM API 厂商的真实用量和性能数据。

不靠厂商宣传，靠用户本地装探针核账 + 众包上报脱敏数据。同套餐多用户真实流量汇聚，三方交叉验证（本地计数 vs 厂商 monitor API vs 套餐标称）。

## 这是什么

一个**本地探针 + 厂商套餐横评榜单**。你装探针自用核账（查自己被吞了多少 Token），脱敏数据可上传/提 PR 汇聚成套餐画像，平台按厂商×套餐交叉验证后公开榜单。

- **横向对比对象**：厂商 × 套餐（如「智谱 GLM Coding Plan Pro」「某中转站 Claude 9.9 元套餐」），不是用户、不是性能跑分
- **数据来源**：本地透传探针 + 厂商官方 monitor API（三方交叉验证）
- **不经手 Token、不经手资金**

## 当前状态：阶段 0（零号用户自验证）

探针 PoC 已完成代码骨架（v0.1.0-alpha）。当前只在仓库维护者本人环境验证，**未开放给群友**。

- ✅ 透传代理 + 本地核账
- ✅ WebUI 配置页（token 走系统 keychain，不写明文）
- ✅ 智谱 monitor API 三周期额度展示（5h / weekly / 30d MCP）
- ✅ 指标补齐 6 类（用量/性能/稳定性/真伪/成本/时序）
- ✅ 一键 PR 包导出（脱敏 + token 后 4 位）
- ✅ PyInstaller 打包成单二进制
- 🚧 零号用户 3-7 天真实流量验证中
- 🚧 VitePress 榜单 / Cloudflare Workers 接收端（后续阶段）

## 使用

### 1. 下载二进制

从 [Releases](../../releases) 下载对应平台的二进制：

| 平台 | 文件 |
|---|---|
| Windows x64 | `ledger-probe-windows-x64.exe` |
| Linux x64 | `ledger-probe-linux-x64` |
| macOS arm64 | `ledger-probe-macos-arm64` |

### 2. 启动

双击运行（或 `./ledger-probe-*`）。控制台会显示：

```
INFO probe ready — dashboard at /__ledger__
```

浏览器会自动打开 `http://127.0.0.1:8080/__ledger__/settings`（首次启动未配置 token 时）。

### 3. 配置

在配置页填：
- **API Token**（智谱就是 Claude Code 里那个 `ANTHROPIC_AUTH_TOKEN`）
- **厂商**（智谱 GLM / DeepSeek / OpenAI / Anthropic / 中转站）
- **套餐**（如智谱 Pro/Max/Lite）

Token 存在系统 keychain，绝不写明文到磁盘/日志/上传。

### 4. 改 IDE base_url

在 Claude Code / Cursor / 其他 IDE 里把 base_url 从厂商官方地址改成探针：

```
# 智谱原配置
ANTHROPIC_BASE_URL=https://open.bigmodel.cn/api/anthropic

# 改成走探针（加 /zhipu/ 前缀）
ANTHROPIC_BASE_URL=http://127.0.0.1:8080/zhipu
```

然后正常写代码。探针透明转发 + 采集指标，你不会感知到任何差异。

### 5. 看账单

打开 `http://127.0.0.1:8080/__ledger__` 看：
- 今日/30 天 token 用量
- 缓存命中率
- TTFT / TPS 分布
- 状态码分布
- 超时类型分布（四分法：connect/read/ttft/stream_stall）
- 厂商声称额度（5h/weekly/30d MCP 三周期，来自 monitor API）

### 6. 导出数据包（提 PR / 发给维护者）

打开 `http://127.0.0.1:8080/__ledger__/export`：
- 选时间窗（默认最近 7 天）
- 点击「生成数据包」
- 下载 JSON 或复制 Markdown PR 描述

**导出包含**：聚合指标（TTFT/TPS 分布、状态码统计、超时率、缓存命中率、厂商 monitor 快照）
**导出不包含**：Prompt 内容、代码上下文、API key、完整 token（只保留后 4 位）

## ⚠ Token 安全（必读）

**Token 只存在你的系统 keychain，永远不要贴到任何聊天/截图/GitHub issue/PR 里。**

- ✅ 探针配置页用密码框输入，直接存 keychain
- ✅ 日志里 token 永远是 `***后 4 位`
- ✅ 导出 PR 包只保留 token 后 4 位（provenance 用）
- ❌ **不要**在 TG 群发完整 token
- ❌ **不要**在 GitHub issue 截图带 token
- ❌ **不要**把 `~/.claude.json` / 环境变量直接 cat 出来

如果意外泄漏，立刻去厂商控制台吊销并重新生成：
- 智谱：https://open.bigmodel.cn → API Keys
- Z.ai：https://z.ai/manage-apikey/coding-plan/personal/apikey

## 指标体系（6 类）

| 类 | 指标 | 识破的坑 |
|---|---|---|
| **A. 用量核账** | 标称 vs 实际可用 tokens、月底清零、用户方差 | 掺水率、提前清零、区别对待 |
| **B. 性能** | TTFT、TPS、长上下文衰减 | 限流降速、掺了慢模型 |
| **C. 稳定性** | 报错率（按状态码拆）+ **超时率独立** | 超售、限流、服务不稳 |
| **D. 真伪识别** | 缓存命中率、模型一致性、上下文真实性 | 假中转、偷换便宜模型、虚标上下文 |
| **E. 成本** | 实际单价、退款执行率 | 名义便宜实际被掺水反贵 |
| **F. 时序** | 24h/7d/月度曲线 | 高峰期限流、半夜偷降级 |

**关键护城河**：D 类（真伪识别）是物理级硬证据。假中转物理上伪造不了 Prompt Caching 的毫秒级二次返回 + 计费减半。

**关键反差信号**：「报错率低 + 超时率高」= 阴险限流实锤（表上漂亮但实际坑人）。

## 状态码语义（统一）

| 状态码 | 含义 |
|---|---|
| **402 Payment Required** | 额度耗尽（OpenAI/DeepSeek/通用） |
| **429 Too Many Requests** | 速率限制（RFC 6585），可作超售间接证据，不等于额度耗尽 |
| **529** | Anthropic 自定义「服务过载」，与额度无关 |
| 超时（无状态码） | 独立指标，四分法：connect/read/ttft/stream_stall |

## 部署架构（探针本身）

- **本地**：Python + FastAPI + SQLite + HTML-in-Python（参考 api-meter）
- **打包**：PyInstaller 单二进制（50-100MB，含 Python 运行时）
- **无 Docker 依赖**、无外部数据库、无网络要求（除调用上游厂商）

## 项目路线

- [x] **阶段 0**：探针 PoC + 零号用户自验证（当前）
- [ ] **阶段 1**：5-10 个群友内测（7 天数据积累）
- [ ] **阶段 2**：500 人群公测
- [ ] **阶段 3**：上线榜单（Cloudflare Workers + GitHub Pages + 多镜像 + 防炸架构）

后续阶段的设计文档见 EventSys `eventsys.知识.技术.ai.AI算力大盘.*`。

## 贡献

PR 通道是项目的高信任数据层。提 PR 流程：

1. 装探针跑 7 天
2. 在 `/__ledger__/export` 生成脱敏数据包
3. fork 本仓库，把 JSON 放到 `data/reports/<vendor>/<plan>/<user-hash>-<date>.json`
4. 提 PR，描述用导出页生成的 Markdown 模板

5+ 有效 PR 的贡献者可申请升 reviewer。

## License

- **代码**（探针、Worker、聚合脚本、前端）：[GPL-3.0](LICENSE)
- **数据**（`data/aggregated/`，未来开放）：CC BY 4.0
- **文档**（本 README、`docs/`）：CC BY-SA 4.0

商用闭源 fork 本项目代码将被 GPL-3.0 条款强制要求开源。

## 安全 / 漏洞披露

发现安全漏洞请**不要**开公开 issue，邮件联系维护者（见 GitHub profile）。
