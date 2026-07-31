---
evidence_id: e_2026_07_31_openai_api_pricing
vendor_id: openai
captured_at: 2026-07-31
captured_by: claude
source_url: https://platform.openai.com/docs/pricing
capture_method: chrome-cdp-runtime-evaluate
data_status: vendor_official
credibility: high
related_plans:
  - chatgpt-plus
  - chatgpt-pro-5x
  - chatgpt-pro-20x
file_path: data/openai/official/2026-07-31_openai_api_pricing.md
---

# OpenAI Platform API 官方定价 (2026-07-31)

> ⚠ ChatGPT 订阅页 (chatgpt.com/pricing) 被 Cloudflare Turnstile 拦截,Chrome --dump-dom 只返回 11KB challenge HTML。本 evidence 记录的是 **API 定价**(platform.openai.com),ChatGPT 订阅价已在 `data/plans/chatgpt-plus.yml` 等 yml 中以 $20/$100/$200 月费定价(2025-2026 期间稳定)。

## Flagship Models (API 标准价 / 1M tokens)

| Model | Input | Cached input | Output | Batch Input | Batch Cached | Batch Output |
|---|---|---|---|---|---|---|
| **gpt-5.6-sol** | $5.00 | $0.50 | $30.00 | $10.00 | $1.00 | $45.00 |
| **gpt-5.6-terra** | $2.00 | $0.20 | $12.00 | $4.00 | $0.40 | $18.00 |
| **gpt-5.6-luna** | $0.20 | $0.02 | $1.20 | $0.40 | $0.04 | $1.80 |
| **gpt-5.5** | $5.00 | $0.50 | $30.00 | $10.00 | $1.00 | $45.00 |
| **gpt-5.5-pro** | $30.00 | — | $180.00 | $60.00 | — | $270.00 |
| **gpt-5.4** | $2.50 | $0.25 | $15.00 | $5.00 | $0.50 | $22.50 |
| **gpt-5.4-mini** | $0.75 | $0.075 | $4.50 | — | — | — |
| **gpt-5.4-nano** | $0.20 | $0.02 | $1.25 | — | — | — |
| **gpt-5.4-pro** | $30.00 | — | $180.00 | $60.00 | — | $270.00 |

## 多模态 / Realtime / 图像 / 视频 / 转写

(详细价格见原文 body 文本)

## 关键政策变化 (2026)

- **2026-03-05 起**:Regional processing (data residency) endpoints 加 10% uplift(仅限新发布且支持 residency 的模型)
- **2026-07-30 起**:Priority processing 改名为 **Fast mode**,可通过 `service_tier: "priority"` 或 `service_tier: "fast"` 调用

## 抓取方式

```bash
# Chrome DevTools Protocol via websocket,等 JS 完全渲染后抓取 innerText
# Chrome 默认 --dump-dom 对 SPA 只能拿到骨架,必须 CDP 主动等渲染
python scripts/_cdp_dump.py "https://platform.openai.com/docs/pricing" 25s
```

## 二次验证

- [x] 已 Chrome CDP Runtime.evaluate 抓取(2026-07-31)
- [x] Title: "Pricing | OpenAI API"
- [x] Body text 6288 字符,包含完整定价表
- [ ] **未验证** ChatGPT 订阅页(chatgpt.com/pricing 被 Turnstile 拦截,无法直接抓取)
- [ ] **未验证** GPT-5.6 系列是否有 cache writes 字段(原文 body 文本显示只列了 Input/Cached input/Output 三列,Cache writes 列数据空)

## 不确定 / 存疑

- **gpt-5.5-pro / gpt-5.4-pro 不支持 cached input**(官方显示 "—"),这与 vendor.yml 之前的 $3.00/M 标记冲突 — 需要修正 yml 数据。
- **Fast mode / Priority processing 实际价格加成**:文档未给出具体百分比,需要从 API 响应头验证。
- **2026-07-31 GPT-5.6 系列调价**:腾讯新闻/CSDN 报道 -20%/-80%,现与官方 platform.openai.com 报价匹配,**调价已生效**,原 vendor.yml 注 "⚠ 2026-07-31 调价来自腾讯新闻/CSDN 报道,等 OpenAI 官方页确认" 应改为"已确认"。

## 关联引用

- vendor: data/vendors/openai.yml
- plans: data/plans/chatgpt-plus.yml, data/plans/chatgpt-pro-5x.yml, data/plans/chatgpt-pro-20x.yml
- 主页: https://platform.openai.com/docs/pricing
- ChatGPT 主页(被 Turnstile 拦截): https://chatgpt.com/pricing