# data/ 目录规范

> **铁律 28**（2026-08-01 落地）：任何 `source_kind: vendor_official` 或 `anthropic_official` 的 measurement 必须有 `evidence_path` 指向本目录的证据文件。
>
> **当前状态**：本文件描述的是**目标结构**。当前项目还在过渡期（`data/vendors/` + `data/plans/` 仍是主路径），新加的 `data/<vendor>/official/` 目录并存。后续迁移单独 PR。

---

## 目录结构（按厂商聚合 — 目标结构）

```
data/
  README.md                       # 本文件
  config.json                     # 全局配置
  ledger.db                       # 本地账本数据（探针用）
  aggregated/                     # 跨厂商聚合数据（如果有）
  reports/                        # 历史报表 / 巡检报告

  <vendor_id>/                    # 按厂商分子目录（vendor_id 字段值）
    vendor.yml                    # 厂商元数据（homepage / docs / affiliate / shared_features / rate_multipliers）
    plans/                        # 该厂商的所有套餐
      <plan_id>.yml
    official/                     # 厂商自己公布的一手数据
      YYYY-MM-DD_<短描述>.md      # 文字证据（Chrome dump / WebFetch 摘录）
      YYYY-MM-DD_<短描述>.png     # 截图证据（用户手截 / Chrome 截屏）
    scraped/                      # 我们从 web 抓的二手 / 第三方观察 / 社区推算
      YYYY-MM-DD_<短描述>.md
      YYYY-MM-DD_<短描述>.png
    evidence.md                   # 该厂商所有 evidence 的索引（可选）
```

**关键设计点**：

| 子目录 | 来源 | credibility |
|---|---|---|
| `official/` | 厂商自己的一手公布（官网 / 文档 / 公告） | high |
| `scraped/` | 我们抓的二手、社区推算、第三方观察、用户截图 | low / medium / disputed |

**官方 vs 抓取严格分开**——铁律 16 禁止把 scraped 数据当成 vendor_official。

---

## 文件命名规则

| 维度 | 规则 | 例子 |
|---|---|---|
| 日期 | `YYYY-MM-DD`（必填，按捕获时间） | `2026-07-31` |
| 描述 | 简短中文/英文，描述这次抓的是什么 | `opencode_go_official`, `kimi_allegretto_burn_test` |
| 后缀 | `.md` 文字，`.png` 图片，多图加 `_1/_2/_3` | `_1.png`, `_2.png` |

**避免**：空格、中文标点、特殊字符（用 `_` 分隔）

## 文字证据 (.md) frontmatter 必填字段

```yaml
---
evidence_id: e_2026_07_31_opencode_go      # 全局唯一
vendor_id: opencode                         # 厂商 ID
captured_at: 2026-07-31                     # 抓取日期（YYYY-MM-DD）
captured_by: claude                         # 抓取者（claude / user / 第三方工具）
source_url: https://opencode.ai/docs/zh-cn/go/  # 原始 URL
capture_method: chrome-dump-dom             # 抓取方法
data_status: vendor_official                # 数据状态
credibility: high                           # high / medium / low
file_path: data/opencode/official/...md     # 自身文件路径（自引用，方便索引）
related_plans:                              # 关联套餐 ID 列表
  - opencode-go
related_measurements:                       # 关联 measurement_id 列表
  - m_2026_07_opencode_go_official_pricing
---
```

## 文字证据 (.md) 正文建议结构

```markdown
# <一句话标题>

## 原文摘录

> 关键句子（用 blockquote 标注原文）

## 数据点

| 字段 | 值 | 备注 |
|---|---|---|
| pricing_first_month_usd | 5 | 首月特价 |
| pricing_monthly_usd | 10 | 续费 |

## 二次验证（必填）

- [ ] 已 Chrome dump 验证 / 已 WebFetch 验证 / 已 cross-check 厂商 docs 单价
- [ ] 关键数字 ≥ 2 个独立来源对账

## 不确定 / 存疑

（如有，写明；如无，写 "无"）

## 关联引用

- vendor: data/<vendor_id>/vendor.yml
- plan: data/<vendor_id>/plans/<plan_id>.yml
- measurement: <measurement_id>
```

## 截图证据 (.png) 命名

```
YYYY-MM-DD_<短描述>.png                # 单张
YYYY-MM-DD_<短描述>_1.png              # 多张第 1 张
YYYY-MM-DD_<短描述>_2.png              # 多张第 2 张
```

截图建议：
- 截全屏（不要只截相关行——上下文很重要）
- 命名里**说清是什么厂商的什么数据**
- 如果截图内容涉及价格 / 限额，**截到能看清数字的清晰度**

## yml 怎么引用 evidence

在 `data/<vendor>/plans/<plan>.yml` 的 measurements 数组里加字段：

```yaml
- measurement_id: m_2026_07_opencode_go_official_pricing
  source_kind: vendor_official
  source_url: https://opencode.ai/docs/zh-cn/go/
  evidence_path: data/opencode/official/2026-07-31_opencode_go_official.md
  captured_at: 2026-07-31
  credibility: high
  # 数据字段直接放（yml 自包含，前端 / build 不用打开 evidence 文件）
  pricing_first_month_usd: 5
  pricing_monthly_usd: 10
  cost_limit_5h_usd: 12
  # ...
```

**好处**：
- yml 仍然自包含（数字直接可读）
- evidence 文件存**原文 + 验证步骤**（审计追溯）
- 改 evidence 不污染 yml 数据字段

## 什么时候必须建 evidence 文件

| source_kind | 是否需要 evidence | evidence 放哪 |
|---|---|---|
| `vendor_official` | ✅ **必须**（lint 检查，铁律 28） | `data/<vendor>/official/` |
| `anthropic_official` | ✅ 必须（Anthropic 也是 vendor） | `data/anthropic/official/` |
| `vendor_scenario_estimate` | ⚠ 建议（场景估算容易有歧义） | `data/<vendor>/official/` |
| `per_model_breakdown` | ⚠ 建议 | `data/<vendor>/scraped/` |
| `single_user_probe` | ❌ 不需要 | — |
| `vendor_sibling_inferred` | ❌ 不需要 | — |
| `community_report` | ⚠ 建议（贴个社区截图更好） | `data/<vendor>/scraped/` |
| `aggregate_median` | ❌ 不需要 | — |
| `burn_quota` | ❌ 不需要 | — |

## 用户截图工作流

你可以直接把截图丢进 `data/<vendor>/scraped/` 目录，下次让我分析时：

1. 我直接 `ls` 这个目录看有哪些截图
2. 用 Read 工具（支持图片）逐张读图 + OCR / 视觉理解
3. 提取数据填进对应 plan.yml 的 measurements 数组
4. 在 evidence frontmatter 里引用截图路径

**截图命名规范**：`YYYY-MM-DD_<短描述>.png`
- ✅ `2026-08-01_kimi_allegretto_usage.png`
- ✅ `2026-08-01_opencode_go_pricing.png`
- ❌ `IMG_1234.png`
- ❌ `Screenshot 2026-08-01 123456.png`

## 迁移路径（从旧结构 — 待迁移）

| 旧路径 | 新路径 |
|---|---|
| `data/vendors/<vendor>.yml` | `data/<vendor>/vendor.yml` |
| `data/plans/<plan>.yml` | `data/<vendor>/plans/<plan>.yml` |
| `data/evidence/<vendor>/<file>.md` | `data/<vendor>/official/<file>.md` 或 `data/<vendor>/scraped/<file>.md` |

迁移还没开始，等用户授权后用一次性脚本 `scripts/migrate-vendor-structure.mjs`。
