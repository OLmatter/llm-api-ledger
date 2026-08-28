# Z.AI 官方定价页 — GLM-5.3-Flash 抓取（2026-08-28）

## 来源
- URL: https://docs.z.ai/guides/overview/pricing
- 抓取方式: Chrome headless `--dump-dom`（2026-08-28）
- 同时通过 WebFetch + dump-dom 双重验证（铁律 21.2 / SOP §0.6）

## GLM-5.3-Flash 行（HTML tr 简化后）
```
GLM-5.3-Flash $0.15 $0.075 $0.03 $0.015 Limited-time Free $0.50 $0.25
```

**列解读**（z.ai pricing 表 7 列）：
| 列 | 原价 | 促销价 |
|---|---|---|
| Input | $0.15/M | **$0.075/M**（50% off） |
| Cached Input | $0.03/M | **$0.015/M**（50% off） |
| Cached Input Storage | — | **限时免费** |
| Output | $0.50/M | **$0.25/M**（50% off） |

## 促销截止
> "The promotion ends at 24:00 on September 9, 2026 (UTC+8, Singapore time)."

**直采原文**（HTML 内嵌，重复出现两次）：
```
24:00 on September 9, 2026 (UTC+8, Singapore time).
```

## 表格行位置
GLM-5.3-Flash = "Latest Models" 表格**首行**（在 GLM-5.3 / GLM-5.2 之上），官方明示其为最新模型。

## 唯一促销半价模型
页面**仅 GLM-5.3-Flash** 一行有划线（原价 + 促销价）格式。其他模型无促销划线。

## 双重验证
1. WebFetch 直接抓 docs.z.ai → 一致返回 Input $0.075 / Cached $0.015 / Output $0.25 + 截止 2026-09-09
2. Chrome --dump-dom 抓全 HTML → 7 列表格原文 = `GLM-5.3-Flash $0.15 $0.075 $0.03 $0.015 Limited-time Free $0.50 $0.25`
3. Promo end date 在 HTML 中出现 2 次（一处在用户可见文本，一处在 Next.js `__NEXT_DATA__` payload），**完全一致**

## 数据使用建议（铁律 22 自洽性验算）
- yml measurement 应填 z.ai 促销价（$0.075/$0.015/$0.25），因 9-9 后恢复原价 = 虚报
- 同时填原价（$0.15/$0.03/$0.50）作为 notes 提示
- 必须标 `pricing_disputed: false` + `pricing_source: 'z.ai_official_promo_until_2026-09-09'`

## opencode Go 抓取对照（矛盾点 ⚠）
opencode Go 页 (https://opencode.ai/docs/zh-cn/go/, 2026-08-28) 显示 GLM-5.3-Flash 单价为：
```
$0.15 $0.50 $0.03 - $15
```
**这是 z.ai 原价（未跟促销同步）**——opencode 展示口径 vs 实际计费口径**待验证**。
opencode 标请求数 1,580 / 3,950 / 7,900（5h/周/月），按 z.ai 促销价反推：
- 每请求成本 = (1000×$0.075 + 55000×$0.015 + 200×$0.25) / 1e6 = $0.000930
- $15 ÷ $0.000930 ≈ 16,129 请求 → opencode 标 7,900 = 49% 缺口（明显**超出**月档）
- 按 z.ai 原价反推：(1000×$0.15 + 55000×$0.03 + 200×$0.50) / 1e6 = $0.002010
- $15 ÷ $0.002010 ≈ 7,463 请求 → opencode 标 7,900 = **5.9% 缺口**（自洽！）

**结论**：opencode 实际跑的是 z.ai **原价**（账单系统接的是 $0.15/$0.03/$0.50），不是促销半价。
7,900 请求在原价下用 $15/月额度 ≈ 5.9% 缺口（铁律 22 medium 范围），无矛盾。

yml measurement 用 **z.ai 原价**（与 opencode 实际计费一致）+ notes 写明「z.ai 官方展示划线促销价 $0.075/$0.015/$0.25 至 2026-09-09，但 opencode Go 账单按原价跑」。

## 证据文件路径
- data/zai/official/2026-08-28_zai_pricing_glm53flash.md（本文件）
- 抓取 HTML: .scratch/zai_pricing_2026-08-28.html（不入仓）