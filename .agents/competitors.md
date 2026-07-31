---
title: 竞品调研
description: 同类型项目对比，记录方法论差异与可借鉴点
---

# 竞品调研

最后更新：2026-08-01

## 调研目的

AIDASH（llm-api-ledger）做的是「LLM API 订阅套餐横向对比 + 实测量榜单」。这个领域有几种形态相近的项目，本文档记录它们各自的做法、核心差异、以及对 AIDASH 的可借鉴点。

> **本调研只在每次大版本或新增重要项目时更新。** 调研产物不进入 VitePress 站点导航，仅作内部参考。

---

## 直接对标：[tokscale](https://github.com/junhoyeo/tokscale)

**规模**：4,724 stars · 386 forks · MIT · 持续更新（v2 native Rust TUI）

### 它解决什么问题

「我作为一个开发者在 AI coding agent 上烧了多少 token / 多少钱」——**用户视角**的用量追踪 + 全球排行榜。

### 数据来源（核心机制）

| 客户端 | 数据位置 |
|---|---|
| Claude Code | `~/.claude/projects/` + `~/.claude/transcripts/` |
| Codex CLI | `~/.codex/sessions/*.jsonl` |
| Gemini CLI | `~/.gemini/tmp/*/chats/*.json` |
| OpenCode | `~/.local/share/opencode/opencode.db` |
| Cursor | Cursor API 导出 CSV（缓存到 `~/.config/tokscale/cursor-cache/`） |
| Kimi CLI / Kimi Code | `~/.kimi/sessions/` / `~/.kimi-code/sessions/` |
| ZCode | `~/.zcode/cli/db/db.sqlite` |
| CodeBuddy / WorkBuddy | `~/.codebuddy/projects/**/*.jsonl` |
| Antigravity | SQLite / JSONL |
| ... 共 30+ | (略) |

**关键设计**：**直接读本地客户端的 jsonl / SQLite / db 文件**，而不是要厂商暴露 API。
- 好处：能跨客户端汇总、即装即用
- 代价：依赖客户端的文件格式稳定（一旦客户端改 schema 要更新解析器）

### 定价数据实时性

用 [LiteLLM pricing data](https://github.com/BerriAI/litellm) 自动算成本，**不依赖厂商手动维护**。LiteLLM 维护 200+ 厂商的实时价格 JSON。

### 提交流程

```bash
bunx tokscale@latest submit
```
用户主动提交 → 创建公开 profile → 数据展示在 leaderboard。

### 最有借鉴价值的一节：Subscription Usage

直接调厂商监控 API（OAuth / API key）显示**实时剩余配额**：

```
Session    85% left  [=========---] resets in 2h 15m
Weekly     72% left  [========----] resets Fri 3pm
Plan     Max 20x
```

这不是排行榜，是**个人剩余配额面板**。配套的 Nuxt 3 前端（`tokscale.ai`）有 3D Contributions Graph。

### 局限性

- **没有套餐横比**：只回答「我用了多少」，不回答「我该买哪个」
- **隐私**：默认公开 profile，用户名直接展示
- **数据归用户**：不展示套餐 baseline 的公平比较

---

## 直接对标：[ccusage](https://github.com/ryoppippi/ccusage)

**规模**：17,630 stars · 764 forks · NOASSERTION（之前 m1_0014 调研时 1524 commits / 实际更高，已超到scale 3.7 倍）

### 它解决什么问题

**个人日常编码 session 的 token 用量 report**——比 tokscale 更窄更深：不做社交 leaderboard，专做 daily / weekly / monthly / session 四种维度的本地报告。

### 核心命令

```bash
npx ccusage@latest
ccusage daily / weekly / monthly / session
ccusage blocks                  # 5h 账单窗口
ccusage statusline              # 状态栏集成（Beta）
```

### 数据来源（与 tokscale 高度相似）

读本地客户端文件：Claude Code / Codex / OpenCode / Amp / Droid / Codebuff / Hermes / pi-agent / Goose / OpenClaw / Kilo / Kimi / Qwen / Copilot / Gemini / Antigravity——**16+ 客户端**（比 tokscale 30+ 少）。

### 定价数据

也用 [LiteLLM pricing data](https://github.com/BerriAI/litellm)，跟 tokscale 一致。

### 关键差异 vs tokscale

| 维度 | tokscale | ccusage |
|---|---|---|
| **社交**：排行榜 / submit | ✅ 有 | ❌ 没有（纯本地 report） |
| **状态栏集成**（statusline） | ❌ | ✅ 有（Beta） |
| **订阅配额面板**（Subscription Usage） | ✅ 调厂商监控 API | ❌ 没有 |
| **客户端覆盖** | 30+ | 16+ |
| **stars** | 4,724 | **17,630** |

**为什么 ccusage stars 更高**：ccusage 早做 + 专注 Claude Code 单类场景（用户量最大）+ 状态栏集成。比 tokscale 更实用，能直接嵌到开发者工作流（statusline 实时显示）。

### 局限性

- **无社交**：没有 leaderboard、没有 profile 提交
- **无套餐横比**：跟 tokscale 一样不回答「我该买哪个」
- **无订阅实时剩余**：不像 tokscale 调监控 API 显示 5h 剩余

### 借鉴价值

- **状态栏集成**（statusline）—— AIDASH 未来也可做 statusline 模式，让用户在 IDE 直接看到当前套餐剩余
- **blocks 命令**（5h 账单窗口）—— 这个命名比 tokscale 的「Subscription Usage」更直观

---

## AIDASH vs tokscale vs ccusage：三方对比

| 维度 | AIDASH | tokscale | ccusage |
|---|---|---|---|
| 数据视角 | 套餐能跑多少（横比） | 用户用了多少（个人） | 用户用了多少（个人） |
| 数据来源 | 维护者手动 + 官方监控 API | 本地客户端文件 + 监控 API | 本地客户端文件 |
| 提交流程 | 维护者 PR | 用户主动 `submit` | 无 |
| 隐私 | 服务端零账号（无用户名） | 公开 profile | 纯本地，无上传 |
| 排行榜 | 厂商×套餐横比 | 用户个人 rank | 无 |
| 状态栏集成 | ❌ | ❌ | ✅ |
| 订阅实时剩余 | ❌ | ✅ | ❌ |
| 客户端覆盖 | 26 套餐 | 30+ 客户端 | 16+ 客户端 |
| 价格来源 | yml 手维护 | LiteLLM 自动 JSON | LiteLLM 自动 JSON |

**三个项目互补不重叠** —— AIDASH 不被 tokscale/ccusage 替代。

---

## 其他参考项目

### ~~[Awesome-Coding-Plan](https://github.com/zerrouki-omar/Awesome-Coding-Plan)~~ — 已删除/404

> 描述：「Centralizing AI coding plan details: quotas, limits, API pricing & value-for-money across providers」
> 列举式 README，**没有任何代码或聚合**——纯文字 list，已经 404。

教训：GitHub 上**纯列表 README 类项目生命周期很短**。AIDASH 必须有实时数据 + 自动构建才有壁垒。

### [llm-pricing.com](https://www.llm-pricing.com/) — SaaS 网

- 覆盖 OpenAI / Anthropic / Gemini / Kimi / 通义
- Markdown 导出 + 实时追踪
- 不是 GitHub 项目，无代码可学

### 中文社区博客类

- 博客园「国产 AI 编程套餐对比」(2026-05) — 一次性人工对比表，无自动更新
- 掘金「OpenAI 封锁中国？国产大模型价格战」 — 临时性媒体稿
- 163 / 搜狐「LLM 价格全面下跌」 — 趋势报道

**结论**：中文社区有大量单点对比但**没有持久化的项目**，AIDASH 的「持续维护 + 真实测」组合正好填补空白。

---

## AIDASH 借鉴清单（按实施成本排序）

| 借鉴点 | 实施成本 | 优先级 | 状态 | 来源 |
|---|---|---|---|---|
| 接入 LiteLLM pricing data 自动算成本 | 中（一次性脚本） | 高 | 未做 | tokscale + ccusage |
| 状态栏集成（statusline） | 低（生成字符串） | 高 | 未做 | ccusage |
| 实时剩余配额面板（订阅 View） | 中（前端 + 后端） | 中 | 未做 | tokscale |
| 本地客户端 JSONL 读取（探针替代） | 高（要写 parser） | 中 | 未做 | tokscale + ccusage |
| 公开 profile + submit 模式 | 中（账号 + 流程） | 中 | 未做 | tokscale |
| `${model} blocks` 5h 账单窗口命名 | 低 | 中 | 未做 | ccusage |
| Nuxt 3 / Web 3D Graph 替代 VitePress | 高（重构） | 低 | 未做 | tokscale |

---

## 调研方法论（避免下次浪费）

1. **GitHub topic 搜不到什么**：`<topic>` 主页只显示说明文字，不列仓库。直接搜关键词 + 限定 `TypeScript` / `language:Markdown` 才出结果
2. **WebSearch + GitHub repo API 组合最快**：先用 WebSearch 找候选 URL → 用 GitHub API `search/repositories` 验证存在 + 拉 stars 排序
3. **WebFetch 失败时 Chrome --dump-dom 兜底**：GitHub SPA 渲染慢，dump-dom + virtual-time-budget=8000 才稳
4. **raw.githubusercontent.com 经常被网络拦截**：备选 GitHub 主页 dump-dom
5. **从 commit 描述挖机制**：很多项目 README 写得简略，但 PR/issue commit 描述会详细得多（参考本次 opencode Go 推荐机制调研）

---

## 更新日志

- **2026-08-01**：v2。补 ccusage（17,630 stars）作为第二大直接对标；增加 AIDASH ↔ tokscale ↔ ccusage 三方对比；借鉴清单从 5 项扩张到 7 项（新增 statusline 集成、`blocks` 命名参考）
- **2026-07-31**：初版。核心对标 tokscale；其他参考项目（Awesome-Coding-Plan 已 404、llm-pricing.com、中文博客类）标注对比；产生借鉴清单 5 项
