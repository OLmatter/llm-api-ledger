---
evidence_id: e_2026_08_28_opencode_rate_card_refresh
vendor_id: opencode
captured_at: 2026-08-28
captured_by: claude
source_url: https://opencode.ai/docs/zh-cn/go/
capture_method: webfetch
data_status: vendor_official
credibility: high
file_path: data/opencode/scraped/2026-08-28_opencode_rate_card_refresh.md
related_plans:
  - opencode-go
related_measurements:
  - m_2026_08_opencode_model_list_refresh
---

# OpenCode Go 费率卡刷新：GLM-5.3-Flash / Qwen3.8 / Grok 4.6（官方直抓 2026-08-28）

## 原文摘录

> 订阅：Go 每月 $10。"我们的目标是为你提供 6 倍于此的使用额度"
> 限制：5h $12 / 周 $30 / 月 $60 使用额度
> "GLM-5.3-Flash | $0.15 | $0.50 | $0.03 | — | $15"
> "Grok 4.6 (≤200K) | $2.00 | $6.00 | $0.50 | — | $15"；"Grok 4.6 (>200K) | $4.00 | $12.00 | $1.00 | — | $15"
> "Qwen3.8 Flash | $0.15 | $0.47 | $0.016 | $0.20 | $30"；"Qwen3.8 Max | $2.00 | $6.00 | $0.25 | $2.50 | $15"
> Peak 说明（DS 系列）："Peak 时段为周一至周五的 01:00-04:00 和 06:00-10:00 UTC"

## 与账本的对账结论

1. **GLM-5.3-Flash 整行缺失**（用户报）→ 已补：$0.15/$0.50/$0.03，$15 档。
   z.ai 侧 5.3-Flash 为促销价（五折至 2026-09-09），opencode 报价与促销价一致；
   促销结束后基础价未公示，9-9 后复核（铁律 11 expires 逻辑）。
2. **Grok 版本过时**：账本写 Grok 4.5，官方现为 Grok 4.6 → 已更正。
3. **Qwen3.8 系列缺失**：Qwen3.8 Max（$15 档）、Qwen3.8 Flash（$30 档）→ 已补档位说明。
4. **$60 档列表不全**：补 LongCat-2.0 / MiniMax M3 / MiniMax M2.7-M2.5 / Muse Spark 1.2。
5. DS V4 Flash/Pro 峰谷价与本账本 2026-08-28 已录行逐项一致（铁律 23 零加价复核通过）。

## 二次验证（必填）

- [x] opencode 官方文档 WebFetch 直抓（2026-08-28）
- [x] GLM-5.3-Flash / DS / Grok / Qwen3.8 数字逐项照录
- [ ] GLM-5.3-Flash 基础价（促销后）官方未公示，存疑

## 不确定 / 存疑

- GLM-5.3-Flash 基础价（9-9 后）未公布；推断为 $0.30/$1.00（促销五折反推），**推断值不入 yml**。
- "有人说 opencode 数据不对"的具体所指未获逐项确认，本轮按费率卡全量对账处理。

## 关联引用

- plan: data/plans/opencode-go.yml
- 关联: data/deepseek/official/2026-08-28_ds_peak_valley_pricing.md（DS 峰谷）
