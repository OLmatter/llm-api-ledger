---
evidence_id: e_2026_08_28_chatgpt_go_global_models
vendor_id: openai
captured_at: 2026-08-28
captured_by: claude
source_url: https://openai.com/zh-Hans-CN/index/introducing-chatgpt-go/
capture_method: web-search-official-announcement
data_status: vendor_official
credibility: high
file_path: data/openai/official/2026-08-28_chatgpt_go_global_5p6luna.md
related_plans:
  - chatgpt-go
  - chatgpt-plus
  - chatgpt-business
  - chatgpt-pro-5x
  - chatgpt-pro-20x
related_measurements:
  - m_2026_08_chatgpt_go_global_luna
---

# ChatGPT Go 全球开放（$8 官宣）；GPT-5.6 Luna 对 Free/Go 无限聊天；o3 退役

## 原文摘录

> OpenAI 官方（2026-08-26）："ChatGPT Go 每月 8 美元*；ChatGPT Plus 每月 20 美元；ChatGPT Pro 每月 200 美元。*所示价格为美国定价。ChatGPT Go 现已面向全球用户开放。"
> 第三方评测（2026-08-08）："OpenAI 宣布 Free 与 Go 套餐可使用 GPT-5.6 Luna 提供无限文字聊天和 Think 按钮；Plus 与 Pro 的普通 Chat 改用新版 Sol 模型"
> OpenAI 帮助中心："o3 将于 2026 年 8 月 26 日从 ChatGPT 下线"
> 知乎套餐解析：Business "年付 $25/人/月，月付 $30/人/月"

## 数据点

| 字段 | 值 | 与账本对比 |
|---|---|---|
| Go 月付 | $8（美国定价，全球开放） | 一致 ✓；账本"首月 $5"促销未复核 |
| Plus 月付 | $20 | 一致 ✓ |
| Pro | $200（另有 $100 档讨论，未官宣新档） | 一致 ✓（Pro 5x/20x 结构不变） |
| Business | 年付 $25/人/月，**月付 $30/人/月** | ⚠ 账本 business yml 记 $25/月未区分计费周期，需补注 |
| 模型动态 | GPT-5.6 Luna 对 Free/Go 无限文字聊天；o3 8-26 退役 | 榜单已有 @gpt-5.6-luna 实测，口径吻合 |

## 结论（对账本的动作）

1. 五档价格**均无需改**；`last_verified` 更新 2026-08-28。
2. `chatgpt-business.yml` 补注：$25 为年付折月，月付 $30/人/月。
3. `chatgpt-go.yml` 补注：Go 已全球开放（此前区域限制解除），模型权益变化（Luna 无限聊天不占 token 额度口径——影响"实测 tokens"的解读：Luna 聊天部分不计入）。

## 二次验证（必填）

- [x] OpenAI 官方公告页（Go $8 / Plus $20 / Pro $200 + 全球开放）——官方 URL 直出
- [x] o3 退役日期（OpenAI 帮助中心）
- [ ] Business 双轨定价仅第三方转述，官方页 JS 未直抓 → 补注标 medium

## 不确定 / 存疑

- Go "首月 $5" 促销是否仍在售未核实。
- Pro $100 档：仅社区讨论，无官宣，**不建档**。

## 关联引用

- vendor: data/vendors/openai.yml
- plans: data/plans/chatgpt-{go,plus,business,pro-5x,pro-20x,enterprise}.yml
