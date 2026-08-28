---
evidence_id: e_2026_08_28_zhipu_glm53_rollout
vendor_id: zhipu
captured_at: 2026-08-28
captured_by: claude
source_url: https://docs.bigmodel.cn/cn/coding-plan/overview
capture_method: web-search-official-docs
data_status: vendor_official
credibility: high
file_path: data/zhipu/official/2026-08-28_glm53_full_rollout.md
related_plans:
  - zhipu-glm-coding-lite-v3
  - zhipu-glm-coding-pro-v3
  - zhipu-glm-coding-max-v3
  - zhipu-glm-coding-lite
  - zhipu-glm-coding-pro
  - zhipu-glm-coding-max
related_measurements:
  - m_2026_08_zhipu_glm53_rollout
---

# 智谱 GLM-5.3 发布并全量接入 GLM Coding Plan；v3 积分制价格复核

## 原文摘录

> 智谱AI开放文档（coding-plan/overview）："可用模型：所有套餐均支持 GLM-5.3、GLM-5.3-Flash。"
> 智谱AI开放文档（GLM-5.3 模型页）："GLM-5.3 是智谱最新旗舰模型……采用基于积分的配额系统,额度公开透明。消耗标准积分的50%。"（GLM-5.3-Flash 半价）
> IT之家（2026-07-31）："智谱 GLM Coding Plan 订阅回归：透明积分制，每月 118 元起"
> 新浪财经（2026-07-31）：Lite ¥49 → ¥118/月，Pro ¥149 → ¥538/月，Max ¥469 → ¥1078/月

## 数据点

| 字段 | 值 | 备注 |
|---|---|---|
| GLM-5.3 发布 | 2026-08-14 | 编程能力比 GLM-5.2 提升约 50%，同基座后训练扩展 |
| Coding Plan 接入 | 全量（所有档位） | 含 GLM-5.3-Flash |
| v3 价格（7-31 上线） | Lite ¥118 / Pro ¥538 / Max ¥1078 每月 | 与账本 zhipu-*-v3 yml 一致，无需改价 |
| 积分闲峰五折 | 工作日 14:00–18:00 (UTC+8) 为 peak，其余 50% | 与 z.ai 同规则（同产品） |
| 老用户权益 | docs.bigmodel.cn/cn/coding-plan/notice/usage-revision | v2 用户迁移说明 |

## 结论（对账本的动作）

1. **价格**：v3 三档现价与账本一致，本轮**不改价**。
2. **模型**：zhipu 全部 6 个 plan yml 的模型口径应标注"GLM-5.3 / GLM-5.3-Flash 全量支持"；v2 用户按老用户权益说明迁移（v2 状态待观察，暂不标 deprecated）。
3. **实测 tokens 数字**：榜单现有 @GLM-5.2 探针值仍是有效实测（历史观测），但同额度下 GLM-5.3 消耗积分为标准的 50%（Flash），实际可用 token 会有结构性变化——待新一轮探针实测。

## 二次验证（必填）

- [x] 官方文档 coding-plan/overview（模型支持）——搜索转述 + 官方页标题双重确认
- [x] v3 价格与账本/榜单对账一致（¥118/538/1078）
- [x] GLM-5.3 发布日期（2026-08-14）多源一致（36氪/官方文档）
- [ ] bigmodel.cn/glm-coding 购买页 JS 渲染，未直接抓到价签原文

## 不确定 / 存疑

- GLM-5.3 时代积分→token 换算系数未公布，账本 tokens 反推值口径不变。
- 7-31 上线时有限时折扣（年付 7 折/季付 8 折，至 8-15），已过期，不影响标准价。

## 关联引用

- plans: data/plans/zhipu-glm-coding-{lite,pro,max}-v3.yml、data/plans/zhipu-glm-coding-{lite,pro,max}.yml
- 海外同产品: data/zai/official/2026-08-28_zai_devpack_credits_glm53.md
