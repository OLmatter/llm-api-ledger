---
evidence_id: e_2026_08_28_volc_codingplan_verified
vendor_id: volcengine
captured_at: 2026-08-28
captured_by: claude
source_url: https://www.volcengine.com/product/coding-plan
capture_method: web-search-official-docs
data_status: vendor_official
credibility: high
file_path: data/volcengine/official/2026-08-28_volc_codingplan_verified.md
related_plans:
  - volc-coding-lite
  - volc-coding-pro
related_measurements:
  - m_2026_08_volc_no_price_change
---

# 火山方舟 Coding Plan 价格复核：Lite/Pro 无变化；方舟侧新增 Serverless OpenClaw

## 原文摘录

> 火山方舟文档（套餐概览）："本文介绍火山方舟 Coding Plan 的套餐概览，涵盖支持的主流模型、兼容的 AI 编码工具，以及 Lite 与 Pro 套餐的适用场景等核心内容"
> 第三方横评（CodePick 2026-08）：Lite ¥40/月（限时 ¥9.9 起，1200 次/5h，7 天试用）；Pro ¥200/月（活动价常见 ¥49.9，6000 次/5h）
> 方舟动态："Coding Plan 上线 Serverless OpenClaw，开箱即用、免运维免服务器"
> 模型侧：整合豆包系列模型与第三方编程模型，支持多模型切换

## 数据点

| 字段 | 值 | 与账本对比 |
|---|---|---|
| Lite | ¥40/月，首月 ¥9.9，1200 次/5h，9000 次/周 | 一致 ✓ |
| Pro | ¥200/月，首月 ¥49.9，6000 次/5h，4.5万 次/周 | 一致 ✓ |

## 结论（对账本的动作）

1. **两档现价与额度与账本一致，本轮不改数**；`last_verified` 更新 2026-08-28。
2. 方舟"Serverless OpenClaw"属厂商级动态，可在 vendor.yml 后续迭代时收录（不影响套餐字段）。
3. 榜单实测 @GLM-5.2（11.9M/89.4M/179M Lite）——火山接入了 GLM 系第三方模型，与官方"第三方优质编程模型"口径一致。

## 二次验证（必填）

- [x] 官方套餐概览文档存在且口径一致（搜索转述 + 官方 URL）
- [x] Lite/Pro 价格与账本逐项对账一致（首月价、5h/周次数）
- [ ] 购买页 JS 渲染，未直抓价签原文

## 不确定 / 存疑

- "首月 ¥9.9"活动价截止时间未公示，若 9 月复核发现变动以此为先。

## 关联引用

- vendor: data/vendors/volcengine.yml
- plans: data/plans/volc-coding-{lite,pro}.yml
