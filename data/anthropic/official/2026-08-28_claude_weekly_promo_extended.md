---
evidence_id: e_2026_08_28_claude_weekly_promo_extended
vendor_id: anthropic
captured_at: 2026-08-28
captured_by: claude
source_url: https://news.ycombinator.com/item?id=claude-code-weekly-limits
capture_method: web-search-community
data_status: community_report
credibility: medium
file_path: data/anthropic/official/2026-08-28_claude_weekly_promo_extended.md
related_plans:
  - claude-code-pro
related_measurements:
  - m_2026_08_weekly_promo_reextended
---

# Claude Code 周 +50% 促销再度两次延期，现至 2026-08-31（与账本"已结束"结论冲突）

## 原文摘录

> HN 讨论（Claude Code May–August 2026 weekly limits promotion）：
> "Anthropic's latest Claude Code weekly limits promotion — the 50% increase to weekly Claude Code limits was first extended through **August 19, 2026**, then extended again through **August 31, 2026**. This benefit applies to Pro, Max, Team, and Enterprise users."
> 另（同期搜索）："Claude Fable 5 added to Max and Team plans"（Fable 5 从"仅 usage credits"变为 Max/Team 可用）
> "Opus 4.1 deprecation — retirement from the API on August 5, 2026"

## 数据点

| 字段 | 值 | 与账本对比 |
|---|---|---|
| 周 +50% 促销状态 | **生效中，至 2026-08-31** | 账本 claude-code-pro 记"2026-07-19 结束，未再次延期"→ **已过时** |
| 适用范围 | Pro / Max / Team / Enterprise | Pro 受影响（weekly/monthly 实际可用 +50%） |
| Max 5x / Max 20x | $100 / $200 每月（support.claude.com） | 账本按铁律 18 未建 yml——本轮仍不建（未直接实测），仅在 evidence 记录 |
| Opus 4.1 | API 端 2026-08-05 退役 | 订阅内使用待确认；账本 per-model 拆分含 opus-4-1 行 |
| Fable 5 | Max/Team 套餐内可用（新） | Pro 仍仅 usage credits（账本口径不变） |

## 结论（对账本的动作）

1. `claude-code-pro.yml` 新增 measurement：周 +50% 促销**复活并延期至 2026-08-31**（credibility=medium，社区对官方政策的转述，非官方页直抓）。weekly/monthly 的 `tokens_measured` 字段**维持剥离口径**（铁律 17：标准价为底，促销不写入基础字段），由该 measurement 提示"8 月内实际可用 +50%"。
2. 9-01 后需复核促销是否第三次延期；若结束，无需回改（账本本就是剥离口径）。
3. Opus 4.1 API 退役不影响订阅内使用口径，但 per-model 拆分中 opus-4-1 行标注"API 已退役"。

## 二次验证（必填）

- [x] HN 原帖 + 多源转述一致（两次延期时间线自洽：7-19 → 8-19 → 8-31）
- [ ] anthropic.com/pricing 为 JS 页未直接抓到促销 banner 原文 → credibility 降为 medium
- [ ] Max 5x/20x 官方 help 页未直抓，铁律 18 维持（不建 Max yml）

## 不确定 / 存疑

- 促销是否 9 月后第三次延期未知。
- Fable 5 进 Max/Team 的具体额度口径未核实。

## 关联引用

- vendor: data/vendors/anthropic.yml
- plan: data/plans/claude-code-pro.yml
- 前序 evidence: data/anthropic/official/2026-07-31_claude_pro_pricing.md
