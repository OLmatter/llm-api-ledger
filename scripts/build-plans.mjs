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

// ── DeepSeek V4 按量等价换算 ──
// 把套餐月费换算成「如果买 DS V4 非高峰期按量，能跑多少 tokens」
// 用真实编程比例（non-cache input 9.4% / output 1.2% / cache read 89.4%）
// DS V4 非高峰期定价（元/百万 tokens，来源 GCMP deepseek.json）
// 两个版本：Flash（便宜）和 Pro（贵 3 倍）
const DS_V4_PRICES = {
  flash: { input: 1.0, output: 2.0, cache_read: 0.02 },
  pro:   { input: 3.0, output: 6.0, cache_read: 0.025 },
}
// 真实编程比例（来源：用户 MiniMax 实际使用数据）
const CODING_RATIO = { input: 0.094, output: 0.012, cache_read: 0.894 }
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
}

// 各厂商不同 tier 的倍率（基于官方产品定义）
// volcengine: Lite:Pro = 1:5
// zhipu: Lite:Pro:Max = 1:5:20
// minimax: Plus:Max:Ultra = 1:3:11.8
// kimi: Andante:Moderato:Allegretto:Allegro = 1:4:20:60
// zai: Lite:Pro:Max = 1:5:20（跟国内智谱完全对齐）
const TIER_RATIOS = {
  volcengine: { lite: 1, pro: 5 },
  zhipu:      { lite: 1, pro: 5, max: 20 },
  minimax:    { plus: 1, max: 3, ultra: 11.8 },
  kimi:       { andante: 1, moderato: 4, allegretto: 20, allegro: 60 },
  zai:        { lite: 1, pro: 5, max: 20 },
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
  const direct = {
    h5: lim.window_5h?.tokens_measured || null,
    weekly: lim.window_weekly?.tokens_measured || null,
    monthly: lim.window_monthly?.tokens_measured || null,
    monthly_estimated: lim.window_monthly?.monthly_estimated || false,
  }
  // Kimi 特殊：周可能直接从 measurements 拿（Allegretto 社区实测 690M）
  if (direct.weekly == null) {
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
  // 月度：Kimi 无月度（monthly_unlimited）；其他按周×ratio
  if (direct.monthly == null && !ratio?.monthly_unlimited) {
    if (direct.weekly && ratio?.monthly_to_weekly) {
      direct.monthly = Math.round(direct.weekly * ratio.monthly_to_weekly)
      direct.monthly_estimated = ratio.monthly_is_estimate
      if (!direct.monthly_source) direct.monthly_source = 'inferred_from_weekly'
    }
  }
  // 从 measurements 反推（火山 Pro 月度 / MiniMax Max 5h burn 测试）
  if (direct.h5 == null && direct.monthly == null && !ratio?.monthly_unlimited) {
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
  if (affActive?.stackable && affActive.discount) {
    const base = pricing.intro_monthly ?? pricing.original_monthly
    if (base != null) {
      intro_with_aff = Math.round(base * affActive.discount * 100) / 100
      // 统一改名「用邀请码」（之前是「首单+邀请码」/「首单 9 折」，不直接）
      // 紧迫感来自「用」字 + 红色按钮 + 损失对照，不在 tag 文字本身
      intro_tag = '用邀请码'
    }
  } else if (pricing.intro_monthly) {
    intro_with_aff = pricing.intro_monthly
    intro_tag = '用邀请码'
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
  const standard_yearly = pricing.original_yearly || pricing.intro_yearly || pricing.yearly_total || null
  // 年付邀请码叠加：standard_yearly × discount
  const yearly_with_aff = (affActive?.stackable && affActive.discount && standard_yearly)
    ? Math.round(standard_yearly * affActive.discount * 100) / 100
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
  if (tokens.weekly == null) {
    const inferred = inferTokensFromSibling(p, allPlans)
    if (inferred) tokens = inferred
  }

  return {
    plan_id: p.plan_id,
    vendor: p.vendor,
    vendor_display: v.vendor_display || p.vendor,
    brand_color: v.brand_color || null,
    plan_name: p.plan_name,
    plan_tier: p.plan_tier,
    status: p.status,
    // 主力模型（榜单对比基准；vendor 级共享）
    primary_model: v.shared_features?.primary_model || null,

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
      intro_tag: intro_tag,
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
    // 火山/智谱：次数（requests_official）
    // MiniMax/Kimi：tokens（官方公布 token 总量）
    claimed: (() => {
      const lim = p.limits || {}
      const isTokenVendor = p.vendor === 'minimax' || p.vendor === 'kimi'
      if (isTokenVendor) {
        return {
          unit: 'tokens',
          h5: null,
          weekly: lim.window_weekly?.tokens_official_claimed || null,
          monthly: lim.window_monthly?.tokens_official_claimed || null,
        }
      }
      // 火山/智谱：次数
      return {
        unit: '次',
        h5: lim.window_5h?.requests_official ?? null,
        weekly: lim.window_weekly?.requests_official ?? null,
        monthly: lim.window_monthly?.requests_official ?? null,
      }
    })(),
    claimed_unit: (p.vendor === 'minimax' || p.vendor === 'kimi') ? 'tokens' : '次',

    // 实测 tokens（反推到 100% 满额）
    tokens: {
      h5: tokens.h5,
      weekly: tokens.weekly,
      monthly: tokens.monthly,
      monthly_is_estimate: tokens.monthly_estimated,
      monthly_source: tokens.monthly_source || null,
      // ZCode 专属优惠（智谱 + 智谱海外版 Z.AI 都支持，全周期 ×1.5 等效额度）
      zcode_h5: tokens.h5 ? Math.round(tokens.h5 * 1.5) : null,
      zcode_weekly: tokens.weekly ? Math.round(tokens.weekly * 1.5) : null,
      zcode_monthly: tokens.monthly ? Math.round(tokens.monthly * 1.5) : null,
      zcode_applicable: ['zhipu', 'zai'].includes(p.vendor),
      // 实测周聚合说明(任意形式的跨档/多源 measurement 的 notes,用于 hover tooltip)
      // 优先级:aggregate_median(多源聚合) > vendor_sibling_inferred(跨境反推) > community_report 带 source_plan(同档反推)
      weekly_aggregate_note: ((p.measurements || []).find(m => m.source_kind === 'aggregate_median')?.notes)
        ?? ((p.measurements || []).find(m => m.source_kind === 'vendor_sibling_inferred')?.notes)
        ?? ((p.measurements || []).find(m => m.source_plan && m.source_weekly_tokens)?.notes)
        ?? null,
      // 数据争议标记：disputed=true 时给前端显示红色 ⚠
      weekly_disputed: (p.measurements || []).some(m => m.disputed === true),
      dispute_note: ((p.measurements || []).find(m => m.disputed === true)?.dispute_note) || null,
    },

    measurements_count: (p.measurements || []).length,
    measurements_credibility_max: (p.measurements || []).reduce(
      (m, x) => {
        const rank = { low: 1, medium: 2, high: 3 }
        return Math.max(m, rank[x.credibility] || 0)
      }, 0
    ),
    // 数据争议标记：任一 measurement 标 disputed=true，整个 plan 标争议
    measurements_disputed: (p.measurements || []).some(x => x.disputed === true),
    measurements_dispute_note: (() => {
      const disputed = (p.measurements || []).find(x => x.disputed === true)
      return disputed?.dispute_note || null
    })(),

    affiliate: affActive ? {
      code: affActive.code,
      url: affActive.url,
      discount: affActive.discount,
      stackable: affActive.stackable,
      discount_note: affActive.discount_note,
      owner: affActive.owner,
      expires: affActive.expires || null,
    } : null,

    // 厂商名跳转目标：有邀请码用邀请码链接（带 source/折扣参数），否则用各家官方订阅直达页
    subscribe_url: (aff?.url) || SUBSCRIBE_URLS[p.vendor] || v.homepage || null,

    // DeepSeek V4 按量等价换算：月费 → 如果买 DS V4 非高峰期能跑多少 tokens
    // 两个版本：Flash（便宜）和 Pro（贵 3 倍）
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

// 排序：默认按厂商分组（同厂商连续）+ tier 倍率升序（Lite < Pro < Max）
// 前端可重新按 credibility / price 排序，但默认保持厂商分组不拆散
const tierRank = { lite: 1, 'team-lite': 1, pro: 2, 'team-pro': 2, max: 3 }
// 排序用价格：USD 套餐用折算价（CNY），统一口径对比
const priceFor = (p) => p.pricing.original_monthly_cny ?? p.pricing.original_monthly ?? 0
plans.sort((a, b) => {
  // 1. 厂商分组（按 vendor 字母序，保证同厂商连续）
  if (a.vendor !== b.vendor) return a.vendor.localeCompare(b.vendor)
  // 2. 同厂商内按 tier 升序（Lite → Pro → Max）
  const ta = tierRank[a.plan_tier] || 99
  const tb = tierRank[b.plan_tier] || 99
  if (ta !== tb) return ta - tb
  // 3. 同 tier 按 CNY 口径价格升序（USD 套餐走折算价）
  return priceFor(a) - priceFor(b)
})

const out = {
  generated_at: new Date().toISOString(),
  plans_count: plans.length,
  vendors_count: Object.keys(vendors).length,
  credibility_label: credLabel,
  plans,
}

mkdirSync(join(root, 'docs', '.vitepress'), { recursive: true })
writeFileSync(
  join(root, 'docs', '.vitepress', 'plans.json'),
  JSON.stringify(out, null, 2),
  'utf-8'
)
console.log(`✓ built ${plans.length} plans from ${Object.keys(vendors).length} vendors → docs/.vitepress/plans.json`)
