# Z.AI DevPack — GLM-5.3-Flash 抵扣系数（2026-08-28）

## 来源
- URL: https://docs.z.ai/devpack/
- 抓取方式: Chrome headless `--dump-dom`（2026-08-28）
- 同时通过 WebFetch + dump-dom 双重验证（铁律 21.2 / SOP §0.6）

## 原文（"Supported Models" 段）
> "All plans support GLM-5.3, GLM-5.3-Flash."

> "Requests for GLM-5.2/GLM-5.1 will be automatically routed to GLM-5.3, requests for GLM-4.7 will automatically be routed to GLM-5.3-Flash."

含义：
- Lite/Pro/Max **全套餐**支持 GLM-5.3 + GLM-5.3-Flash（不再分套餐限制）
- GLM-5.2/GLM-5.1 老请求**自动路由**到 GLM-5.3（不报错）
- GLM-4.7 老请求**自动路由**到 GLM-5.3-Flash（不报错）

## GLM-5.3-Flash 抵扣系数（HTML tr 抓取）

直接抓 devpack HTML tr（Input / Cached / Output 3 列）：

```
GLM-5.3-Flash   2.3   0.56   8
```

每 10000 tokens 抵扣系数：
- **Input** = 2.3 credits / 10000 tokens
- **Cached** = 0.56 credits / 10000 tokens
- **Output** = 8 credits / 10000 tokens

## 反推 tokens 公式（铁律 9 反推合法化）

编程场景 cache 命中率 90.9%（官方）+ 实测 token 比例 input 4.4% / cached 90.9% / output 0.6%：

```
avg_credit_per_token = (0.044 × 2.3 + 0.909 × 0.56 + 0.006 × 8) / 10000
                     = (0.1012 + 0.5090 + 0.048) / 10000
                     = 0.00006582 credits/token
                     = 65.82 credits / 1M tokens
```

→ **1 credit ≈ 15,194 tokens** （平均）
→ **1M tokens ≈ 65.82 credits**

## z.ai Coding Plan 各套餐 GLM-5.3-Flash 跑量反推

| 套餐 | 5h credits | 5h tokens | 周 credits | 周 tokens | 月（周×4.3）|
|---|---|---|---|---|---|
| **Lite** | 2,000 | 30.4M | 10,000 | 151.9M | 653.2M |
| **Pro** | 12,000 | 182.3M | 60,000 | 911.5M | 3.92B |
| **Max** | 56,000 | 850.8M | 280,000 | 4.25B | 18.29B |

## 与 z.ai devpack GLM-5.2 估算对比

| 套餐 | GLM-5.2 周估算（官方） | GLM-5.3-Flash 周反推 | 倍数 |
|---|---|---|---|
| Lite | 0.43-0.87亿 = 43-87M | 151.9M | **1.7-3.5×** |
| Pro | 2.63-5.26亿 = 263-526M | 911.5M | **1.7-3.5×** |
| Max | 6.13-12.26亿 = 613-1226M | 4,253.8M | **3.5-7×** |

GLM-5.3-Flash 因抵扣系数低（5.2 = 6.9/1.7/24 vs 5.3-Flash = 2.3/0.56/8），**同样 credits 跑更多 tokens**。

## ⚠ 重要边界

1. **反推值 = 全非高峰 + 90.9% cache 命中**的理论上限
   - 高峰期（工作日 14:00-18:00 UTC+8）基础 1.0× → 抵扣不打折
   - 用户实际跑：高峰期混合跑只到下限
   - **不**写进 yml 的 `tokens_measured`（那是实测字段，铁律 9）
   - 写进 `window_*_tokens` 是「**反推**」**反推合法化**——已在 yml notes 注明公式 + 数据来源

2. **z.ai docs 表面展示 GLM-5.3-Flash 促销半价 $0.075/$0.015/$0.25 至 2026-09-09**
   - 这是按量 API 单价，**不**与 Coding Plan 套餐积分互通
   - Coding Plan 是**积分制**（credits），跟按量 API 计价体系分离
   - yml 用 Coding Plan 积分反推（套餐口径），不是按量 API 单价

3. **GLM-5.3-Flash 与 GLM-5.3 性能/能力差异**
   - devpack 原文未明示 Flash 与非 Flash 的能力差异
   - 推测 Flash = 更快 + 更便宜（系数 1/3），但牺牲部分能力
   - 能力分数需等 LMArena 或第三方 benchmark 更新（铁律 15 暂留 null）

## 证据文件路径
- data/zai/official/2026-08-28_zai_devpack_glm53flash.md（本文件）
- 抓取 HTML: .scratch/zai_devpack_2026-08-28.html（不入仓）
- 已有 evidence: data/zai/official/2026-08-28_zai_pricing_glm53flash.md（按量 API 价）
- 已有 evidence: data/zai/official/2026-08-28_zai_devpack_credits_glm53.md（5h/周 credits 复核）