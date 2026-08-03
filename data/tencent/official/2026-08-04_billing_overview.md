---
evidence_id: e_2026_08_04_tencent_hunyuan_billing
vendor_id: tencent
captured_at: 2026-08-04
captured_by: claude
source_url: https://cloud.tencent.com/document/product/1729/97731
capture_method: chrome-dump-dom
data_status: vendor_official
credibility: high
file_path: data/tencent/official/2026-08-04_billing_overview.md
related_plans: []
---

# 腾讯混元大模型 混元生文计费概述 (官方文档)

## 原文摘录

> 注意： 为进一步提升大模型服务体验，腾讯混元大模型相关功能将逐步迁移至 **TokenHub**。迁移后，原平台将不再新增模型能力，并停止支持新购模型服务。用户已购买的模型服务可继续使用，暂不受影响。如需开通新的模型服务或使用更多模型能力，请前往 TokenHub。

### 计费方式

> 腾讯混元大模型提供 API 接入方式，采用**后付费日结和预付费**的计费模式。

### 免费额度（首次开通）

| 产品名 | 免费额度 |
|---|---|
| Hunyuan-a13b | 共 100 万 tokens，共享消耗，1 年有效 |
| Hunyuan-embedding | 100 万 tokens，1 年有效 |

### 混元生文价格说明（按 token 后付费）

| 产品名 | 刊例价（每 百万 tokens） |
|---|---|
| Hunyuan-a13b | 输入：0.5 元 / 输出：2 元 |
| Hunyuan-role-latest | 输入：2.4 元 / 输出：9.6 元 |
| Hunyuan-translation | 输入：1.2 元 / 输出：3.6 元 |
| Hunyuan-translation-lite | 输入：1 元 / 输出：3 元 |
| Tencent HY Vision 1.5 Instruct | 输入：3 元 / 输出：9 元 |
| Hunyuan-turbos-vision | 输入：3 元 / 输出：9 元 |
| Hunyuan-t1-vision | 输入：3 元 / 输出：9 元 |
| Hunyuan-turbos-vision-video | 输入：3 元 / 输出：9 元 |
| Hunyuan-embedding | 输入：0.7 元 / 输出：0.7 元 |
| 腾讯元器 | 输入：100 元 / 输出：100 元 |

> 默认情况下，免费资源包耗尽或到期后**不会**自动转入后付费。如需使用后付费模式结算，请前往腾讯混元大模型控制台 > 设置 > 后付费设置开通后付费。

### 结算顺序

> 混元生文结算顺序为：**赠送的免费资源包 > 付费资源包 > 后付费**。

## 数据点

| 字段 | 值 | 备注 |
|---|---|---|
| 计费模式 | 后付费日结 / 预付费资源包 | 两种模式 |
| Hunyuan-a13b 输入价 | 0.5 元/百万 tokens | 混元主力模型 |
| Hunyuan-a13b 输出价 | 2 元/百万 tokens | 4× input |
| Hunyuan-role-latest 输入价 | 2.4 元/百万 tokens | 角色对话模型 |
| Hunyuan-role-latest 输出价 | 9.6 元/百万 tokens | 4× input |
| 平台迁移状态 | 迁移至 TokenHub | 2026-06-26 文档更新日 |

## 二次验证

- [x] chrome --dump-dom 抓取 (659 KB HTML, 7442 chars 文本)
- [x] chrome --screenshot 全屏截图 (321 KB PNG)
- [x] 与 Coding Plan intro 一致：腾讯混元 = 腾讯云官方产品 (Tencent HY = Hunyuan)
- [x] 价格单位自洽性验算：Hunyuan-a13b 输入 0.5 元/百万 tokens, 输出 2 元/百万 tokens, 输出/输入比 = 4× 合理

## 不确定 / 存疑

1. **迁移至 TokenHub 后是否还显示这套价目表**：文档明确说"原平台将不再新增模型能力"——当前是历史档,新购需走 TokenHub。
2. **最新模型(Hy3 preview)定价不在此页**：最新旗舰 Hy3 preview 不在这份生文价目表,定价走 TokenHub。

## 关联引用

- vendor: data/tencent/vendor.yml (待建)
- 截图: data/tencent/official/2026-08-04_billing_overview_screenshot.png