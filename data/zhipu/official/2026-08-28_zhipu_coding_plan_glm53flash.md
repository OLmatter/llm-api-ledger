# Zhipu 国内版 Coding Plan — GLM-5.3-Flash 抵扣系数（2026-08-28）

## 来源
- URL: https://docs.bigmodel.cn/cn/coding-plan/overview
- 抓取方式: Chrome headless `--dump-dom`（2026-08-28）
- 同时通过 WebFetch + dump-dom 双重验证（铁律 21.2 / SOP §0.6）

## 原文（"Supported Models" 段）
> "套餐 GLM-5.3-Flash（含视觉理解 MCP）"

> "调用历史模型 GLM-5.2、GLM-5.1 都将自动切换至 GLM-5.3，调用 GLM-5-Turbo、GLM-4.7 将自动切换至 GLM-5.3-Flash。"

含义：
- Lite/Pro/Max **全套餐**支持 GLM-5.3 + GLM-5.3-Flash（含视觉理解 MCP）
- GLM-5.2/GLM-5.1 老请求**自动路由**到 GLM-5.3
- GLM-5-Turbo/GLM-4.7 老请求**自动路由**到 GLM-5.3-Flash

## GLM-5.3-Flash 抵扣系数（HTML tr 抓取）

```
GLM-5.3-Flash   2.3   0.56   8
```

每 10000 tokens 抵扣系数：
- **Input** = 2.3 credits / 10000 tokens
- **Cached** = 0.56 credits / 10000 tokens
- **Output** = 8 credits / 10000 tokens

## zhipu Coding Plan 各套餐 5h/周 credits

| 套餐 | 5h credits | 周 credits | 来源 |
|---|---|---|---|
| **Lite** | 2,000 | 10,000 | 2026-08-28 docs.bigmodel.cn 直核 |
| **Pro** | 12,000 | 60,000 | 2026-08-28 docs.bigmodel.cn 直核 |
| **Max** | 28,000 | 140,000 | 2026-08-28 docs.bigmodel.cn 直核 |

## 反推公式（铁律 9 反推合法化）

编程场景 cache 命中率 90.9%（官方）+ 实测 token 比例 input 4.4% / cached 90.9% / output 0.6%：

```
avg_credit_per_token = (0.044 × 2.3 + 0.909 × 0.56 + 0.006 × 8) / 10000
                     = 0.00006582 credits/token
                     = 65.82 credits / 1M tokens
```

## 各套餐 GLM-5.3-Flash 跑量反推

| 套餐 | 5h tokens | 周 tokens | 月（周×4.3）|
|---|---|---|---|
| **Lite** | 30.4M | 151.9M | 653.2M |
| **Pro** | 182.3M | 911.5M | 3.92B |
| **Max** | 425.4M | 2.13B | 9.15B |

## 与 z.ai 国际版一致性验证

智谱是 z.ai 母公司，同一套 Coding Plan 产品（中文站 vs 英文站）：

| 维度 | z.ai 国际版 | zhipu 国内版 | 一致? |
|---|---|---|---|
| 抵扣系数 Input | 2.3 | 2.3 | ✅ |
| 抵扣系数 Cached | 0.56 | 0.56 | ✅ |
| 抵扣系数 Output | 8 | 8 | ✅ |
| Lite 5h/周 credits | 2000/10000 | 2000/10000 | ✅ |
| Pro 5h/周 credits | 12000/60000 | 12000/60000 | ✅ |
| Max 5h/周 credits | 28000/140000 | 28000/140000 | ✅ |

**6/6 项完全一致**。反推值两边通用。

## ⚠ 重要边界

1. **反推值 = 全非高峰 + 90.9% cache 命中**的理论上限
   - 高峰期（工作日 14:00-18:00 UTC+8）基础 1.0× → 抵扣不打折
   - **不**写进 yml 的 `tokens_measured`（铁律 9 那是实测）
   - 写进 `window_*_tokens` 是「反推」，已在 yml notes 注明公式

2. **GLM-5.3-Flash 与 GLM-5.3 性能差异**
   - 智谱官方未明示 Flash 与非 Flash 的能力差异
   - 推测 Flash = 更快 + 更便宜，能力略弱（系数 1/3 vs 6.9/1.7/24）
   - 能力分数需等 LMArena 或第三方 benchmark 更新（铁律 15 暂留 null）

## 证据文件路径
- data/zhipu/official/2026-08-28_zhipu_coding_plan_glm53flash.md（本文件）
- 抓取 HTML: .scratch/zhipu_coding_plan_2026-08-28.html（不入仓）
- 已有 evidence: data/zhipu/official/2026-07-31_glm_coding_v3_official.md（v3 原始抓取）
- 已有 evidence: data/zhipu/official/2026-08-28_glm53_full_rollout.md（GLM-5.3 全量上线）