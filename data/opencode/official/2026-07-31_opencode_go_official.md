---
evidence_id: e_2026_07_31_opencode_go
vendor_id: opencode
captured_at: 2026-07-31
captured_by: claude
source_url: https://opencode.ai/docs/zh-cn/go/
capture_method: chrome-dump-dom
data_status: vendor_official
credibility: high
related_plans:
  - opencode-go
related_measurements:
  - m_2026_07_opencode_go_official_pricing
file_path: data/opencode/official/2026-07-31_opencode_go_official.md
---

# OpenCode Go 官方定价与额度（2026-07-31）

## 原文摘录

> OpenCode Go 是一项低成本的订阅服务 —— 首月 5 美元,之后每月 10 美元
>
> • 首月 5 美元,之后每月 10 美元
> • 5 小时 12 美元的使用额度,每周 30 美元,每月 60 美元

## 数据点

| 字段 | 值 | 备注 |
|---|---|---|
| pricing_first_month_usd | 5 | 首月特价 |
| pricing_monthly_usd | 10 | 续费价（自动续费） |
| cost_limit_5h_usd | 12 | 5 小时窗口使用额度 |
| cost_limit_weekly_usd | 30 | 每周使用额度 |
| cost_limit_monthly_usd | 60 | 每月使用额度 |

## 二次验证

- [x] 已 Chrome --dump-dom 抓取（2026-07-31）
- [x] 已 cross-check 官方 docs（pricing / cost limit 表述一致）
- [x] 已与 v1 (旧文档) 对比——未发现变更

## 不确定 / 存疑

无

## 关联引用

- vendor: data/opencode/vendor.yml (待迁移)
- plan: data/opencode/plans/opencode-go.yml (待迁移)
- measurement: m_2026_07_opencode_go_official_pricing
- 推荐码（已在 vendor.yml）: AQ0H42B676（首月 +$5 credit）

## 附：抓取方式

```bash
"C:/Program Files/Google/Chrome/Application/chrome.exe" \
  --headless --disable-gpu --no-sandbox --dump-dom \
  "https://opencode.ai/docs/zh-cn/go/" > /tmp/opencode_go.html
```

抓取体积：约 26KB（已过滤 nav/footer）
