---
evidence_id: e_2026_08_28_minimax_tokenplan_verified
vendor_id: minimax
captured_at: 2026-08-28
captured_by: claude
source_url: https://platform.minimaxi.com/docs/token-plan/promotion
capture_method: web-search-official-docs
data_status: vendor_official
credibility: high
file_path: data/minimax/official/2026-08-28_minimax_tokenplan_verified.md
related_plans:
  - minimax-tp-plus
  - minimax-tp-max
  - minimax-tp-ultra
related_measurements:
  - m_2026_08_minimax_no_price_change
---

# MiniMax Token Plan 价格复核：三档无变化；M3 API 降价与邀请活动节点记录

## 原文摘录

> MiniMax 开放平台文档（订阅活动）："邀请共建活动：2025 年 12 月 26 日至 2026 年 8 月 31 日。参与资格——邀请人：所有 MiniMax 开放平台 Token Plan 的有效订阅用户（包含历史订阅用户）"
> 腾讯云 TokenHub 公告（转述）：自 2026-06-15 起 MiniMax-M3 推理输入、输出及缓存命中费用下调 50%

## 数据点

| 字段 | 值 | 与账本对比 |
|---|---|---|
| Plus 月付 | ¥49 | 一致 ✓ |
| Max 月付 | ¥119（年 ¥1190） | 一致 ✓ |
| Ultra 月付 | ¥469（年 ¥4690） | 一致 ✓ |
| M3 API 输入价（≤512K） | ¥2.1/M tokens（6-15 五折后） | API 价，非套餐字段 |

## 事件时间线（背景，不影响现价）

- 2026-03-23：Coding Plan 升级为 Token Plan（全模态调用，M3/M2.7 + 图像/语音/音乐）
- 2026-06 上旬：次数/额度制改 Token 计费引发"变相涨价"争议，官方致歉并公布迁移方案（Plus/Max 价格不变保留折扣；Ultra 老年包按订阅日切到 ¥469/月多退少补）
- 2026-06-15：M3 API 五折
- 2026-08-31：邀请共建活动截止（邀请码 9 折渠道的官方依据到期日）

## 结论（对账本的动作）

1. **三档现价与账本一致，本轮不改价**；`last_verified` 更新为 2026-08-28。
2. **邀请码 9 折的有效性绑定"邀请共建活动"8-31 截止**——榜单 Plus/Max/Ultra 的"用邀请码 ¥44.1/107.1/422.1"列在 9-1 后可能失效，届时需复核（已列入 follow-up）。
3. M3 API 降价不直接改套餐限额，但同样的 token 额度下官方成本减半——性价比排名的"厂商成本侧"参考。

## 二次验证（必填）

- [x] 官方 promotion 文档（活动起止）——搜索转述 + 官方 URL
- [x] 三档价格与账本/榜单对账一致
- [ ] 购买页（JS 渲染）未直接抓到价签原文

## 不确定 / 存疑

- Ultra "极速版 ¥899" 老包已迁移完毕与否未核实（账本未收录该历史档，不影响）。

## 关联引用

- vendor: data/vendors/minimax.yml
- plans: data/plans/minimax-tp-{plus,max,ultra}.yml
