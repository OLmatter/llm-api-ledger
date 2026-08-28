---
evidence_id: e_2026_08_28_ds_peak_valley_pricing
vendor_id: deepseek_intl
captured_at: 2026-08-28
captured_by: claude
source_url: https://api-docs.deepseek.com/quick_start/pricing
capture_method: webfetch
data_status: vendor_official
credibility: high
file_path: data/deepseek/official/2026-08-28_ds_peak_valley_pricing.md
related_plans:
  - opencode-go
related_measurements:
  - m_2026_08_ds_peak_valley_full_table
---

# DeepSeek API 峰谷定价全表（官方直抓）；V4 全系列 8-13 正式版、8-17 新价生效、周末全天谷价

## 原文摘录

> "Off-peak rates are half of the peak rates."
> "Peak hours are 01:00 - 04:00 and 06:00 - 10:00 UTC, Monday through Friday (all other hours are off-peak)."
> "Product prices may vary and DeepSeek reserves the right to adjust them."

（北京时间即工作日 9:00–12:00、14:00–18:00 为高峰；周末全部时段均为谷价）

## 数据点（USD / 1M tokens，官方直抓 2026-08-28）

| 类别 | v4-flash 谷 | v4-flash 峰 | v4-pro 谷 | v4-pro 峰 | vision-exp 谷/峰 |
|---|---|---|---|---|---|
| 输入（缓存命中） | $0.007 | $0.014 | $0.022 | $0.044 | $0.007 / $0.014 |
| 输入（缓存未命中） | $0.22 | $0.44 | $0.66 | $1.32 | $0.22 / $0.44 |
| 输出 | $0.66 | $1.32 | $1.98 | $3.96 | $0.66 / $1.32 |

其他：上下文 1M；最大输出 384K；并发 v4-flash 2500 / v4-pro 500。无独立"缓存写入"价。

## 国内版人民币价（api-docs.deepseek.com/zh-cn，官方直抓 2026-08-28）

| 类别 | v4-flash 谷/峰 | v4-pro 谷/峰 |
|---|---|---|
| 输入（缓存命中） | ¥0.05 / ¥0.10 | ¥0.15 / ¥0.30 |
| 输入（缓存未命中） | ¥1.5 / ¥3.0 | ¥4.5 / ¥9.0 |
| 输出 | ¥4.5 / ¥9.0 | ¥13.5 / ¥27.0 |

注意：中文站只标人民币，国际站只标美元，两站是同源不同账户（registry: deepseek_intl）。
换算核对：¥1.5 ≈ $0.21 ≈ 国际 $0.22，实质同价不同币种。

## 事件时间线

- 2026-08-06：预告 API 涨价（"价格屠夫"告别低价策略）
- 2026-08-13：**DeepSeek-V4 全系列正式版上线**（V4-Pro 正式版），发布调价公告
- 2026-08-17 0 时（北京时间）：峰谷新价生效；谷价为峰价一半
- ⚠ 媒体口径修正：此前转述的"旧价约 ¥20/M 输入、¥100/M 输出、最高涨幅 1100%"与官方价格表对不上
  （v4-pro 峰价也仅 ¥9 输入 / ¥27 输出），判定为报道失实，不采信。实际幅度：峰价 = 谷价 ×2。
- 2026-08-23 0 时：周末计费新规——周六周日全天按谷价（与当前官方表格"高峰仅限周一至周五"口径一致）

## 对账本的动作

1. `opencode-go.yml` 模型单价表此前只录 Off-Peak 行（0.22/0.66/0.007，与本表谷价完全一致 ✓）；本次补 **Peak 行**（0.44/1.32/0.014）与 **V4-Pro 行**（Go $15 档模型列表含 DeepSeek V4 Pro）。
2. Go 的 DS 实测（2.19B tokens 等）为 7 月末跑量——当时是旧平价；峰谷制后同样 token 量的成本取决于跑量时段，**性价比解读需带时段假设**（周末/夜间跑 = 谷价不变，工作日白天跑 = 成本翻倍）。
3. DeepSeek 为纯 API 厂商（无订阅套餐），registry 已预登记 `deepseek_intl`（未收录状态）；本 evidence 挂其名下，暂不建 plans。

## 二次验证（必填）

- [x] 官方 pricing 页 WebFetch 直抓（非搜索转述），全表数字逐项照录
- [x] 谷价与账本 opencode-go.yml 已录 Off-Peak 行完全一致（交叉验证）
- [x] 高峰时段 UTC 定义与中文报道（北京 9-12/14-18 点）换算一致
- [ ] 8-17/8-23 生效日期来自官方更新日志与媒体报道（官方 pricing 页不标日期）

## 不确定 / 存疑

- 旧平价（¥20/M 输入）与现峰价的精确倍数未从官方页核到原表，"最高涨 1100%"为媒体口径。

## 关联引用

- plan（受影响成本侧）: data/plans/opencode-go.yml
- registry: data/registry/vendors.yml#deepseek_intl
