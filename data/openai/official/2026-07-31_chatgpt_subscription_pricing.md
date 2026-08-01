---
evidence_id: e_2026_07_31_chatgpt_subscription_pricing
vendor_id: openai
captured_at: 2026-07-31
captured_by: claude
source_url: https://chatgpt.com/pricing
capture_method: playwright-stealth (Playwright + playwright-stealth bypass Cloudflare Turnstile)
data_status: vendor_official_partial
credibility: medium
related_plans:
  - chatgpt-plus
  - chatgpt-pro-5x
  - chatgpt-pro-20x
file_path: data/openai/official/2026-07-31_chatgpt_subscription_pricing.md
---

# ChatGPT 订阅套餐官方页面 (2026-07-31, 部分数据)

> ⚠ 抓取局限:用 Playwright + playwright-stealth 绕过 Cloudflare Turnstile 成功,但页面上 **`$X /month` 数字未渲染**(仅显示 "/ month")。已尝试 5 种等待策略(domcontentloaded/networkidle/30s/60s/90s),价格始终不显示。
> 推测原因:OpenAI 价格通过 API 按用户区域/auth 状态动态注入,headless + stealth 拿不到完整状态。

## 已抓到的页面结构 (可信)

**Title**: "ChatGPT Plans | Free, Go, Plus, Pro, Business, and Enterprise"
**Source**: https://chatgpt.com/pricing

### 个体套餐 6 档 + Business/Enterprise

| 套餐 | Slogan | 价格 (WebSearch 印证) | 关键内容 |
|---|---|---|---|
| **Free** | Best for trying out ChatGPT | $0/月 | Limited GPT-5.5 Instant,Limited messages/uploads/image/research/memory/Codex |
| **Go** | Best for longer conversations | **$8/月** (印度首发 2025-08, 2026 全球化) | More GPT-5.5 Instant + more messages/uploads/images/longer memory。**可能含广告**。 |
| **Plus** | Best for advanced work and productivity | **$20/月** | GPT-5.6 推理模型 + 扩展 messages + Projects/scheduled tasks/custom GPTs + 扩展 Codex |
| **Pro** | Best for research and coding | **$200/月** (From $100/$200 两个 variant) | 5x or 20x more usage, GPT-5.6 Sol Pro 推理, Maximum Codex/deep research/memory |
| **Business** | For teams (2+ users) | **$25/user/month** | SAML SSO + Admin console + SOC 2 + 32K context window + data 不用于训练 |
| **Enterprise** | For large orgs | 联系销售 | + 128K context + unlimited GPT-4o + SCIM + Data analytics + 专属客户经理 + API credits |

### 模型可用性 (跨套餐)

| Model | Free | Go | Plus | Pro |
|---|---|---|---|---|
| GPT-5.5 Instant | Limited | Expanded | Unlimited* | Unlimited* |
| GPT-5.6 Sol | — | — | Unlimited* | Unlimited* |
| GPT-5.6 Sol Pro | — | — | — | (独占) |
| GPT-5.6 Terra | Limited (Work/Codex) | Limited (Work/Codex) | — | Unlimited* |
| GPT-5.6 Luna | — | — | — | Unlimited* |
| GPT-5 Thinking Mini | Limited | — | Expanded | Unlimited* |

### Context Window (token)

| 维度 | Free | Go | Plus | Pro |
|---|---|---|---|---|
| GPT Instant 总窗口 | 27K | 54K | 54K | 128K |
| GPT Instant 输入最大 | ~12 pages | ~40 pages | ~40 pages | ~250 pages |
| GPT Reasoning 总窗口 | Varies | 256K | 256K | 400K |
| GPT Reasoning 输入最大 | Varies | ~320 pages | ~320 pages | ~680 pages |

### Business & Enterprise

| 套餐 | 关键特性 |
|---|---|
| **Business** | SAML SSO, Unified billing, Dedicated workspace, GPTs analytics, Admin console, Bulk member management, Admin roles, SOC 2 Type 2, Basic user analytics, Domain verification, ISO 27001/27017/27018/27701, SCIM |
| **Enterprise** | Enterprise Key Management, Granular GPT controls, Role-based access controls, Analytics dashboard, Compliance API Logs, IP allowlisting, Data residency (US/EU/UK/JP/CA/KR/SG/IN/AU/UAE), Intune for iOS, Branded workspace, Global admin console, Connector registry |

Business 起 2 用户;Enterprise 联系 sales。Business 含 nonprofits 75% 折扣。

### FAQ 摘录

- "Paid plans (Go, Plus, Business, and Enterprise) are priced per user per month"
- "Monthly plans for Go, Plus and Business; annual plans for Business and Enterprise"
- "ChatGPT for Teachers" 免费给美国 K-12 教育者(到 2027-06),ChatGPT Edu 大学校园版
- Nonprofits 75% 折扣 (Business/Enterprise)
- Free/Go/Plus 仅个人;Business 2+ 用户起;Enterprise 联系 sales
- 付款方式:信用卡 (Go/Plus/Pro/Business);Enterprise 接受发票

## ⚠ 价格未抓到的原因

1. **页面通过 API 动态注入价格**:HTML 静态部分不含 $X,JS 通过 fetch API 拿后注入
2. **API 可能需要 region/auth**:headless 无 auth cookie,可能拿到的是 null 占位
3. **价格依赖地理位置**:页面可能根据 IP 地区显示不同价格,headless + 单一 IP 可能拿到空
4. **缓存机制**:打开过的会话 cookie 可能缓存价格

## 替代证据策略(待办)

1. **WebSearch 多源印证** ✅ 已完成 - 见上方表格价格列
   - Free $0(稳定)
   - Go $8(2025-08 印度首发, 2026 全球化,腾讯新闻报道「OpenAI全面上线廉价版ChatGPT Go订阅方案:每月8美元」)
   - Plus $20(自 2025-08 起稳定)
   - Pro $200 / $100 5x variant(自 2024-12 起稳定)
   - Business $25/user(2026 WebSearch 多源印证)
   - Enterprise 联系销售(无公开价)
2. **OpenAI 新闻/博客**:chatgpt.com 官方 changelog 有时公布定价
3. **AI 媒体监测**:TechCrunch / The Verge 报道新套餐时必给价格
4. **手动截图**:用户在浏览器登录后截图

## 关联引用

- vendor: data/vendors/openai.yml
- plans: 
  - chatgpt-plus.yml (Plus tier)
  - chatgpt-pro-5x.yml (Pro 5x variant)  
  - chatgpt-pro-20x.yml (Pro 20x variant)
  - **缺**: chatgpt-go.yml, chatgpt-business.yml, chatgpt-enterprise.yml(本次发现新档位)
- 主页: https://chatgpt.com/pricing
- API 定价(已抓):data/openai/official/2026-07-31_openai_api_pricing.md

## 抓取脚本

`scripts/_stealth_chatgpt.py`(待沉淀到 scripts/)