---
name: ledger-data-discipline
description: 改 llm-api-ledger 项目的套餐/厂商数据前必读。触发条件：修改 data/plans/*.yml 或 data/vendors/*.yml、跑 scripts/build-plans.mjs、用户说"加套餐 / 加厂商 / 改价格 / 改用量 / 改邀请码 / 改 ZCode / 改 DS 等价 / 改排序"。本 skill 收录 16 条铁律（每条配历史踩坑案例），违反任一条必返工。
---

# Ledger 数据纪律（改数据前必读）

> **强制触发**：任何对 `data/plans/*.yml`、`data/vendors/*.yml`、`scripts/build-plans.mjs`、`LeaderBoard.vue` 排序逻辑的修改前，必须读完本文件。
>
> 这 16 条铁律每一条都来自**实际踩过的坑**——不是理论规范，是事故总结。违反任一条 = 用户发现数据错 = 榜单公信力掉。
>
> **连续违反 2 条立刻停下来读 NPL 记忆**（root.project 下 ledger 相关 task），不准继续凭印象改。

---

## 0. 心智模型（先理解再改）

榜单要回答的是：**"某套餐在真实开发者使用下能交付多少？"**

为了这个目标，数据有三层：

```
┌─────────────────────────────────────────────────┐
│  实测层（最硬）   tokens_measured  ← 探针反推  │
│  宣称层（参考）   tokens_official_claimed       │
│                  requests_official  ← 厂商公布  │
│  推导层（兜底）   tier_ratio / window_ratio 反推 │
└─────────────────────────────────────────────────┘
```

**三类价格不可混**（这是用户反复强调的最重要规则）：

| 类别 | 中文 | 字段前缀 | 谁能享受 | 例子 |
|---|---|---|---|---|
| **pricing** | 定价 / 刊例价 | `original_*` / `base_*` | 所有人 | 火山 Pro ¥200/月 |
| **discount** | 优惠 / 少付钱 | `intro_*` / `affiliate.discount` | 特定人群（首单/受邀） | 首单 ¥49.9、邀请码 95折 |
| **boost** | 加成 / 多跑量 | `rate_multipliers` / `zcode_*` | 特定客户端（ZCode） | ZCode ×1.5 等效额度 |

**discount 和 boost 是两个独立维度，可叠加**：
- 邀请码 95折（discount）+ ZCode ×1.5（boost）= 用户少付钱 + 多跑量，**同时享受**

---

## 1. 16 条铁律

### 铁律 1：pricing / discount / boost 严禁混用字段

**事故**：早期把 ZCode ×1.5 当成"首单 9 折"处理，写成 discount。

**规则**：
- 定价（所有人付的钱）→ `pricing.original_*` 或 `pricing.base_*`
- 优惠（特定人少付钱）→ `pricing.intro_*`（首单）或 `affiliate.discount`（邀请码）
- 加成（特定客户端多跑量）→ `vendor.rate_multipliers` 或 build 时算 `tokens.zcode_*`

**自检**：写之前问自己——这个值影响"付的钱"还是"跑的量"？前者是 discount，后者是 boost。

---

### 铁律 2：ZCode ×1.5 是 boost，不是 discount

**事故**：把 ZCode 1.5x 等同于"首单 9 折"。

**规则**：
- ZCode 1.5x = 额度加成（boost）：跑相同 tokens 只扣 0.67 额度，等效多跑 1.5×
- 邀请码 95折 = 价格折扣（discount）：付的钱 ×0.95
- 两者**独立可叠加**，不能合并成单一字段
- build 输出时：`tokens.zcode_*` 独立成行，不污染 `tokens.monthly`

**ZCode 计算公式**（智谱官方）：
- 非高峰期：扣费系数 1.0 → 0.67（=1/1.5）
- 高峰期 14:00-18:00：扣费系数 3.0 → 2.0
- 全程非高峰假设下：等效额度 × 1.5

**适用范围**：仅 `zhipu` 和 `zai` 两家厂商，其他厂商写 ZCode 字段 = bug。

---

### 铁律 3：B / 亿 / M / K 单位不混用，YAML 写完整数字

**事故**：把 MiniMax 月度 18亿 写成 `18000000000`（18B），实际应该是 `1800000000`（1.8B = 18亿）。

**规则**：
| 符号 | 含义 | 等于 |
|---|---|---|
| M | 百万 | 1,000,000 |
| B | 十亿 | 1,000,000,000 |
| 亿 | 一亿 | 100,000,000 |
| K | 千 | 1,000 |

**YAML 必须写完整数字，禁止用字符串单位**：
```yaml
# ❌ 错
tokens_measured: 18B
tokens_measured: "1.8B"

# ✅ 对
tokens_measured: 1800000000   # 1.8B = 18亿
```

**自检**：YAML 写完后心算一遍——18 亿应该是几个零？1+8+0...0（8 个零）= `180000000`。错，亿是 8 个零但前面有 18，所以是 `1_8000_0000` = `180000000`（8 个零）= 18亿 = 1.8B。

**口诀**：亿 = 8 个零，B = 9 个零。

---

### 铁律 4：MiniMax / Kimi 不公布次数，claimed 用 tokens

**事故**：把 MiniMax 月度写成"宣称用量（次）"——但 MiniMax 根本不公布请求次数。

**规则**：
- **次数**（requests）：仅 `volcengine`、`zhipu`、`zai` 公布，填 `requests_official`
- **tokens**：`minimax`、`kimi` 公布的是 token 总量，填 `tokens_official_claimed`
- build-plans.mjs 第 321-340 行硬编码了这条规则：
  ```javascript
  const isTokenVendor = p.vendor === 'minimax' || p.vendor === 'kimi'
  ```
- **不准给 MiniMax/Kimi 加 requests_official 字段**

---

### 铁律 5：cache_read 不是 output，是 input 同类

**事故**：MiniMax 烧表"全是输入"被当成"纯 input 测试"——但 cache_read 其实是"读缓存命中"，按 input 价计费（¥0.02/M 几乎免费）。

**规则**：
- `cache_read` = 缓存命中读取 = 按 input 价的极低比例计费（DS V4 Flash ¥0.02/M）
- `input`（缓存未命中）= 完整 input 价
- `output` = 最贵（通常是 input 的 2-4 倍）

**真实编程 token 分布**（来源：用户 MiniMax 实测，已校准到 95% 缓存命中场景）：

| 类型 | 占比 |
|---|---|
| cache_read | 95% |
| input | 4.4% |
| output | 0.6% |

**不准把 cache_read 当 output 算钱**——会把成本估高 4 倍。

**方法论补充（2026-07-23 洞察）**：计费结构对实测数据的**放大效应**

三家价格差距极大（缓存命中 < 未命中 input < output，通常差 **10-50 倍**），意味着：

> **同样额度，不同使用模式（缓存命中率 / 输出占比）实测 token 数可以差数倍甚至数十倍。**

典型案例：Kimi Allegretto 2 个社区样本差距 2.1×（326M vs 690M），根因不是测量误差或用户撒谎，而是**K3 计费结构**决定——高缓存命中+少输出的用户能跑 690M，低缓存+多输出的只能跑 326M。

**对榜单的影响**：
- 单点 token 数据天然有放大不确定性，**必须标 disputed**（跟铁律 10 呼应）
- 未来理想方案：记录 measurement 时的「缓存命中率 + input/output 占比」，让数据可归一化对比
- 当前简化处理：median 多点 + 显式 disputed 标记，让用户知道"这个数字会因你的使用模式漂移"

---

### 铁律 6：月度 ≤ 周 × 5，超过 10× 一定是单位错

**事故**：MiniMax 月度 18B + 周度 1.45B = 12× 比例（不可能）。

**规则**：
- 厂商月/周比例通常 **4-5×**（一个月 ≈ 4.3 周）
- 火山是特例：月 = 2 × 周（官方硬封顶，月度比想象中小）
- **月 > 周 × 10 一定是单位错了**，立刻回头查 B/亿

**自检**：写完月度后算 `月 / 周`：
- 2-5× → 正常
- 6-10× → 警惕，看是不是限时活动或 estimate
- > 10× → **必错**，铁律 3 重查单位

---

### 铁律 7：邀请码统一 schema，6 字段不可缺

**事故**：各厂商邀请码字段名不统一，前端读起来乱。

**规则**（vendor.yml 里）：
```yaml
affiliate:
  code: NMJG4D6P                    # 邀请码字符串
  url: https://volcengine.com/...   # 邀请链接（带 source/折扣参数）
  discount: 0.95                     # 折扣系数（0.95 = 95折）
  stackable: true                    # 能否跟官方活动叠加
  expires: 2026-08-08                # 过期日（YYYY-MM-DD），过期前端自动隐藏
  owner: OLmatter                    # 归属（默认 OLmatter）
  added_at: 2026-07-21               # 加入日期
```

**无邀请码的厂商**（如智谱）：`affiliate: null`，**不要省略字段**。

**邀请码影响排序 = 公信力自杀**：铁律，没邀请码的套餐照样上榜，邀请码列只能少付钱不能影响 sort。

---

### 铁律 8：原价 vs 首单价两套字段

**事故**：早期把原价和首单价写在一起。

**规则**：
- `original_*`：刊例价（所有人付的钱，无任何优惠）
- `intro_*`：限时特惠价（首单/特定活动，仅新购首期）
- 两者**必须分字段**，前端根据需要展示

```yaml
# ✅ 对
pricing:
  original_monthly: 200         # 刊例价
  intro_monthly: 49.9           # 首单限时
  intro_duration_months: 2      # 首单持续 2 个月
  intro_condition: 新购 / 同主体仅一次
  intro_end_hint: 2026-08-08    # 活动截止日

# ❌ 错（混在一起）
pricing:
  monthly: 49.9  # 这是首单还是原价？前端怎么知道？
```

---

### 铁律 9：实测 vs 宣称 严格分栏

**事故**：MiniMax 把官方宣称 token（18 亿）当成探针实测填进 `tokens_measured`。

**规则**：
| 字段 | 来源 | 单位 | 可信度 |
|---|---|---|---|
| `requests_official` | 厂商公布 | 次 | 仅参考 |
| `tokens_official_claimed` | 厂商公布 | tokens | 仅参考 |
| `tokens_measured` | 探针反推 | tokens | high |
| `inferred_*` | tier/window 反推 | tokens | medium/low |

**实测字段留空 ≠ 0**：`tokens_measured: null` 表示"还没测"，前端展示 `—`。**不准填 0，不准填官方宣称值冒充实测**。

---

### 铁律 10：单样本必须标 disputed，多源聚合才能升级可信度

**事故**：另一个 AI 把 Kimi Allegretto 单点 690M 当高可信度展示。

**规则**：
- `credibility` 三级：`low`（单用户）/ `medium`（3+ 用户或 burn 测试）/ `high`（PR 验证）
- 单样本差距大（> 1.5×）必须标 `disputed: true` + 写 `dispute_note`
- 多源数据取 **median**（中位数），不准取 mean（极端值污染）

**Kimi Allegretto 案例**（教科书级）：
- 数据点 1：326M（95% 用量反推，较可信）
- 数据点 2：690M（早期单点采样，可能低利用率）
- 差距 2.1× → 标 `disputed: true`
- median = 508M（不是 mean 508M，巧合相同但方法不同）

---

### 铁律 11：限时活动必须有 expires，过期自动摘

**事故**：ZCode 7-31 到期后没人摘，UI 继续展示已失效的优惠。

**规则**：
- 任何限时活动（首单/邀请码/ZCode/年付特惠）必须填 `expires` 或 `intro_end_hint`
- build-plans.mjs 第 200-206 行：`expires` 过期 → 自动隐藏邀请码按钮
- **新增限时活动时立刻在 NPL 记一条**（slug 含日期），到期前主动 review

```yaml
# ✅ 有过期日
affiliate:
  expires: 2026-08-08

# ❌ 无过期日（永远有效的活动极少）
affiliate:
  expires: null   # 永久？必须确认
```

---

### 铁律 12：USD 套餐必须有 CNY 折算（防 USD/CNY 混淆回归）

**事故**：早期跨厂商价格排序直接拿 `original_monthly` 比较，Z.AI 是 USD 但没折算 → **$72 跟 ¥99 直接比**，排序全错。

**规则**：
- 所有 USD 套餐在 build 输出时必须有 `original_monthly_in_cny`（build-plans.mjs 第 292 行已自动生成）
- 排序用的 `priceFor()` 必须用 `original_monthly_cny ?? original_monthly ?? Infinity`，**不准直接拿 `original_monthly`**
- lint 铁律 12 强制检查：`currency=USD` 时 `original_monthly_in_cny` 不能为 null，`is_usd` 必须为 true

**自检**：改完排序逻辑后，检查 Z.AI 套餐（USD）排到的位置是不是按折算后的 ¥ 价排的，而不是按 $ 数值排的。

---

### 铁律 13：tier 排序用 tier_multiplier，不准用 tierRank 字典

**事故**：早期 tierRank 字典只写 `{ lite: 1, pro: 2, max: 3 }`，**不认 kimi 的 andante/moderato/allegretto/allegro，也不认 minimax 的 plus/ultra** → kimi 4 档套餐全落到 `|| 99`，同厂商内顺序变成按价格乱排。

**规则**：
- 所有 tier 排序（build 默认顺序 + 前端 vendor 排序）必须用 `tier_multiplier` 数字字段
- build 输出时 `tier_multiplier` 来自 `TIER_RATIOS[vendor][tier]`，所有套餐都必须有这个字段
- lint 铁律 13 强制检查：每个套餐 `tier_multiplier` 必须存在且 > 0
- **新增厂商时必须同步更新 `TIER_RATIOS`**，否则该厂商所有套餐 lint 报错

```javascript
// ❌ 错（tierRank 字典不全，新增厂商/档位就漏）
const tierRank = { lite: 1, pro: 2, max: 3 }
arr.sort((a, b) => (tierRank[a.plan_tier] || 99) - (tierRank[b.plan_tier] || 99))

// ✅ 对（用数字字段，所有厂商统一）
arr.sort((a, b) => (a.tier_multiplier ?? 99) - (b.tier_multiplier ?? 99))
```

---

### 铁律 14：排序按钮分两类——分组型 vs 跨厂商型

**用户明确要求**：点「价格/用量/性价比/可信度」时跨厂商排（不保分组），默认才是分组型。

**规则**：
| 排序键 | 类型 | 行为 |
|---|---|---|
| `vendor`（默认） | 分组型 | 厂商字母序 + tier_multiplier 升序，保留厂商分组视觉 |
| `price_asc` / `price_desc` | 跨厂商 | 跨厂商按 CNY 口径价格排 |
| `tokens` | 跨厂商 | 跨厂商按实测月度用量降序 |
| `value` | 跨厂商 | 跨厂商按「周用量 ÷ 月费」性价比降序 |
| `credibility` | 跨厂商 | 跨厂商按可信度降序 |

**跨厂商排时的视觉影响**：邀请码 rowspan 合并 + 厂商列合并会按新顺序重算（连续相同 vendor 才合并），用户预期是"看到全局对比"，不再追求"同厂商视觉连贯"。

**性价比公式**：`value = tokens.weekly / priceFor(plan)`，用 weekly 不用 monthly（Kimi 月度无限，weekly 才有可比性）。

---

### 铁律 15：能力排序（Chatbot Arena）数据采集纪律

**用户要求**：至少**现在就记录** Chatbot Arena 分数，为后续做"能力排序"做准备。

**当前障碍**（2026-07 调查）：
- LMArena 官方榜单（lmarena.ai/leaderboard）模型命名跟国内厂商不一致
- 我们榜单上的 GLM-5.2 / Kimi-K2.7 / MiniMax-M3 / DS-V4 Pro 这些**新版本**，LMArena 还停留在 K2.5 / K2-thinking / M2.1 / V3.2 等旧名
- 榜单表格很多行模型名是图片占位符，爬不全

**采集纪律**：
1. **每个厂商建 `data/vendors/<vendor>.yml` 加 `arena_score` 字段**（结构如下），数据缺失时 `null`
2. **数据来源必须标注**（LMArena / Artificial Analysis / SuperCLUE / 第三方 benchmark）
3. **采集日期必须记录**（`arena_last_updated`），能力分数变化快，过期要重采
4. **不准用单次测评当权威**——LMArena 是众包投票，置信区间宽

```yaml
# vendor.yml 里加（未来用）
arena:
  model_name: GLM-5.2              # LMArena 上的模型名（可能跟 vendor 名不一样）
  score: 1357                       # LMArena Elo 分（arena-hard / code arena）
  rank: 4                           # 全球排名
  category: code                    # 评测类别（code / overall / hard-prompts）
  source: https://lmarena.ai/leaderboard
  last_updated: 2026-07-22
  note: |
    LMArena 2026-07 榜单可能未收录最新版本，分数参考价值有限。
```

**前端展示**（未来 P1）：
- 加「能力」排序按钮（arena_score 降序，跨厂商）
- 每个套餐行加分数标签（类似 `[×20]` 标签的样式）
- 数据缺失的厂商显示 `—`，**不准伪造分数**

**自检**：加能力排序前，先确认数据源是不是覆盖所有上榜厂商。如果只有 3/5 厂商有分数，排序意义不大。

---

### 铁律 16：不准编造"官方标称"数据

**事故**（2026-07-22 发现，严重公信力事故）：上一个 AI 在 `data/plans/kimi-code-*.yml` 里写了：
```yaml
tokens_official_claimed: 50000000    # andante 50M
tokens_official_claimed: 200000000   # moderato 200M
tokens_official_claimed: 1000000000  # allegretto 1000M
tokens_official_claimed: 3000000000  # allegro 3000M
```
**这些数字全部是编的**——Kimi 官方只标倍数（1×/4×/20×/60×），**从不公开绝对 token 数**。AI 看到社区第三方推算就当成官方数据填了。

**规则**：
- `tokens_official_claimed` / `requests_official` 字段**只能填官方页能直接看到的数字**
- **不确定是不是官方公布时，宁可留 null，不准填**
- 任何 `official_*` 字段必须有 `source_url` 或注释指向官方页
- 社区推算的数字只能进 `measurements`（带 `credibility: low`），**不准进 `official_*`**

**自检**：写 `official_*` 字段前，问自己——这个数字在厂商官网哪个页面能看到？看不到 = 不准写。

**关联铁律**：铁律 9（实测 vs 宣称严格分栏），铁律 10（单点标 disputed）。

**lint 检查**（防回归，已加到 lint-plans.mjs）：
- Kimi 厂商的 `tokens_official_claimed` 必须是 null（官方明确不公开绝对 token）
- 其他厂商如有 `tokens_official_claimed`，必须能找到官方依据（lint 暂不强检，靠人 review）

---

## 2. YAML Schema 模板

### vendor.yml 完整字段

```yaml
# 厂商级元数据。同厂商所有套餐共享。
vendor_id: volcengine                    # 必填，跟 plans 里 vendor 对应
vendor_display: 火山方舟                  # 必填，中文展示名
vendor_display_en: Volcengine Ark        # 可选，英文展示名
brand_color: "#0b8aff"                   # 必填，品牌色（hex）
homepage: https://...                    # 必填，官网
docs: https://...                        # 可选，API 文档
last_verified: 2026-07-21                # 必填，最后核实日期

# 邀请码（铁律 7）
affiliate:
  code: NMJG4D6P
  url: https://...                       # 带 source/折扣参数的邀请链接
  discount: 0.95                          # 折扣系数（0.95 = 95折）
  stackable: true                         # 能否跟官方活动叠加
  expires: 2026-08-08                     # 过期日（铁律 11）
  owner: OLmatter
  added_at: 2026-07-21
  discount_note: 与火山首单活动叠加...    # 可选，叠加规则说明
# 无邀请码：affiliate: null

# 厂商公共特性
shared_features:
  primary_model: GLM-5.2                  # 主力模型（榜单对比基准）
  models: [...]                           # 模型池
  clients: [...]                          # 支持的客户端
  rate_limit_tiers: [5h, weekly, monthly] # 限流窗口层级
  rate_limit_note: ...                    # 限流规则说明

# 厂商特殊机制（仅 zhipu/zai 有 ZCode，铁律 2）
rate_multipliers:
  normal:
    peak: 3.0
    off_peak: 1.0
  zcode:
    peak: 2.0
    off_peak: 0.67
  zcode_note: |
    ZCode 权益说明...
```

### plan.yml 完整字段

```yaml
# 套餐级数据。vendor 字段指向 vendor.yml。
plan_id: volc-coding-pro                  # 必填，全局唯一
vendor: volcengine                        # 必填，指向 vendor_id
plan_name: Coding Plan Pro                # 必填
plan_tier: pro                            # 必填，lite/pro/max/plus/andante 等
status: active                            # 必填，active/deprecated
last_verified: 2026-07-21                 # 必填

# 定价（铁律 1 + 8）
pricing:
  currency: CNY                           # CNY 或 USD
  # 刊例价（所有人付的）
  original_monthly: 200
  original_quarterly: 600                 # 可选
  original_yearly: 2400                   # 可选
  # 首单/限时特惠（少付钱）
  intro_monthly: 49.9
  intro_quarterly: 299.80
  intro_yearly: 2099.80
  intro_duration_months: 2
  intro_condition: 新购 / 同主体仅一次
  intro_end_hint: 2026-08-08              # 铁律 11
  auto_renew_default: true
  price_warning: 第 3 个月自动恢复原价...  # 可选，价格陷阱提示

# 三周期限额（铁律 4 + 9）
limits:
  window_5h:
    requests_official: 6000               # 火山/智谱/zai 才有
    tokens_measured: null                 # 探针反推，留空 ≠ 0
    tokens_official_claimed: null         # 厂商公布 token（仅 minimax/kimi）
  window_weekly:
    requests_official: 45000
    tokens_measured: 508000000            # 508M（写完整数字，铁律 3）
    tokens_official_claimed: null
  window_monthly:
    requests_official: 90000
    tokens_measured: null
    tokens_official_claimed: 1800000000   # 18 亿 = 1.8B
    monthly_estimated: true               # 月度是否估算
    is_unlimited: false                   # Kimi 月度无限 = true

# 实测样本（铁律 10）
measurements:
  - measurement_id: m_2026_07_single_001  # 全局唯一
    source_kind: single_user_probe        # single_user_probe / multi_user_average / verified_pr / burn_quota / aggregate_median / vendor_sibling_inferred / community_report
    user_hash: pending                    # sha256(token+salt) 前 12 位，待 PR 填
    period: 2026-07
    method: burn_quota                    # 可选，测试方法
    monthly_used_tokens: 804430000        # 实际用量
    monthly_used_pct: 90                  # 用量百分比
    inferred_monthly_cap_tokens: 893800000 # = used / pct，反推 cap
    credibility: low                      # low/medium/high（铁律 10）
    disputed: false                       # 铁律 10
    dispute_note: ...                     # disputed=true 必填
    notes: |
      样本说明...

# 套餐特性（可选）
features:
  concurrent_agents: "4-5"
  video_daily_quota: 3
```

---

## 3. 修改前 checklist（做之前）

- [ ] **read 原 YAML 文件**（不准凭印象改，AGENTS.md 第 4 条：探测式更新零容忍）
- [ ] **查 NPL 记忆**：`root.project.<ledger 相关 task>.search query="<vendor> <关键词>"`，看上次踩了什么坑
- [ ] **确认单位**：心算一遍零的个数（亿=8，B=9，M=6，K=3）
- [ ] **确认类别**：这个改动影响 pricing / discount / boost 哪一类？（铁律 1）
- [ ] **如果是新厂商**：先建 vendor.yml（铁律 7），再建 plan.yml，最后加 VENDOR_RATIOS / TIER_RATIOS 到 build-plans.mjs

## 4. 修改后 checklist（验完才算完）

- [ ] **`node scripts/build-plans.mjs`** 成功，无报错
- [ ] **`node scripts/lint-plans.mjs`** 通过（机械检查铁律 3/4/6/9）
- [ ] **数字合理性**：抽查 1-2 个套餐，月 / 周 比例在 2-5×（铁律 6）
- [ ] **`npx vitepress build docs`** 成功
- [ ] **三处 UI 抽查**（如果改了显示字段）：榜单表格 / 厂商页 / 详情页
- [ ] **M1 记忆**：改动写到 NPL（`root.project.<ledger>.task001.mem create`），含"改了什么 + 为什么 + 来源"

---

## 5. 常见错误自检表

| 症状 | 可能原因 | 对应铁律 |
|---|---|---|
| 月度比周度大 10× | B/亿 混用 | 铁律 3 |
| MiniMax 显示"次" | 错填 requests_official | 铁律 4 |
| DS 等价比实际贵 4× | cache_read 当 output 算 | 铁律 5 |
| ZCode 价格异常低 | ZCode 当 discount 算 | 铁律 2 |
| 邀请码按钮在过期日还在显示 | expires 字段缺失/写错 | 铁律 11 |
| 套餐只有一个数据点却显示 high credibility | credibility 字段乱填 | 铁律 10 |
| 同一价格出现两次（原价/首单分不开） | intro/original 混用 | 铁律 8 |
| 厂商页显示"实测 0" | 应该是 null 写成了 0 | 铁律 9 |

---

## 6. 历史事故索引（供溯源）

每条铁律对应的真实事故，详见 NPL 记忆（关键词搜）：
- 铁律 2（ZCode 当折扣）：`zcode 首单九折 邀请码 独立`
- 铁律 3（B/亿 混用）：`minimax 18B 18亿 月度 weekly`
- 铁律 4（次数 vs tokens）：`minimax claimed 次 tokens`
- 铁律 5（cache 当 output）：`minimax 烧表 输入 缓存 编程比例`
- 铁律 10（单点当高可信）：`kimi allegretto 690M 326M median`
- 铁律 12（USD/CNY 混淆）：`zai USD 排序 original_monthly 折算`
- 铁律 13（tierRank 残缺）：`kimi andante moderato allegretto tier 排序 乱`

---

## 7. 升级机制（本 skill 怎么演进）

**触发**：每次用户发现新的事故并要求"以后不准再这样"
1. 加新铁律（编号递增，保留历史编号）
2. 在第 6 节加 NPL 关键词
3. 如果可机械化检查，同步加到 `scripts/lint-plans.mjs`
4. 本 skill 改动也写 NPL（slug: `ledger-skill-铁律N-<短描述>`）

**禁止**：私自删铁律、私自放宽检查规则。任何放宽必须用户明确同意。
