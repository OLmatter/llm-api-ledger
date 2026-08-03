---
evidence_id: e_2026_08_04_tencent_coding_plan_intro
vendor_id: tencent
captured_at: 2026-08-04
captured_by: claude
source_url: https://cloud.tencent.com/developer/article/2638167
capture_method: chrome-dump-dom
data_status: vendor_official
credibility: high
file_path: data/tencent/official/2026-08-04_coding_plan_intro.md
related_plans:
  - tencent-coding-lite
  - tencent-coding-pro
---

# 腾讯云 Coding Plan 上架介绍 (2026-03-12 发布)

## 原文摘录

> 上新！腾讯云大模型 Coding Plan 订阅服务全新上架，现支持 Tencent HY 2.0 Instruct、GLM-5、Kimi-K2.5、MiniMax-M2.5 等多个最新模型，更多模型持续接入中，用户订阅后可自由切换模型。
>
> 首发支持使用 CodeBuddy、OpenClaw、Claude Code、Cline、Cursor 等主流编程工具，更多工具持续接入中。
>
> 新用户专享订阅特惠，Lite 套餐首月超值来袭低至 **7.9 元 / 月，立享 18000 次 请求**，Pro 套餐仅需 **39.9 元 / 月，畅享 90000 次 请求**。
>
> Coding Plan 新客限量优惠活动，**每天上午 10 点开始，24 点结束**，库存有限，先到先得。售罄即切换官网刊例价：**Lite 套餐 40 元 / 月、Pro 套餐 200 元 / 月**，按需选购更省心。

## 数据点

| 字段 | 值 | 备注 |
|---|---|---|
| 套餐 Lite 月费（首购首月） | 7.9 元 | 新客限量，每天 10:00-24:00 |
| 套餐 Lite 月费（首次续费） | **20 元** | 5 折续费（2026-08-04 截图证实） |
| 套餐 Lite 月费（刊例价） | 40 元 | 售罄后切换 / 第二次续费起恢复 |
| 套餐 Lite 5h 限额 | **1200 次/5 小时** | 滚动恢复（2026-08-04 截图证实） |
| 套餐 Lite 周限额 | **9000 次/周** | 周一 00:00 UTC+8 重置（2026-08-04 截图证实） |
| 套餐 Lite 月限额 | 18000 次/月 | 首月特惠赠送请求数 |
| 套餐 Pro 月费（首购首月） | 39.9 元 | 新客限量 |
| 套餐 Pro 月费（首次续费） | **100 元** | 5 折续费（2026-08-04 截图证实） |
| 套餐 Pro 月费（刊例价） | 200 元 | 售罄后切换 / 第二次续费起恢复 |
| 套餐 Pro 5h 限额 | **6000 次/5 小时** | 滚动恢复（2026-08-04 截图证实） |
| 套餐 Pro 周限额 | **45000 次/周** | 周一 00:00 UTC+8 重置（2026-08-04 截图证实） |
| 套餐 Pro 月限额 | 90000 次/月 | 首月特惠赠送请求数 |
| 上架日期 | 2026-03-12 | 文章发布时间 |
| 支持模型 | Tencent HY 2.0 Instruct, GLM-5, Kimi-K2.5, MiniMax-M2.5 | 用户可自由切换 |
| 支持工具 | CodeBuddy, OpenClaw, Claude Code, Cline, Cursor | 首发工具 |
| 新客特惠时段 | 每天 10:00-24:00 | 限量抢购 |

## 二次验证

- [x] chrome --dump-dom 抓取原文 (505 KB HTML, 6813 chars 提取文本)
- [x] chrome --screenshot 全屏截图 (540 KB PNG)
- [x] **用户控制台高清截图 2026-08-04**（图片源：`C:\Users\520hh\.claude\image-cache\47ff13b8-7adc-469c-a6d7-61cad32f402b\1.png`，已转存到 `2026-08-04_coding_plan_pricing_detail.png`）— 揭示了 Lite/Pro 套餐卡的完整定价结构（首购首月 + 首次续费 + 5h/周/月限额）
- [x] 与混元生文计费概述 (`document/product/1729/97731`) 一致：腾讯云官方域名一致、模型列表一致
- [x] 与 Token Plan 文章 (`developer/article/2675766`) 一致：Token Plan 单独定价,跟 Coding Plan 是两条独立产品线

## 不确定 / 存疑

1. ~~**5h 限额、weekly 限额**:Coding Plan 文章原文**只给出月度总请求数(18000/90000 次)**,**未明确给出 5h 滑动窗口限额和 weekly 限额**。二手资料(CSDN/blog)提到 5h 1200/6000、weekly 9000/45000,但**未在腾讯云官方页面验证到**~~ — **2026-08-04 解决**：用户控制台高清截图证实 5h 1200/6000、周 9000/45000、月 18000/90000 全部正确，已写入 yml。
2. **首次续费后是否继续折扣**：图片只显示"首购首月 + 首次续费"2 阶段，未说第 2 次续费及之后的价格。默认第 2 次续费起 = 刊例价（¥40 / ¥200）。
3. **是否双套餐并存**:文章说 Coding Plan 和 Token Plan 独立,但同一账号是否可同时购买需进一步核对官方文档。
4. **新客特惠名额库存**:文章说"库存有限,先到先得",但具体名额数未公布。

## 关联引用

- vendor: data/tencent/vendor.yml (待建)
- plan: data/tencent/plans/tencent-coding-lite.yml (待建)
- plan: data/tencent/plans/tencent-coding-pro.yml (待建)
- 截图: data/tencent/official/2026-08-04_coding_plan_intro_screenshot.png