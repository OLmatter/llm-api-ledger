---
evidence_id: e_2026_08_28_zai_devpack_credits_verified
vendor_id: zai
captured_at: 2026-08-28
captured_by: claude
source_url: https://docs.z.ai/devpack/
capture_method: webfetch
data_status: vendor_official
credibility: high
file_path: data/zai/official/2026-08-28_zai_devpack_credits_glm53.md
related_plans:
  - zai-glm-coding-lite-v3
  - zai-glm-coding-pro-v3
  - zai-glm-coding-max-v3
related_measurements:
  - m_2026_08_zai_devpack_credits_verified
---

# Z.AI GLM Coding Plan (devpack) 积分额度复核 —— 与账本 v3 一致，GLM-5.3 全量支持

## 原文摘录

> "All plans support GLM-5.3, GLM-5.3-Flash."
> "Requests for GLM-5.2/GLM-5.1 will be automatically routed to GLM-5.3"
> "Requests for GLM-4.7 route to GLM-5.3-Flash."
> "Starting at just 18 USD per month" (Lite)
> "credit quota resets 5 hours after consumption" / "resets every 7 days"
> "off-peak usage is charged at 50% of the standard credit rate"
> "peak hours are Mon–Fri, 14:00–18:00 UTC+8 (Singapore)"

## 数据点

| 字段 | Lite | Pro | Max | 备注 |
|---|---|---|---|---|
| 5h credits | 2,000 | 12,000 | 28,000 | 与账本 v3 一致 |
| 周 credits | 10,000 | 60,000 | 140,000 | 与账本 v3 一致 |
| 月付价格 | $18 起 | 未公示 | 未公示 | Pro/Max 价格页 JS 未渲染，账本 $80/$168 暂无法复核 |

## 机制变化（对账本口径有影响）

1. **闲峰五折**：工作日 14:00–18:00 (UTC+8) 为 peak 按标准扣；其余时段（含周末全天）积分按 **50%** 扣 → 实际可用量在闲峰时段等效 ×2。账本 measurements 目前按标准扣率反推 tokens，**未含闲峰加成**。
2. **模型自动路由**：5.2/5.1 请求自动路由到 GLM-5.3；GLM-4.7 请求路由到 GLM-5.3-Flash → 探针报的 model 字段可能与实际服务模型不一致。
3. **重置规则确认**：5h credits 从"消费后"起算 5 小时（非固定整点），周每 7 天重置。

## 二次验证（必填）

- [x] 已 WebFetch 官方 devpack 页直接抓取（非搜索转述）
- [x] credits 数字与账本 v3 yml / 线上榜单逐项对账一致（2000/1.2万/2.8万，1万/6万/14万）
- [ ] Pro/Max 月付价格未复核（官网 JS 未渲染），维持账本现值 $80/$168，标 last_verified 待更新

## 不确定 / 存疑

- Pro/Max 的 USD 定价本轮未能直接复核（z.ai/subscribe 为 JS 渲染）。
- 积分→token 换算系数官方未公示；账本的 tokens 反推值仍为估算口径。

## 关联引用

- vendor: data/vendors/zai.yml
- plans: data/plans/zai-glm-coding-{lite,pro,max}-v3.yml
- 同产品国内版: data/zhipu/official/2026-08-28_glm53_full_rollout.md
