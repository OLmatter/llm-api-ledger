// 读 data/vendors/*.yml + data/plans/*.yml，合成 plans.json 给前端消费。
// 输出：docs/.vitepress/plans.json
//
// 数据合成规则：
// 1. tokens_measured 优先用 plan.limits.window_*.tokens_measured（直接写死）
// 2. 没 tokens_measured 的，按同厂商其他档实测 + tier_ratio 反推
// 3. 月度预估（monthly_estimated=true）按周 × monthly_factor 算

import yaml from 'js-yaml'
import { readFileSync, writeFileSync, readdirSync, mkdirSync } from 'node:fs'
import { join, dirname } from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = dirname(fileURLToPath(import.meta.url))
const root = join(__dirname, '..')

function loadYamlDir(dir) {
  const out = {}
  for (const f of readdirSync(dir).filter(f => f.endsWith('.yml'))) {
    const doc = yaml.load(readFileSync(join(dir, f), 'utf-8'))
    out[doc.vendor_id || doc.plan_id] = doc
  }
  return out
}

const vendors = loadYamlDir(join(root, 'data', 'vendors'))
const planFiles = readdirSync(join(root, 'data', 'plans')).filter(f => f.endsWith('.yml'))

// USD → CNY 折算汇率（顶部常量，便于调整；近期 7.10–7.20）
// 榜单里 USD 套餐（Z.AI）会在原价下显示一行 "≈ ¥xxx" 作为对比参考
const USD_TO_CNY = 7.15

// 统一备注体系（annotations）label/tooltip 中心定义
// kind: scenario(口径) / promo(优惠加成) / warning(异常争议) / note(普通备注)
// 新增一种备注 = 这里加一条 + 前端 .ann-<kind> 上色，不再新长一套字段
const ANNOTATION_DEFS = {
  'scenario/full_offpeak': {
    label: '全非高峰期',
    tooltip: '官方场景估算「全非高峰 + 95% cache」口径（区间上限）：全部流量在非高峰时段按 0.5 倍积分消耗时的最大可跑 tokens，全高峰口径则为区间下限。',
  },
  'scenario/probe_inferred': {
    label: '实测反推',
    tooltip: '探针实测反推口径：由用户实测用量反推到 100% 满额（普通客户端口径），非官方场景估算，与「全非高峰期」口径不可直接对比。',
  },
  'scenario/opencode-go-client': {
    label: 'Go 观测',
    tooltip: '数据是 OpenCode 团队在自家 Go 客户端上观察到的使用模式，不是该模型 API 在所有场景下的通用值（缓存率尤其偏高于通用 API）。',
  },
  'promo/zcode_1_5x': {
    label: 'ZCode×1.5',
    tooltip: 'ZCode 客户端权益：全周期 0.67 折算（等效 1.5x 额度）。倍率来自 vendor.yml rate_multipliers.zcode，跟邀请码独立可叠加。',
  },
  'warning/disputed': {
    label: '数据有争议',
    tooltip: '该数据存在较大不确定性或多方口径冲突，谨慎参考。',
  },
}

// ── DeepSeek V4 按量等价换算 ──
// 把套餐月费换算成「如果买 DS V4 非高峰期按量，能跑多少 tokens」
// 用真实编程比例（non-cache input 9.4% / output 1.2% / cache read 89.4%）
// DS V4 非高峰期定价（元/百万 tokens，来源 GCMP deepseek.json）
// 两个版本：Flash（便宜）和 Pro（贵 3 倍）
const DS_V4_PRICES = {
  flash: { input: 1.0, output: 2.0, cache_read: 0.02 },
  pro:   { input: 3.0, output: 6.0, cache_read: 0.025 },
}
// 真实编程比例（缓存命中按实测偏高场景 95%；input/output 按原比例分剩余 5%）
const CODING_RATIO = { input: 0.044, output: 0.006, cache_read: 0.95 }
// 每百万混合 tokens 的 DS V4 价格（两个版本各算一次）
function dsV4MixedPricePerM(variant) {
  const p = DS_V4_PRICES[variant]
  return CODING_RATIO.input * p.input +
         CODING_RATIO.output * p.output +
         CODING_RATIO.cache_read * p.cache_read
}

// 各厂商官方订阅直达链接（用户提供的国内正版页面，affiliate 缺失时兜底）
const SUBSCRIBE_URLS = {
  volcengine: 'https://www.volcengine.com/activity/codingplan',
  zhipu:      'https://www.bigmodel.cn/glm-coding',
  minimax:    'https://platform.minimaxi.com/subscribe/token-plan',
  kimi:       'https://www.kimi.com/code',
  zai:        'https://z.ai/subscribe',         // 智谱海外版（USD / 海外线路）
  opencode:   'https://opencode.ai/docs/zh-cn/go/',
}

// 各厂商的窗口换算比例
// 智谱：周 = 5 × 5h；月 = 4.3 × 周（无官方月封顶，预估）
// 火山：周 = 7.5 × 5h；月 = 2 × 周（官方硬封顶）
// MiniMax：周 = 10 × 5h；月 = 4.3 × 周（按周反推，跟智谱一样逻辑）
// Kimi：周独立公布（无固定换算公式）；5h/月 都留空
// Z.AI：跟国内智谱完全一致（智谱海外版）
const VENDOR_RATIOS = {
  volcengine: { weekly_to_5h: 1 / 7.5, monthly_to_weekly: 2.0, monthly_is_estimate: false },
  zhipu:      { weekly_to_5h: 1 / 5.0, monthly_to_weekly: 4.3, monthly_is_estimate: true },
  minimax:    { weekly_to_5h: 1 / 10.0, monthly_to_weekly: 4.3, monthly_is_estimate: true },
  kimi:       { weekly_to_5h: null, monthly_to_weekly: null, monthly_is_estimate: false, monthly_unlimited: true },
  zai:        { weekly_to_5h: 1 / 5.0, monthly_to_weekly: 4.3, monthly_is_estimate: true },
  openai:     { weekly_to_5h: null, monthly_to_weekly: 4.0, monthly_is_estimate: true },
  // Anthropic:5h 是主要瓶颈,周/月 Anthropic 不公开 cap 数字(留 null,前端显示 —)
  anthropic:  { weekly_to_5h: null, monthly_to_weekly: null, monthly_is_estimate: false },
  // opencode Go:5h/周/月三个窗口官方都直接公布($12/$30/$60 + per-model 请求数),无需任何反推
  opencode:   { weekly_to_5h: null, monthly_to_weekly: null, monthly_is_estimate: false },
}

// 各厂商不同 tier 的倍率（基于官方产品定义）
// volcengine: Lite:Pro = 1:5
// zhipu: Lite:Pro:Max = 1:5:20
// minimax: Plus:Max:Ultra = 1:3:11.8
// kimi: Andante:Moderato:Allegretto:Allegro = 1:4:20:60
// zai: Lite:Pro:Max = 1:5:20（跟国内智谱完全对齐）
// tencent: Coding Plan lite:pro=1:5; Token Plan lite:standard:pro:max=1:2:5:20
//   (pro=5 两条产品线相同档,排序靠 plan_id 字典序兜底)
// openai: Plus:Pro-5x:Pro-20x = 1:5:20
// anthropic: Pro:Max-5x:Max-20x = 1:5:20 (Claude Code 倍率,跟 OpenAI ChatGPT Codex 同档)
const TIER_RATIOS = {
  volcengine: { lite: 1, pro: 5 },
  zhipu:      { lite: 1, pro: 5, max: 20 },
  minimax:    { plus: 1, max: 3, ultra: 11.8 },
  kimi:       { andante: 1, moderato: 4, allegretto: 20, allegro: 60 },
  zai:        { lite: 1, pro: 5, max: 20 },
  tencent:    { lite: 1, standard: 2, pro: 5, max: 20 },
  openai:     { go: 0.4, plus: 1, 'pro-5x': 5, 'pro-20x': 20, business: 1.25, enterprise: 30 },
  anthropic:  { pro: 1, 'max-5x': 5, 'max-20x': 20 },
}

function getTierRatio(vendor, fromTier, toTier) {
  const r = TIER_RATIOS[vendor]
  if (!r || !r[fromTier] || !r[toTier]) return null
  return r[toTier] / r[fromTier]
}

// 从 plan 直接拿 tokens（如果 plan 文件里已经填了 tokens_measured）
function getDirectTokens(plan) {
  const lim = plan.limits || {}
  const ratio = VENDOR_RATIOS[plan.vendor]
  // SOP 铁律 18：tokens_inference_disabled 同步禁止 in-function 周×ratio 推导和 measurements 反推
  // 之前只 gate 了外层 inferTokensFromSibling,内层 monthly = weekly × 4.3 仍会跑出"看起来像实测"的数字
  const inferenceDisabled = plan.tokens_inference_disabled === true
  const direct = {
    h5: lim.window_5h?.tokens_measured ?? lim.window_5h?.tokens_scenario_estimate ?? null,
    weekly: lim.window_weekly?.tokens_measured ?? lim.window_weekly?.tokens_scenario_estimate ?? null,
    monthly: lim.window_monthly?.tokens_measured ?? lim.window_monthly?.tokens_scenario_estimate ?? null,
    monthly_estimated: lim.window_monthly?.monthly_estimated || false,
  }
  // Kimi 特殊：周可能直接从 measurements 拿（Allegretto 社区实测 690M）
  if (direct.weekly == null && !inferenceDisabled) {
    const m = (plan.measurements || [])[0]
    if (m?.weekly_tokens_measured) {
      direct.weekly = m.weekly_tokens_measured
      direct.monthly_source = 'community_measured'
    } else if (m?.inferred_weekly_tokens) {
      direct.weekly = m.inferred_weekly_tokens
      direct.monthly_source = 'inferred_from_sibling'
    }
  }
  // 5h 实测 → 推周（按 ratio）
  if (direct.h5 && direct.weekly == null && ratio?.weekly_to_5h) {
    direct.weekly = Math.round(direct.h5 / ratio.weekly_to_5h)
  }
  // 月度：Kimi 无月度（monthly_unlimited）；其他按周×ratio（inferenceDisabled 时跳过，避免把 cap 当实测）
  if (direct.monthly == null && !ratio?.monthly_unlimited && !inferenceDisabled) {
    if (direct.weekly && ratio?.monthly_to_weekly) {
      direct.monthly = Math.round(direct.weekly * ratio.monthly_to_weekly)
      direct.monthly_estimated = ratio.monthly_is_estimate
      if (!direct.monthly_source) direct.monthly_source = 'inferred_from_weekly'
    }
  }
  // 从 measurements 反推（火山 Pro 月度 / MiniMax Max 5h burn 测试）
  if (direct.h5 == null && direct.monthly == null && !ratio?.monthly_unlimited && !inferenceDisabled) {
    const m = (plan.measurements || [])[0]
    if (m?.inferred_monthly_cap_tokens) {
      direct.monthly = m.inferred_monthly_cap_tokens
      if (ratio?.monthly_to_weekly) {
        direct.weekly = Math.round(direct.monthly / ratio.monthly_to_weekly)
        direct.h5 = Math.round(direct.weekly * ratio.weekly_to_5h)
        direct.monthly_estimated = ratio.monthly_is_estimate
        direct.monthly_source = 'inferred_from_measurement'
      }
    }
    if (m?.inferred_h5_cap_tokens) {
      direct.h5 = m.inferred_h5_cap_tokens
      if (ratio?.weekly_to_5h) {
        direct.weekly = Math.round(direct.h5 / ratio.weekly_to_5h)
      }
    }
  }
  return direct
}

// 反推 tokens：本档没填，找同厂商其他档实测
function inferTokensFromSibling(plan, allRawPlans) {
  const vendor = plan.vendor
  const ratio = VENDOR_RATIOS[vendor]
  if (!ratio) return null

  // 找同厂商能拿到 tokens 的 sibling（不管是直接填还是从 measurements 推）
  for (const sib of allRawPlans) {
    if (sib.vendor !== vendor || sib.plan_id === plan.plan_id) continue
    const sibTokens = getDirectTokens(sib)
    if (sibTokens.weekly == null) continue

    const tierRatio = getTierRatio(vendor, sib.plan_tier, plan.plan_tier)
    if (!tierRatio) continue

    // 5h/周 按 tierRatio 反推
    const weekly = Math.round(sibTokens.weekly * tierRatio)
    const h5 = ratio.weekly_to_5h ? Math.round(weekly * ratio.weekly_to_5h) : null

    // 月度：按周 × monthly_to_weekly 反推（实测口径）
    let monthly = null
    let monthlySource = null
    let monthlyEstimated = false
    if (ratio.monthly_to_weekly) {
      monthly = Math.round(weekly * ratio.monthly_to_weekly)
      monthlySource = 'inferred_from_sibling'
      monthlyEstimated = ratio.monthly_is_estimate
    }

    return {
      h5,
      weekly,
      monthly,
      monthly_estimated: monthlyEstimated,
      monthly_source: monthlySource,
    }
  }
  return null
}

const plans = planFiles.map(f => {
  const p = yaml.load(readFileSync(join(root, 'data', 'plans', f), 'utf-8'))
  const v = vendors[p.vendor] || {}

  // ZCode 折算倍率：只由 vendor.yml 的 rate_multipliers.zcode 定义驱动（off_peak 0.67 折算 → 等效 1/0.67=1.5 倍）。
  // vendor.yml 没定义 zcode 的厂商，任何 ZCode 字段都不出现（金额/单位等全局量除外，权益必须哪里定义哪里出现）
  const zcodeBoost = v.rate_multipliers?.zcode?.off_peak
    ? Math.round((1 / v.rate_multipliers.zcode.off_peak) * 10) / 10   // 1/0.67≈1.4925 → 1.5（与 yml「等效 1.5 倍」及 UI 标签一致）
    : null

  // 邀请码（vendor 级合并）
  const pricing = p.pricing || {}
  const aff = v.affiliate || null
  // 邀请码过期判断：expires 字段过期则视为无邀请码（前端自动隐藏按钮）
  const now = new Date()
  let affActive = aff
  if (aff?.expires) {
    const expDate = new Date(aff.expires)
    if (!isNaN(expDate.getTime()) && expDate < now) {
      affActive = null  // 过期，按无邀请码处理
      console.warn(`⚠ affiliate expired for ${p.plan_id}: ${aff.code} expired ${aff.expires}, hiding`)
    }
  }
  // 计算各种优惠价
  // - 邀请码叠加首单：intro_monthly × discount
  // - 邀请码叠加月付(无 intro_monthly)：original_monthly × discount（MiniMax 场景）
  // - 邀请码叠加季付：intro_quarterly × discount（火山 Lite/Pro 有季付特惠）
  // - 年付邀请码叠加：standard_yearly × discount
  //   (MiniMax yml 里 intro_yearly 实际是标准年付价,不是特惠 — ¥1190/年 = 标价,¥1490 是按月价 ×12 反推)
  // - 年付折月：yearly_monthly_equivalent
  let intro_with_aff = null
  let intro_tag = null
  let intro_tags = []                  // 多 tag 数组：可叠加显示（铁律 1 三类严格分离 + 用户原话「多加一个 tag 也可以」）
  if (affActive?.stackable && affActive.discount) {
    const base = pricing.intro_monthly ?? pricing.original_monthly
    if (base != null) {
      intro_with_aff = Math.round(base * affActive.discount * 100) / 100
      // 统一改名「用邀请码」（之前是「首单+邀请码」/「首单 9 折」，不直接）
      // 紧迫感来自「用」字 + 红色按钮 + 损失对照，不在 tag 文字本身
      intro_tag = '用邀请码'
      intro_tags.push('用邀请码')
    }
  } else if (pricing.intro_monthly) {
    intro_with_aff = pricing.intro_monthly
    // 邀请码不给被推荐人折扣时（no_user_discount），这个价是官方首单价、人人都有，
    // 标「用邀请码」会误导成"点了链接才有"（opencode Go 首月 $5 属此类）
    // 用户原话 2026-08-04：优惠 ≠ 邀请码，无邀请码时默认 tag = "首月价"
    intro_tag = '首月价'
    // 如果 yml 没有显式 intro_tag，build 默认把"首月价" push 进去（保持向后兼容）
    if (!pricing.intro_tag && !intro_tags.includes(intro_tag)) {
      intro_tags.push(intro_tag)
    }
  }
  // yml 显式声明的 intro_tag 覆盖默认值（铁律 18 不擅改默认逻辑，只在显式声明时覆盖）
  if (pricing.intro_tag) {
    intro_tag = pricing.intro_tag
    // intro_tags 数组去重：yml 显式值应排第一位
    intro_tags = intro_tags.filter(t => t !== intro_tag)
    intro_tags.unshift(intro_tag)
  }
  // yml 显式声明的 affiliate_tag（独立于 intro_tag，邀请码折扣的展示文本）
  if (pricing.affiliate_tag && !intro_tags.includes(pricing.affiliate_tag)) {
    intro_tags.push(pricing.affiliate_tag)
  }
  // 季付邀请码叠加(base 优先 intro_quarterly 限时价,fallback original_quarterly 长期方案价 — Z.AI/智谱场景)
  const quarterly_with_aff_base = pricing.intro_quarterly ?? pricing.original_quarterly
  const intro_quarterly_with_aff = (affActive?.stackable && affActive.discount && quarterly_with_aff_base != null)
    ? Math.round(quarterly_with_aff_base * affActive.discount * 100) / 100
    : null
  // 标准年付价(用户实际年付的钱),按字段优先级:
  // - original_yearly: 字段名直观,Kimi/Z.AI/火山 Lite/Pro 用(¥151.2/$604.8 等)
  // - intro_yearly: MiniMax 历史命名(¥1190 = 用户付的标价,字段语义错位但保留)
  // - yearly_total: Kimi 字段名(¥468/年)
  // 标准年付价(榜单年付列显示用),按字段优先级:
  // - original_yearly 定价（Kimi/Z.AI/火山 Lite/Pro 用 ¥151.2/$604.8 等）
  // - intro_yearly MiniMax 历史命名（¥1190 = 用户付的标价,字段语义错位但保留）
  // - yearly_total Kimi 字段名（¥468/年）
  const standard_yearly = pricing.original_yearly || pricing.intro_yearly || pricing.yearly_total || null
  // 年付邀请码叠加基价：用户实际付的年付价（限时特惠优先于原价）
  // ⚠ 邀请码叠加必须基于「用户实际付的钱」，不是原价（否则折扣算错）
  // 例：MiniMax Ultra intro_yearly=¥4690（用户付的），邀请码 9 折 = ¥4221（不是原价 ¥5628 × 0.9 = ¥5065）
  // 例：火山 Pro intro_yearly=¥2099.80（限时），邀请码 9.5 折 = ¥1994.81（不是原价 ¥2400 × 0.95）
  const yearly_aff_base = pricing.intro_yearly || pricing.original_yearly || pricing.yearly_total || null
  const yearly_with_aff = (affActive?.stackable && affActive.discount && yearly_aff_base)
    ? Math.round(yearly_aff_base * affActive.discount * 100) / 100
    : null
  // 年付折月价：优先用 yml 显式字段；没有就从 original_yearly / 12 反推
  const explicit_yearly_monthly = pricing.yearly_monthly_equivalent || null
  const yearly_monthly = explicit_yearly_monthly
    ?? (pricing.original_yearly ? Math.round(pricing.original_yearly / 12 * 10) / 10 : null)
    ?? (pricing.yearly_total ? Math.round(pricing.yearly_total / 12 * 10) / 10 : null)

  // tokens：优先直接填，没有就反推
  const allPlans = planFiles.map(pf =>
    yaml.load(readFileSync(join(root, 'data', 'plans', pf), 'utf-8'))
  )
  let tokens = getDirectTokens(p)
  // SOP 铁律 18：yml 显式标记 tokens_inference_disabled: true 时，禁止 sibling 反推
  // 用于 v3 等"还没实测数据"的套餐，避免 build 偷偷反推同厂商其他档位的实测
  const inferenceDisabled = p.tokens_inference_disabled === true
  if (tokens.weekly == null && !inferenceDisabled) {
    const inferred = inferTokensFromSibling(p, allPlans)
    // 反推只补 null 字段，不覆盖已有真实值（如 yml 里写的 monthly）
    // 之前的 bug：直接 tokens = inferred 会把 Allegro 的 monthly(30亿) 丢成 null
    if (inferred) {
      for (const k of ['h5','weekly','monthly','monthly_estimated','monthly_source']) {
        if (tokens[k] == null && inferred[k] != null) tokens[k] = inferred[k]
      }
    }
  }

  return {
    plan_id: p.plan_id,
    vendor: p.vendor,
    vendor_display: v.vendor_display || p.vendor,
    brand_color: v.brand_color || null,
    plan_name: p.plan_name,
    plan_tier: p.plan_tier,
    // 同厂商不同档位的用量倍率（基于官方产品定义，1 = 最低档）
    // 例：kimi andante=1, moderato=4, allegretto=20, allegro=60
    // 前端用作「×N」标签显示，让用户一眼看出档位差距
    tier_multiplier: p.tier_multiplier ?? (() => {
      const tr = TIER_RATIOS[p.vendor]
      const m = tr?.[p.plan_tier]
      // 整数显示 4，小数显示 11.8（保留 1 位）
      return m != null ? (Number.isInteger(m) ? m : Math.round(m * 10) / 10) : null
    })(),
    status: p.status,
    // 主力模型（榜单对比基准；plan 级字段优先于 vendor 级，详见 SKILL-and-SOP.md 铁律 13）
    primary_model: p.primary_model || v.shared_features?.primary_model || null,

    pricing: {
      currency: pricing.currency || 'CNY',
      original_monthly: pricing.original_monthly,
      original_quarterly: pricing.original_quarterly || null,    // 季原价(目前各家都没数据)
      // 包年价 = 标准年付价(MiniMax: intro_yearly=¥1190是标价,不是特惠;Kimi: yearly_total=¥468)
      original_yearly: standard_yearly,
      // USD 套餐同步输出 CNY 折算价（按顶部 USD_TO_CNY 汇率，便于跟国内套餐对比）
      original_monthly_cny: pricing.currency === 'USD' && pricing.original_monthly != null
        ? Math.round(pricing.original_monthly * USD_TO_CNY)
        : null,
      // 优惠价(只有真优惠,标准长期方案不算)
      intro_monthly: pricing.intro_monthly || null,
      intro_with_affiliate: intro_with_aff,
      intro_tag: intro_tag,                                  // 主 tag（向后兼容）
      intro_tags: intro_tags,                                // 多 tag 数组（用户原话「多加一个 tag 也可以」——首月优惠 + 邀请码 可叠加显示）
      // 优惠多阶段结构（用户 2026-08-04：优惠生命周期是「首月 + 首次续费」2 阶段）
      intro_stages: (pricing.intro_stages && Array.isArray(pricing.intro_stages))
        ? pricing.intro_stages.map(s => ({
            stage: s.stage,
            name: s.name,
            duration_months: s.duration_months ?? null,
            price: s.price ?? null,
            discount_rate: s.discount_rate ?? null,
            condition: s.condition ?? null,
          }))
        : null,
      // 首次续费价（兼容旧前端：直接读 ¥20 / ¥100）
      intro_renewal_price: (() => {
        if (!pricing.intro_stages || !Array.isArray(pricing.intro_stages)) return null
        const renewal = pricing.intro_stages.find(s => s.stage === 2)
        return renewal?.price ?? null
      })(),
      intro_quarterly: pricing.intro_quarterly || null,
      intro_quarterly_with_affiliate: intro_quarterly_with_aff,    // 季付邀请码叠加
      yearly_monthly_equivalent: yearly_monthly,
      yearly_total: pricing.yearly_total || null,
      intro_yearly: pricing.intro_yearly || null,    // 数据保留(给 standard_yearly 用),UI 不再标"特惠"
      yearly_with_affiliate: yearly_with_aff,    // 年付邀请码叠加(MiniMax: ¥1190 × 0.9 = ¥1071)
      // 全套 CNY 折算（USD 套餐专用；CNY 套餐字段值相同，前端切货币直接用）
      is_usd: pricing.currency === 'USD',
      fx_rate: USD_TO_CNY,
      original_monthly_in_cny: pricing.currency === 'USD' && pricing.original_monthly != null
        ? Math.round(pricing.original_monthly * USD_TO_CNY * 10) / 10
        : pricing.original_monthly,
      original_quarterly_in_cny: (pricing.currency === 'USD' && pricing.original_quarterly != null)
        ? Math.round(pricing.original_quarterly * USD_TO_CNY * 10) / 10
        : pricing.original_quarterly,
      original_yearly_in_cny: (pricing.currency === 'USD' && standard_yearly != null)
        ? Math.round(standard_yearly * USD_TO_CNY * 10) / 10
        : standard_yearly,
      intro_with_affiliate_in_cny: (pricing.currency === 'USD' && intro_with_aff != null)
        ? Math.round(intro_with_aff * USD_TO_CNY * 10) / 10
        : intro_with_aff,
      intro_quarterly_with_affiliate_in_cny: (pricing.currency === 'USD' && intro_quarterly_with_aff != null)
        ? Math.round(intro_quarterly_with_aff * USD_TO_CNY)
        : intro_quarterly_with_aff,
      yearly_with_affiliate_in_cny: (pricing.currency === 'USD' && yearly_with_aff != null)
        ? Math.round(yearly_with_aff * USD_TO_CNY)
        : yearly_with_aff,
      yearly_monthly_equivalent_in_cny: (pricing.currency === 'USD' && yearly_monthly != null)
        ? Math.round(yearly_monthly * USD_TO_CNY * 10) / 10
        : yearly_monthly,
    },

    limits: {
      window_5h: { requests_official: p.limits?.window_5h?.requests_official ?? null },
      window_weekly: { requests_official: p.limits?.window_weekly?.requests_official ?? null },
      window_monthly: {
        requests_official: p.limits?.window_monthly?.requests_official ?? null,
        is_estimate: tokens.monthly_estimated,
      },
    },

    // 宣称用量（厂商公布的官方值，单位跟随厂商）
    // 火山/智谱/z.ai v2：次数（requests_official）
    // 智谱/z.ai v3：积分/Credits（credits_weekly，单位 = 积分 or Credits）
    // MiniMax/Kimi：tokens（官方公布 token 总量）
    // opencode Go：美元额度（cost_limit_usd,opencode 官方原意是金额不是次数）
    claimed: (() => {
      const lim = p.limits || {}
      // isTokenVendor: 套餐按 token 数计费的厂商
      // minimax/kimi/anthropic 直接公布 tokens；tencent Token Plan 也是 token 单位
      const isTokenVendor = p.vendor === 'minimax' || p.vendor === 'kimi' || p.vendor === 'anthropic' || p.vendor === 'tencent'
      // opencode Go：官方窗口是「$12/$30/$60 使用额度」，不是次数也不是 token
      const isCostDollar = p.vendor === 'opencode' && lim.window_5h?.cost_limit_usd != null
      if (isCostDollar) {
        const cred = affActive?.credit_usd
        return {
          unit: '$',
          h5: lim.window_5h.cost_limit_usd,
          weekly: lim.window_weekly?.cost_limit_usd ?? null,
          monthly: lim.window_monthly?.cost_limit_usd ?? null,
          // 用邀请码后额度：仅加在月列
          // 原因：usage credit 是「一次性 apply」而非「每周期叠加」(credit_apply: once)。
          // 一次性 $5 credit 计入整体订阅期(约 1 个月),**不能**每个 5h/周窗口都加 $5,
          // 否则会显示「每个窗口都多 $5」=假象「每月额外 $5×3=$15」,这跟实际不符。
          // 5h 和周窗口的撞 limit 阈值仍按基准；月窗口撞 limit 阈值 = $60 + $5 = $65(整体期间)
          with_credit: cred ? {
            h5: null,
            weekly: null,
            monthly: (lim.window_monthly?.cost_limit_usd ?? 0) + cred,
            credit_usd: cred,
          } : null,
        }
      }
      // v3 积分/Credits 单位（智谱/z.ai v3 启用，单位不同）
      const hasCredits = lim.window_weekly?.credits_weekly != null
      if (hasCredits) {
        return {
          unit: p.vendor === 'zai' ? 'Credits' : '积分',
          h5: lim.window_5h?.credits_5h ?? null,
          weekly: lim.window_weekly.credits_weekly ?? null,
          monthly: lim.window_monthly?.credits_monthly ?? null,
        }
      }
      if (isTokenVendor) {
        return {
          unit: 'tokens',
          h5: null,
          weekly: lim.window_weekly?.tokens_official_claimed || null,
          monthly: lim.window_monthly?.tokens_official_claimed || null,
        }
      }
      // 火山/智谱/z.ai v2：次数
      return {
        unit: '次',
        h5: lim.window_5h?.requests_official ?? null,
        weekly: lim.window_weekly?.requests_official ?? null,
        monthly: lim.window_monthly?.requests_official ?? null,
      }
    })(),
    claimed_unit: (() => {
      const lim = p.limits || {}
      // yml 顶层显式声明的 claimed_unit 优先（铁律 18 不擅改默认逻辑）
      if (p.claimed_unit) return p.claimed_unit
      if (p.vendor === 'opencode' && lim.window_5h?.cost_limit_usd != null) return '$'
      if (lim.window_weekly?.credits_weekly != null) {
        return p.vendor === 'zai' ? 'Credits' : '积分'
      }
      return (p.vendor === 'minimax' || p.vendor === 'kimi' || p.vendor === 'anthropic' || p.vendor === 'tencent') ? 'tokens' : '次'
    })(),

    // 实测 tokens（反推到 100% 满额）
    tokens: {
      h5: tokens.h5,
      weekly: tokens.weekly,
      monthly: tokens.monthly,
      monthly_is_estimate: tokens.monthly_estimated,
      monthly_source: tokens.monthly_source || null,
      // ZCode 专属优惠：倍率来自 vendor.yml rate_multipliers.zcode（见顶部 zcodeBoost）
      zcode_h5: tokens.h5 && zcodeBoost ? Math.round(tokens.h5 * zcodeBoost) : null,
      zcode_weekly: tokens.weekly && zcodeBoost ? Math.round(tokens.weekly * zcodeBoost) : null,
      zcode_monthly: tokens.monthly && zcodeBoost ? Math.round(tokens.monthly * zcodeBoost) : null,
      zcode_applicable: zcodeBoost != null,
      // 用量口径备注:统一 annotations(聚合行没有 model_breakdown,备注挂整个单元格)
      // 来源:plan 级 yml usage_annotations 数组,或旧字段 usage_remark(未迁移文件兼容)
      annotations: (() => {
        const anns = []
        const legacy = p.usage_remark
        const list = (p.usage_annotations && p.usage_annotations.length) ? p.usage_annotations : (legacy ? [{ kind: 'scenario', value: legacy }] : [])
        for (const a of list) {
          const def = ANNOTATION_DEFS[a.kind + '/' + a.value]
          anns.push({ kind: a.kind, value: a.value, label: def?.label || a.value, tooltip: def?.tooltip || '' })
        }
        return anns
      })(),
      usage_remark: p.usage_remark || null,   // 过渡保留:未迁移前端仍可读
      // 实测周聚合说明(任意形式的跨档/多源 measurement 的 notes,用于 hover tooltip)
      // 优先级:aggregate_median(多源聚合) > vendor_sibling_inferred(跨境反推) > community_report 带 source_plan(同档反推)
      weekly_aggregate_note: ((p.measurements || []).find(m => m.source_kind === 'aggregate_median')?.notes)
        ?? ((p.measurements || []).find(m => m.source_kind === 'vendor_sibling_inferred')?.notes)
        ?? ((p.measurements || []).find(m => m.source_plan && m.source_weekly_tokens)?.notes)
        ?? null,
      // 数据争议标记：disputed=true 时给前端显示红色 ⚠
      // 铁律 18：仅「被同模型新测量取代」的 outdated disputed 不触发争议标签（如 DS 旧价）；
      // 模型被换但数据仍有效的 outdated（如 GLM-5.2）若 disputed 照常触发
      weekly_disputed: (() => {
        const perModelAll = (p.measurements || []).filter(m => m.source_kind === 'per_model_breakdown' && m.model_id)
        const activeModels = new Set(perModelAll.filter(m => !m.outdated).map(m => m.model_id))
        return (p.measurements || []).some(m => m.disputed === true && (!m.outdated || !activeModels.has(m.model_id)))
      })(),
      dispute_note: (() => {
        const perModelAll = (p.measurements || []).filter(m => m.source_kind === 'per_model_breakdown' && m.model_id)
        const activeModels = new Set(perModelAll.filter(m => !m.outdated).map(m => m.model_id))
        const found = (p.measurements || []).find(m => m.disputed === true && (!m.outdated || !activeModels.has(m.model_id)))
        return found?.dispute_note || null
      })(),
    },

    measurements_count: (p.measurements || []).length,
    // 铁律 18：聚合口径与 model_breakdown 显示口径一致——
    // outdated 且被同模型新测量取代的不参与；模型被换但数据仍有效的（如 GLM-5.2）参与
    measurements_credibility_max: (() => {
      const perModelAll = (p.measurements || []).filter(m => m.source_kind === 'per_model_breakdown' && m.model_id)
      const activeModels = new Set(perModelAll.filter(m => !m.outdated).map(m => m.model_id))
      const visible = m => !m.outdated || !activeModels.has(m.model_id)
      return (p.measurements || []).reduce(
        (m, x) => {
          if (!visible(x)) return m
          const rank = { low: 1, medium: 2, high: 3 }
          return Math.max(m, rank[x.credibility] || 0)
        }, 0
      )
    })(),
    // Per-model breakdown：每个 model 一个 token 组合（同一 cap 不同 model 用量不同）
    // 前端渲染多个 model_tag 堆叠在 tokens 列
    // 铁律 18：outdated measurement 分两种，处理不同：
    //   a) 同模型被重测取代（如 DS V4 Flash 旧价被重定价取代）→ 藏旧显新（「DS 做对」）
    //   b) 模型本身被新模型取代但数据仍有效（如 GLM-5.2 主字段换成 GLM-5.3）→ **保留显示**（「不准删模型」）
    // 规则：仅当同 model_id 存在非 outdated 的测量时，才隐藏该模型的 outdated 测量
    model_breakdown: (() => {
      const perModelAll = (p.measurements || []).filter(m => m.source_kind === 'per_model_breakdown' && m.model_id)
      const activeModels = new Set(perModelAll.filter(m => !m.outdated).map(m => m.model_id))
      return perModelAll.filter(m => !m.outdated || !activeModels.has(m.model_id))
    })()
      .map(m => {
        // 用邀请码后用量：仅 +monthly。
        // 原因：usage credit 是「一次性 apply」而非「每周期叠加」(credit_apply: once)。
        // 一次性 $5 credit 计入整体订阅期(约 1 个月)+只在月窗口内有效,**不能**5h/周也都加
        // ——否则显示「每个窗口都多 $5」= 假象「每月额外 $5×3 = $15」,跟实际不符。
        const creditUsd = affActive?.credit_usd
        const monthlyCreditBase = m.model_monthly_credit_usd
        let withCredit = null
        if (creditUsd && monthlyCreditBase) {
          const ratio = 1 + creditUsd / monthlyCreditBase
          withCredit = {
            credit_usd: creditUsd,
            h5_tokens: null,                                       // 5h 窗口不变
            weekly_tokens: null,                                   // 周窗口不变
            monthly_tokens: m.window_monthly_tokens ? Math.round(m.window_monthly_tokens * ratio) : null,
          }
        }
        // 统一备注体系（annotations）：模型是「量的维度」(model_id)，其余一切修饰都是 annotation。
        // kind 枚举: scenario(口径) / promo(优惠加成) / warning(异常争议) / note(普通备注)
        // label/tooltip 在 build 层中心化，前端只按 kind 上色，不再各自维护映射
        const anns = []
        const pushAnn = (kind, value) => {
          const def = ANNOTATION_DEFS[kind + '/' + value]
          if (def) anns.push({ kind, value, label: def.label, tooltip: def.tooltip || '' })
          else if (value) anns.push({ kind, value, label: value, tooltip: '' })
        }
        // 兼容旧字段:scope / usage_scenario（未迁移的厂商文件继续生效）
        if (m.usage_scenario) pushAnn('scenario', m.usage_scenario)
        if (m.scope && m.scope !== m.usage_scenario) pushAnn('scenario', m.scope)
        // 新语法:measurement 级 annotations 数组
        for (const a of (m.annotations || [])) pushAnn(a.kind, a.value)
        // promo:ZCode×1.5 由 vendor.yml rate_multipliers.zcode 派生（哪定义哪出现，不在 yml 手写）
        if (zcodeBoost) pushAnn('promo', 'zcode_1_5x')
        if (m.disputed) pushAnn('warning', 'disputed')
        return {
          model_id: m.model_id,
          weekly_tokens: m.window_weekly_tokens,
          monthly_tokens: m.window_monthly_tokens,
          h5_tokens: m.window_5h_tokens || null,
          // promo 修饰的量化结果（倍率来自 zcodeBoost；子行渲染时继承 model_id，铁律 30 自动满足）
          zcode_h5_tokens: m.window_5h_tokens && zcodeBoost ? Math.round(m.window_5h_tokens * zcodeBoost) : null,
          zcode_weekly_tokens: m.window_weekly_tokens && zcodeBoost ? Math.round(m.window_weekly_tokens * zcodeBoost) : null,
          zcode_monthly_tokens: m.window_monthly_tokens && zcodeBoost ? Math.round(m.window_monthly_tokens * zcodeBoost) : null,
          cost_per_million: m.cost_per_million,
          credibility: m.credibility,
          notes: m.notes,
          // 周=月等窗口相等是有意设计(如月额度封顶=周上限)时置 true,lint「窗口相等」豁免
          windows_equal_by_design: m.windows_equal_by_design === true,
          // 统一备注（scenario/promo/warning/note），前端按 kind 上色
          annotations: anns,
          // 用邀请码后用量（仅 opencode 等有 usage_credit 机制的有意义；仅 +monthly 适用）
          with_referral_credit: withCredit,
        }
      }),
    // 数据争议标记：同 weekly_disputed 口径——被同模型新测量取代的 outdated disputed 不算
    measurements_disputed: (() => {
      const perModelAll = (p.measurements || []).filter(m => m.source_kind === 'per_model_breakdown' && m.model_id)
      const activeModels = new Set(perModelAll.filter(m => !m.outdated).map(m => m.model_id))
      return (p.measurements || []).some(x => x.disputed === true && (!x.outdated || !activeModels.has(x.model_id)))
    })(),
    measurements_dispute_note: (() => {
      const perModelAll = (p.measurements || []).filter(m => m.source_kind === 'per_model_breakdown' && m.model_id)
      const activeModels = new Set(perModelAll.filter(m => !m.outdated).map(m => m.model_id))
      const disputed = (p.measurements || []).find(x => x.disputed === true && (!x.outdated || !activeModels.has(x.model_id)))
      return disputed?.dispute_note || null
    })(),

    affiliate: affActive ? {
      code: affActive.code,
      url: affActive.url,
      discount: affActive.discount,
      no_user_discount: affActive.no_user_discount === true,   // 纯推荐链接，被推荐人无价格折扣
      reward_kind: affActive.reward_kind || null,              // 推荐奖励形态: usage_credit / cash_back / discount 等
      stackable: affActive.stackable,
      discount_note: affActive.discount_note,
      owner: affActive.owner,
      expires: affActive.expires || null,
    } : null,

    // 厂商名跳转目标：有邀请码用邀请码链接（带 source/折扣参数），否则用各家官方订阅直达页
    subscribe_url: (aff?.url) || SUBSCRIBE_URLS[p.vendor] || v.homepage || null,

    // 重置卡（ChatGPT 官方功能，几块钱一次可重置 5h/周窗口）
    // 标注：tokens_measured 是「标准情况」基础 cap，买重置卡可继续超额使用
    reset_card_available: p.reset_card_available ?? null,
    reset_card_note: p.reset_card_note || null,
    ratio_note: p.ratio_note || null,

    // DeepSeek V4 按量等价换算：月费 → 如果买 DS V4 官网原价能跑多少 tokens
    // 注意：此处按缓存命中 95% 写死，仅作兜底/快照。
    // 前端 LeaderBoard.vue 会按用户选择的 dsCacheRate 动态重算（默认 95%）。
    ds_v4_equivalent: (() => {
      const monthlyCny = pricing.currency === 'USD' && pricing.original_monthly
        ? pricing.original_monthly * USD_TO_CNY
        : pricing.original_monthly
      if (!monthlyCny) return null
      return {
        flash: Math.round(monthlyCny / dsV4MixedPricePerM('flash') * 1e6),
        pro:   Math.round(monthlyCny / dsV4MixedPricePerM('pro') * 1e6),
      }
    })(),

    source_urls: v.source_urls || p.source_urls || [],
    last_verified: p.last_verified || v.last_verified,
  }
})

const credLabel = { 3: 'high', 2: 'medium', 1: 'low', 0: 'none' }

// 排序：默认按厂商分组（同厂商连续）+ tier_multiplier 升序（1 < 4 < 20 < 60）
// 前端可重新按 credibility / price / tokens / value 排序，但默认保持厂商分组不拆散
// ⚠ 排序纪律铁律（见 SKILL.md 铁律 12）：
//   - 任何价格比较必须用 priceFor()（统一 CNY 口径），不准直接拿 original_monthly
//   - tier 排序必须用 tier_multiplier（数字），不准用 tierRank 字典（历史 bug：只认 lite/pro/max，
//     导致 kimi andante/moderato/allegretto/allegro 和 minimax plus/ultra 全部落到 || 99 乱序）
// 排序用价格：USD 套餐用折算价（CNY），统一口径对比
const priceFor = (p) => p.pricing.original_monthly_cny ?? p.pricing.original_monthly ?? 0
// 厂商排序优先级：openai 排最底（国外厂商），其他按字母序
const VENDOR_SORT_ORDER = { openai: 99, anthropic: 98 }
plans.sort((a, b) => {
  // 1. 厂商分组：openai 排最底，其他按字母序
  const aOrder = VENDOR_SORT_ORDER[a.vendor] ?? 0
  const bOrder = VENDOR_SORT_ORDER[b.vendor] ?? 0
  if (aOrder !== bOrder) return aOrder - bOrder
  if (a.vendor !== b.vendor) return a.vendor.localeCompare(b.vendor)
  // 2. 同厂商内按 tier_multiplier 升序（基础档 < 高档）
  const ma = a.tier_multiplier ?? 99
  const mb = b.tier_multiplier ?? 99
  if (ma !== mb) return ma - mb
  // 3. 同 tier 按 CNY 口径价格升序（USD 套餐走折算价）
  return priceFor(a) - priceFor(b)
})

// ── 情报模块：plan/vendor 级 intel 聚合（铁律 11：expires 过期自动摘）──
// 数据在哪定义哪出现：plan yml 写 intel:[]（挂具体套餐），vendor yml 写 intel:[]（厂商通用，如 Kimi 闲鱼代邀请）
const intelToday = new Date().toISOString().slice(0, 10)
const intelActive = (list) => (list || []).filter(it => !(it.expires && it.expires < intelToday))
// date = 登记时间(必填):没有登记时间的情报无法判断新鲜度,build 直接拒绝
const intelCheck = (list, where) => {
  for (const it of (list || [])) {
    if (!it.date) throw new Error(`[intel] ${where} 的一条情报缺 date(登记时间,格式 YYYY-MM-DD):${(it.text || '').slice(0, 40)}`)
  }
  return list
}
const intel = []
for (const [vid, v] of Object.entries(vendors)) {
  for (const it of intelActive(intelCheck(v.intel, `vendor:${vid}`))) {
    intel.push({ ...it, scope: 'vendor', vendor: vid, target: v.vendor_display || vid, plan_id: null })
  }
}
for (const p of plans) {
  const v = vendors[p.vendor] || {}
  const items = intelActive(intelCheck(p.intel, `plan:${p.plan_id}`))
  const vItems = intelActive(v.intel)   // 厂商级情报也算到该厂商每个套餐头上（💬 提示用）
  for (const it of items) {
    intel.push({ ...it, scope: 'plan', vendor: p.vendor, target: p.plan_name || p.plan_id, plan_id: p.plan_id })
  }
  p.intel_count = items.length + vItems.length
}

const out = {
  generated_at: new Date().toISOString(),
  plans_count: plans.length,
  vendors_count: Object.keys(vendors).length,
  credibility_label: credLabel,
  intel,
  plans,
}

mkdirSync(join(root, 'docs', '.vitepress'), { recursive: true })
writeFileSync(
  join(root, 'docs', '.vitepress', 'plans.json'),
  JSON.stringify(out, null, 2),
  'utf-8'
)
console.log(`✓ built ${plans.length} plans from ${Object.keys(vendors).length} vendors → docs/.vitepress/plans.json`)

// ── build 末尾自动更新 docs/index.md 的「最新更新」时间 ──
// 数据源:git log -1 --format=%cI . (最近 commit 提交时间, ISO 8601 with timezone)
// 替换 docs/index.md 的 actions 数组里 text: '📅 最新更新 YYYY-MM-DD HH:MM' 里的时间
// (为啥 commit 时间而不是文件 mtime? —— commit 时间反映榜单内容变更时刻, 更准)
try {
  const { execSync } = await import('node:child_process')
  const dateOut = execSync('git log -1 --format=%cI .', { cwd: root, encoding: 'utf-8' }).trim()
  // ISO 8601: 2026-08-01T14:30:00+08:00 → 截前 16 字符 = 2026-08-01T14:30, 再把 T 替空格
  const dateStr = dateOut.slice(0, 16).replace('T', ' ')
  const indexPath = join(root, 'docs', 'index.md')
  const indexText = readFileSync(indexPath, 'utf-8')
  const updated = indexText.replace(
    /(text: ['"]📅 最新更新 )[\d\s:-]+(['"])/,
    `$1${dateStr}$2`
  )
  if (updated !== indexText) {
    writeFileSync(indexPath, updated, 'utf-8')
    console.log(`✓ index.md 最新更新 → ${dateStr}`)
  } else {
    console.log(`✓ index.md 最新更新 (已是 ${dateStr})`)
  }
} catch (e) {
  // git 命令失败不阻塞 build（CI 无 git 时容错）
  console.warn('⚠ 自动更新 index.md 时间失败:', e.message.slice(0, 80))
}

// ── build 末尾自动跑 lint（铁律机械化检查）──
// 详见 .agents/skills/ledger-data-discipline/SKILL.md
// error 阻塞 build（exit 1），warning 只提示不阻塞
import { execSync } from 'node:child_process'
try {
  execSync('node scripts/lint-plans.mjs', { stdio: 'inherit', cwd: root })
} catch (e) {
  console.error('❌ lint 检查失败，build 中止（修复 lint error 后重试）')
  process.exit(1)
}
