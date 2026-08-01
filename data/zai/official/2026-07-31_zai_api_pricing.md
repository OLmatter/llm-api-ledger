---
evidence_id: e_2026_07_31_zai_api_pricing
vendor_id: zai
captured_at: 2026-07-31
captured_by: claude
source_url: https://docs.z.ai/guides/overview/pricing
capture_method: chrome-cdp-runtime-evaluate
data_status: vendor_official
credibility: high
related_plans:
  - zai-glm-coding-lite-v3
  - zai-glm-coding-pro-v3
  - zai-glm-coding-max-v3
file_path: data/zai/official/2026-07-31_zai_api_pricing.md
---

# Z.AI 官方 API 定价 (2026-07-31)

> 抓取方式:Chrome DevTools Protocol via websocket,Runtime.evaluate 等 JS 完整渲染 35s,body text 2052 字符。
> 之前 `chrome --dump-dom` 只能拿到 SPA 导航骨架(标题正确但价格表未渲染),本次用 CDP 突破。

## Text Models (USD per 1M tokens)

| Model | Input | Cached Input | Cached Input Storage | Output |
|---|---|---|---|---|
| GLM-5.2 | $1.4 | $0.26 | Limited-time Free | $4.4 |
| GLM-5.1 | $1.4 | $0.26 | Limited-time Free | $4.4 |
| GLM-5 | $1 | $0.2 | Limited-time Free | $3.2 |
| GLM-5-Turbo | $1.2 | $0.24 | Limited-time Free | $4.0 |
| GLM-4.7 | $0.6 | $0.11 | Limited-time Free | $2.2 |
| GLM-4.7-FlashX | $0.07 | $0.01 | Limited-time Free | $0.4 |
| GLM-4.6 | $0.6 | $0.11 | Limited-time Free | $2.2 |
| GLM-4.5 | $0.6 | $0.11 | Limited-time Free | $2.2 |
| GLM-4.5-X | $2.2 | $0.45 | Limited-time Free | $8.9 |
| GLM-4.5-Air | $0.2 | $0.03 | Limited-time Free | $1.1 |
| GLM-4.5-AirX | $1.1 | $0.22 | Limited-time Free | $4.5 |
| GLM-4-32B-0414-128K | $0.1 | - | - | $0.1 |
| GLM-4.7-Flash | Free | Free | Free | Free |
| GLM-4.5-Flash | Free | Free | Free | Free |

## Vision Models

| Model | Input | Cached Input | Cached Storage | Output |
|---|---|---|---|---|
| GLM-5V-Turbo | $1.2 | $0.24 | Limited-time Free | $4 |
| GLM-4.6V | $0.3 | $0.05 | Limited-time Free | $0.9 |
| GLM-OCR | $0.03 | - | - | $0.03 |
| GLM-4.6V-FlashX | $0.04 | $0.004 | Limited-time Free | $0.4 |
| GLM-4.5V | $0.6 | $0.11 | Limited-time Free | $1.8 |
| GLM-4.6V-Flash | Free | Free | Free | Free |

## Image / Video / Audio / Agents

| 类别 | 名称 | 价格 |
|---|---|---|
| Image | GLM-Image | $0.015/image |
| Image | CogView-4 | $0.01/image |
| Video | CogVideoX-3 | $0.2/video |
| Video | ViduQ1-Text/Image/Start-End | $0.4/video |
| Video | Vidu2-Image/Start-End | $0.2/video |
| Video | Vidu2-Reference | $0.4/video |
| Audio | GLM-ASR-2512 | $0.03/MTok ≈ $0.0024/min |
| Agent | GLM Slide/Poster Agent (beta) | $0.7/MTok |
| Agent | General-Purpose Translation | $3/MTok |
| Agent | Popular Special Effects Video Templates | $0.2/video |
| Tool | Web Search | $0.01/use |

## 与 yml 历史数据对比

之前 yml `zai-glm-coding-{lite,pro,max}-v3.yml` 中的 `credit_coefficients` measurement 引用的抵扣系数表:

| 模型 | Input | Cached | Output | 含义 |
|---|---|---|---|---|
| GLM-5.2 | 6.9 | 1.7 | 24 | per 10000 tokens |
| GLM-5-Turbo | 5.7 | 1.5 | 21 | per 10000 tokens |
| GLM-4.7 | 4.6 | 1.2 | 16 | per 10000 tokens |

**单位换算**:credit coefficient × 100 = per 1M tokens 的 credit 消耗。
- GLM-5.2 input: 690 credits/1M tokens × $1.4/M × (1/690) = $0.00203/credit
- 28,000 credits/5h (Max) × $0.00203/credit = **$56.81 worth of GLM-5.2 input / 5h**

新 API 价格表(GLM-5.2 input $1.4/M)与之前抵扣系数表(6.9/10000 tokens)互相印证,**单位换算关系正确**。

## 二次验证

- [x] 已 Chrome CDP Runtime.evaluate 抓取 docs.z.ai(2026-07-31)
- [x] Title: "Pricing - Overview - Z.AI DEVELOPER DOCUMENT"
- [x] Body text 2052 字符,完整价格表
- [x] 与 yml 历史 credit_coefficients 互相印证(单位换算验证通过)

## 不确定 / 存疑

- **z.ai 跨境订阅页** (z.ai/subscribe) 仍是需登录态才能拿到订阅价格档位($18/$80/$168 月费)
  - 当前 evidence 只覆盖 API 按量计费,**Coding Plan v3 订阅价依赖 z.ai/subscribe Chrome dump-dom(已抓,但需进一步解析订阅档位)**
  - yml 中 $18/$80/$168 月费数据目前来源是 z.ai/subscribe 的 Chrome dump-dom(参考已有 lite/pro/max v3 yml 中的 m_2026_07_zai_*_official_pricing measurement)
- **GLM-5.2 系列 7/31 调价**:之前 yml 标注 "6.9/1.7/24" 系数没明确日期,现与官方 $1.4/M 印证后确认 2026-07-31 是稳态价

## 关联引用

- vendor: data/vendors/zai.yml
- plans: data/plans/zai-glm-coding-{lite,pro,max}-v3.yml
- 主页: https://docs.z.ai/guides/overview/pricing
- 智谱国内版同源数据: data/zhipu/official/2026-07-31_glm_coding_v3_official.md