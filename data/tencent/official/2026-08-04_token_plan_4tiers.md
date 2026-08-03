---
evidence_id: e_2026_08_04_tencent_token_plan_4tiers
vendor_id: tencent
captured_at: 2026-08-04
captured_by: claude
source_url: https://cloud.tencent.com/developer/article/2675766
capture_method: chrome-dump-dom
data_status: vendor_official
credibility: high
file_path: data/tencent/official/2026-08-04_token_plan_4tiers.md
related_plans:
  - tencent-token-plan-lite
  - tencent-token-plan-standard
  - tencent-token-plan-pro
  - tencent-token-plan-max
---

# 腾讯云通用 Token Plan 个人版 4 档套餐对比 (gavin1024, 腾讯云开发者社区)

## 原文摘录

> 摘要：腾讯云通用 Token Plan 个人版分为 **39 / 99 / 299 / 599 元**四档月度套餐，对应 **3,500 万 / 1 亿 / 3.2 亿 / 6.5 亿 Tokens**。

### 4 档套餐价格与配额

| 档位 | 月度 Token 限额 | 价格（元/月） | 适用人群（官方） |
|---|---|---|---|
| 体验 Lite | 3,500 万 | 39 | 首次体验，约 70 轮问答 |
| 基础 Standard | 1 亿 | 99 | 日常使用，约 200 轮问答 |
| 进阶 Pro | 3.2 亿 | 299 | 高频 AI 开发，配额是基础版 3 倍 |
| 专业 Max | 6.5 亿 | 599 | 重度 AI 开发首选 |

### 单价梯度

| 档位 | 单价（元/百万 Tokens） |
|---|---|
| Lite | 约 1.11 |
| Standard | 约 0.99 |
| Pro | 约 0.93 |
| Max | 约 0.92 |

### 通用 Token Plan 是什么

> 通用 Token Plan 是腾讯云面向 AI 编程与龙虾场景推出的个人专属订阅套餐，按月预付，覆盖 GLM-5、GLM-5.1、Kimi-K2.5、MiniMax-M2.5、MiniMax-M2.7 等国产主流模型（更多模型持续接入中），兼容 OpenAI 协议与 Anthropic 协议两种调用入口，可直接接入 CodeBuddy Code、OpenCode、Cursor、Claude Code、Codex、Cline、Kilo CLI、Kilo Code 等编程工具，以及 OpenClaw、AutoClaw、WorkBuddy、CoPaw、Lighthouse OpenClaw 等龙虾工具。

### Hy Token Plan 搭配建议

> 如果你也想用上腾讯混元 Hy3 preview，可以再叠加一份 Hy Token Plan（**28 / 78 / 238 / 468 元/月**）。两条产品线主账号最多各持 1 档，共用同一个 API Key，调用时按 Model ID 自动从对应套餐扣 Token。

### 订阅须知（购买前必看）

- **限购**：每个主账号最多同时持有 1 个通用 Token Plan + 1 个 Hy Token Plan
- **API Key**：仅生成 1 个 API Key（两套餐共用）
- **退款**：均不支持退款，但支持升配（不支持降配）
- **续费**：必须在套餐过期前完成续费，到期后无法续费、剩余 Token 不结转、API Key 失效
- **使用边界**：仅限在 AI 工具中使用，禁止用于自动化脚本与非交互式批量调用

## 数据点

### 通用 Token Plan 个人版（4 档）

| 档位 | 月度 Token 限额 | 月费 | 单价 元/百万 |
|---|---|---|---|
| Lite | 35,000,000 (3,500 万) | 39 元 | 1.11 |
| Standard | 100,000,000 (1 亿) | 99 元 | 0.99 |
| Pro | 320,000,000 (3.2 亿) | 299 元 | 0.93 |
| Max | 650,000,000 (6.5 亿) | 599 元 | 0.92 |

### Hy Token Plan 个人版（4 档）

| 档位 | 月费 |
|---|---|
| Lite | 28 元 |
| Standard | 78 元 |
| Pro | 238 元 |
| Max | 468 元 |

### 覆盖模型（通用 Token Plan）

GLM-5 / GLM-5.1 / Kimi-K2.5 / MiniMax-M2.5 / MiniMax-M2.7（更多持续接入）

### 支持工具（通用 Token Plan）

编程工具：CodeBuddy Code / OpenCode / Cursor / Claude Code / Codex / Cline / Kilo CLI / Kilo Code
龙虾工具：OpenClaw / AutoClaw / WorkBuddy / CoPaw / Lighthouse OpenClaw

## 二次验证

- [x] chrome --dump-dom 抓取 (530 KB HTML, 8984 chars 文本)
- [x] chrome --screenshot 全屏截图 (371 KB PNG)
- [x] **自洽性验算（铁律 22）**：39 元 ÷ 3,500 万 tokens = 39 / 35 = **1.114 元/百万** ✓ (Lite 单价 1.11)
- [x] **自洽性验算**：99 元 ÷ 1 亿 = 99 / 100 = **0.99 元/百万** ✓ (Standard 单价 0.99)
- [x] **自洽性验算**：299 元 ÷ 3.2 亿 = 299 / 320 = **0.934 元/百万** ≈ 0.93 ✓ (Pro 单价)
- [x] **自洽性验算**：599 元 ÷ 6.5 亿 = 599 / 650 = **0.922 元/百万** ≈ 0.92 ✓ (Max 单价)
- [x] **月度 / 比例自洽（铁律 6）**：Standard/Lite = 2.86×, Pro/Standard = 3.2×, Max/Pro = 2.03× — 单价梯度递减合理
- [x] 与 Coding Plan intro 文章一致：腾讯云统一品牌, Token Plan 与 Coding Plan 是两条独立产品线

## 不确定 / 存疑

1. **Hy Token Plan 月度 Token 限额**：文章只列出 28/78/238/468 元 4 档价格,**未明确给出 Hy Token Plan 的月度 Token 限额数字**——**只能填价格,token 数 null**
2. **Hy Token Plan 单价**:无法做自洽性验算(无 token 数)
3. **文章作者 gavin1024 是社区作者,不是腾讯云官方账号**:但发布在 `cloud.tencent.com/developer/` 官方域名下,腾讯云自媒体同步曝光计划——可以视为**官方授权发布的二手分析**,`credibility: high` 但 `data_status: vendor_official` 比 Coding Plan intro (官方账号发布)略低一档,建议使用 `vendor_official` 但在 notes 写明"社区作者授权发布于 cloud.tencent.com"
4. **企业版专业套餐**：本文章主要讲个人版,企业版另文(developer/article/2676529+)
5. **新购流程已迁移至 TokenHub**：与混元生文计费概述一致

## 关联引用

- vendor: data/tencent/vendor.yml (待建)
- plan: data/tencent/plans/tencent-token-plan-{lite,standard,pro,max}.yml (待建)
- 截图: data/tencent/official/2026-08-04_token_plan_4tiers_screenshot.png