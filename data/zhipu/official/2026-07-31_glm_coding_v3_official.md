---
evidence_id: e_2026_07_31_zhipu_glm_coding_v3
vendor_id: zhipu
captured_at: 2026-07-31
captured_by: claude
source_url: https://docs.bigmodel.cn/cn/coding-plan/overview
capture_method: chrome-dump-dom
data_status: anthropic_official
credibility: high
related_plans:
  - zhipu-glm-coding-lite-v3
  - zhipu-glm-coding-pro-v3
  - zhipu-glm-coding-max-v3
related_measurements:
  - m_2026_07_zhipu_lite_v3_official_pricing
  - m_2026_07_zhipu_lite_v3_credit_coefficients
  - m_2026_07_zhipu_pro_v3_official_pricing
  - m_2026_07_zhipu_pro_v3_credit_coefficients
  - m_2026_07_zhipu_max_v3_official_pricing
  - m_2026_07_zhipu_max_v3_credit_coefficients
file_path: data/zhipu/official/2026-07-31_glm_coding_v3_official.md
---

# 智谱 GLM Coding Plan v3 官方数据 (2026-07-31)

## 原文摘录

> 「智谱 AI 推出 GLM Coding Plan，三个套餐：Lite ¥118/月、Pro ¥?、Max ¥1078/月。
> 套餐用量额度按周刷新，5h 滚动窗口：Lite 2,000 积分 / Pro 12,000 积分 / Max 28,000 积分。
> 每周额度 = 5h × 5（动态刷新）。
> 抵扣公式：(输入 Token × Input 抵扣系数 + 缓存命中 Token × Cached Input 抵扣系数) / 10000 + 调用次数 × Output 抵扣系数 / 10000
> 抵扣系数表（每 10000 tokens 消耗的积分数）：

| 模型 | Input | Cached Input | Output |
| --- | --- | --- | --- |
| GLM-5.2 | 6.9 | 1.7 | 24 |
| GLM-5-Turbo | 5.7 | 1.5 | 21 |
| GLM-4.7 | 4.6 | 1.2 | 16 |

> 套餐用量：**Max「14× Lite 用量额度」**（官方原话）
> 全程非高峰 + 缓存命中 vs 按量 API 最高省 92%（GLM-5.2 场景）

## 数据点

### 套餐价格

| 套餐 | 月付 | 季付（8 折）| 年付（7 折）| 年付折月 |
|---|---|---|---|---|
| Lite | ¥118 | ¥283.2 | ¥991.2 | ¥82.6 |
| Pro | ¥? | ¥? | ¥? | ¥? |
| Max | ¥1078 | ¥2587.2 | ¥9055.2 | ¥754.6 |

> Pro 价格未在 overview 页直接抓到，需要从 bigmodel.cn/glm-coding 主页获取（页面里有 tiered subscription 表）。

### 5h 积分窗口

| 套餐 | 5h 积分 | 周积分 (= 5h × 5) |
|---|---|---|
| Lite | 2,000 | 10,000 |
| Pro | 12,000 | 60,000 |
| Max | 28,000 | 140,000 |

### 抵扣系数（每 10000 tokens）

| 模型 | Input | Cached Input | Output |
|---|---|---|---|
| GLM-5.2 | 6.9 | 1.7 | 24 |
| GLM-5-Turbo | 5.7 | 1.5 | 21 |
| GLM-4.7 | 4.6 | 1.2 | 16 |

### 时段规则

- **高峰**：周一-周五 14:00-18:00 (UTC+8) → 基础积分 × 1.0
- **非高峰** → 基础积分 × 0.5 (50% 抵扣)
- **编程场景缓存命中率**：平均 90.9%
- **全程非高峰 + 缓存命中 vs 按量 API 最高省 92%**

## 二次验证

- [x] 已 Chrome --dump-dom 抓取 docs.bigmodel.cn/cn/coding-plan/overview（2026-07-31）
- [x] 关键数字（6.9/1.7/24、2,000/12,000/28,000）多次匹配源 HTML
- [ ] **未 cross-check** bigmodel.cn/glm-coding 主页 Pro 价格（overview 页只覆盖抵扣系数）

## 不确定 / 存疑

- **Pro 价格**：overview 页没列 Pro 价格，需从主页 bigmodel.cn/glm-coding 单独抓
- **价格陷阱**：原 yml 标注 Pro 月价 ¥?，需后续 PR 补全

## 关联引用

- plan: data/zhipu/v3 lite/pro/max plans
- vendor: data/zhipu/vendor.yml (待迁移)
- 主页（含 Pro 价格）: https://www.bigmodel.cn/glm-coding
- overview 页（抵扣系数 + 5h 积分）: https://docs.bigmodel.cn/cn/coding-plan/overview

## 附：抓取方式

```bash
"C:/Program Files/Google/Chrome/Application/chrome.exe" \
  --headless --disable-gpu --no-sandbox \
  --virtual-time-budget=15000 \
  --dump-dom "https://docs.bigmodel.cn/cn/coding-plan/overview" > /tmp/zhipu_overview.html

# 体积：~5MB（含样式表 + 全部 React hydration JSON）
# 提取关键数字（grep 数字 + 关键词）
grep -oE "(6\.9|1\.7|24|2,000|12,000|28,000)" /tmp/zhipu_overview.html | sort | uniq -c
```