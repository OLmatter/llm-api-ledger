---
evidence_id: e_2026_07_31_anthropic_claude_pro
vendor_id: anthropic
captured_at: 2026-07-31
captured_by: claude
source_url: https://www.anthropic.com/pricing
capture_method: chrome-dump-dom
data_status: anthropic_official
credibility: high
related_plans:
  - claude-code-pro
related_measurements:
  - m_2026_05_5h_doubling_permanent
  - m_2026_07_weekly_promo_50pct_expired
file_path: data/anthropic/official/2026-07-31_claude_pro_pricing.md
---

# Anthropic Claude Pro 官方数据 (2026-07-31)

## 原文摘录（anthropic.com/pricing）

> **Claude Pro** — $20 / month
> Get 5× more usage per 5-hour session than Claude Free
>
> **Claude Max** — Starting at $100 / month
> 5× Claude Pro usage, scaled to your needs
> Or **Max 20×** at $200 / month

## 数据点

### 订阅价格

| 套餐 | 月付 | 年付 | 年付折月 |
|---|---|---|---|
| Free | $0 | — | — |
| Pro | $20 | $200 | $17 |
| Max 5× | $100 | — | — |
| Max 20× | $200 | — | — |

### 5h 成本上限（cost limit）

| 时间 | Pro | Max 5× | Max 20× |
|---|---|---|---|
| 2026-05-06 ~ 2026-07-19 | $18/5h | — | — |
| 2026-07-20 之后 | **$36/5h**（×2 永久）| $90/5h | $180/5h |
| 周促销（5/19~7/19）| ×1.5 临时 | — | — |

> 反推：Pro 5h 36M tokens（按 Opus 5 effective $1.00/M 算）

### 周/月成本上限（anthropic 酌定）

- 周上限 Pro $? / Max 5× $? / Max 20× $?
- 月上限 同上
- **不保证按 5×/20× 等比缩放**

## 二次验证

- [x] 已 Chrome --dump-dom 抓取 anthropic.com/pricing（2026-07-31）
- [x] 价格档（$20/$100/$200）多次匹配源 HTML
- [ ] **未验证** 5h cost limit 数字——anthropic.com/pricing 只展示订阅价，cost limit 在 docs.anthropic.com
- [ ] **未验证** weekly promo 50% 数字——yml 注的是 community 抓的，原始公告已撤回

## 不确定 / 存疑

- **5h cost limit 数字来源**：anthropic.com/pricing 不直接显示，而是 docs.anthropic.com 订阅条款页。**当前 evidence 是基于 yml 历史 + 已知公告推断**。
- **Max 5×/20× 周/月上限**：anthropic 明确表示"weekly/monthly caps 由 Anthropic 酌定"，**实际数字需要用户实测验证**——本 evidence 不记录。

## 关联引用

- plan: data/anthropic/plans/claude-code-pro.yml (待迁移)
- vendor: data/anthropic/vendor.yml (待迁移)
- 主页: https://www.anthropic.com/pricing
- 订阅文档: https://docs.anthropic.com/en/docs/build-with-claude/subscription
- Claude Opus 5 发布: https://www.anthropic.com/news/claude-opus-5

## 附：抓取方式

```bash
"C:/Program Files/Google/Chrome/Application/chrome.exe" \
  --headless --disable-gpu --no-sandbox \
  --virtual-time-budget=15000 \
  --dump-dom "https://www.anthropic.com/pricing" > /tmp/anthropic_pricing.html

# 体积：~2MB（含 React + 全页 hydration）
# 关键数字（grep 美元价）
grep -oE "\\\$20|\\\$100|\\\$200|5-hour|weekly" /tmp/anthropic_pricing.html | sort | uniq -c
```