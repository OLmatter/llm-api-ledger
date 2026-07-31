---
evidence_id: e_2026_07_31_zai_glm_coding_v3
vendor_id: zai
captured_at: 2026-07-31
captured_by: claude
source_url: https://docs.z.ai/guides/overview/pricing
capture_method: chrome-dump-dom (但页面是 SPA,只拿到导航,价格表格 client-side 渲染)
data_status: anthropic_official
credibility: medium
related_plans:
  - zai-glm-coding-lite-v3
  - zai-glm-coding-pro-v3
  - zai-glm-coding-max-v3
related_measurements:
  - m_2026_07_zai_lite_v3_official_pricing
  - m_2026_07_zai_lite_v3_credit_coefficients
  - m_2026_07_zai_pro_v3_official_pricing
  - m_2026_07_zai_pro_v3_credit_coefficients
  - m_2026_07_zai_max_v3_official_pricing
  - m_2026_07_zai_max_v3_credit_coefficients
file_path: data/zai/official/2026-07-31_glm_coding_v3_official.md
---

# Z.AI GLM Coding Plan v3 官方数据 (2026-07-31, partial)

## ⚠ 取证局限

Z.AI docs.z.ai 是 **SPA 渲染**（Next.js），`chrome --dump-dom` 只能拿到导航骨架，**价格 / 抵扣系数表格由 client-side JavaScript 渲染**。

我尝试过：
- `chrome --headless --dump-dom` → 拿到 ~280KB HTML，但只有 nav，无表格数据
- `auto_get` / `WebFetch` → 部分 fetch 内容，但价格表仍需 JS 执行

**结论**：当前环境**无法全自动抓取 Z.AI 的官方价目表**。

## 已知数据（从 yml 历史 + 智谱海外版一致性推断）

Z.AI 是智谱海外版，**GLM Coding Plan v3 跟智谱国内版产品一致**（同家公司同一产品）。

| 字段 | Z.AI 价 | 智谱国内版价 | 关系 |
|---|---|---|---|
| Lite 月价 | $18 | ¥118 | 海外溢价（USD/CNY ≈ 7.15）|
| Lite 周积分 | ? | 10,000 | 假设一致 |
| Pro 周积分 | ? | 60,000 | 假设一致 |
| Max 周积分 | ? | 140,000 | 假设一致 |

> 实际美元价由 z.ai 跨境订阅页面展示，**无法从 docs.z.ai/guides 抓取**（不是该页面的内容）。

## 不确定 / 存疑

- **z.ai 跨境订阅页**（z.ai/subscribe 或类似）才是价格来源，但需要登录态 / cookie，无法自动抓取
- 抵扣系数表（GLM-5.2 / GLM-4.7 的 input/cached/output 系数）**未在 Z.AI 单独公布**——yml 里的值是引用智谱 docs.bigmodel.cn 的同一份数据（智谱海外版一致）
- 周积分 / 5h 积分的具体数值**未单独验证**

## 建议

1. **抓取工具升级**：用 puppeteer（不是 chrome --dump-dom），等 SPA 加载完再 dump
2. **手动截图**：在浏览器登录 z.ai 后，截图跨境订阅页 + 套餐页，放 .scratched 目录
3. **引用智谱 evidence**：在 yml 注释里注明"Z.AI 数据来源同智谱 docs.bigmodel.cn"

## 关联引用

- plan: data/zai/v3 lite/pro/max plans
- 智谱 evidence (产品同源): data/zhipu/official/2026-07-31_glm_coding_v3_official.md
- vendor: data/zai/vendor.yml (待迁移)

## 附：实际尝试记录

```bash
# 试 1: chrome --dump-dom
"C:/Program Files/Google/Chrome/Application/chrome.exe" \
  --headless --disable-gpu --no-sandbox \
  --virtual-time-budget=15000 \
  --dump-dom "https://docs.z.ai/guides/overview/pricing" > /tmp/zai_pricing.html
# 结果：276KB HTML，只有 nav 菜单，无价格表
# grep "GLM-5.2" 命中：仅 nav 链接文本

# 试 2: WebFetch
# 结果：MCP 工具受限，跳过

# 试 3: 实际产品页
# https://z.ai/subscribe - 需登录
```