// plans.json 数据纪律 lint（铁律机械化检查）
// 用法：node scripts/lint-plans.mjs
// 接入：build-plans.mjs 末尾自动跑，或 GitHub Action 单独跑
//
// 检查规则（对应 SKILL.md 铁律编号）：
//   铁律 3：B/亿 混用（字符串单位 / 零个数不对）
//   铁律 4：MiniMax/Kimi claimed 用 tokens，不准有 requests_official
//   铁律 6：月 ≤ 周 × 10（> 10× 必错）
//   铁律 9：tokens_measured 不准是 0（应该 null）
//   铁律 10：credibility 字段值合法（low/medium/high）
//   schema：必填字段不缺（plan_id / vendor / pricing.original_monthly / last_verified）
//
// 退出码：0 = 全过，1 = 有 error，2 = 有 warning 但无 error

import { readFileSync } from 'node:fs'
import { join, dirname } from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = dirname(fileURLToPath(import.meta.url))
const root = join(__dirname, '..')

const plansPath = join(root, 'docs', '.vitepress', 'plans.json')
const raw = JSON.parse(readFileSync(plansPath, 'utf-8'))
const plans = raw.plans || []

const errors = []
const warnings = []
const seenNoExpires = new Set()  // 铁律11：同邀请码去重 warn

function err(planId, rule, msg) {
  errors.push({ plan_id: planId || '(unknown)', rule, msg })
}
function warn(planId, rule, msg) {
  warnings.push({ plan_id: planId || '(unknown)', rule, msg })
}

// ── 铁律 3：B/亿/M/K 字符串单位检查（YAML 已解析为 number，如果原始是字符串会保留） ──
// 实际防御：月度 tokens 数值合理性（不可能 < 1000，也不应 > 1e13）
function checkUnitSanity(plan) {
  const t = plan.tokens || {}
  for (const win of ['h5', 'weekly', 'monthly']) {
    const v = t[win]
    if (v == null) continue
    if (typeof v !== 'number') {
      err(plan.plan_id, '铁律3', `tokens.${win}=${JSON.stringify(v)} 不是数字（可能 YAML 写成字符串单位如 "18B"）`)
      continue
    }
    if (!Number.isFinite(v)) {
      err(plan.plan_id, '铁律3', `tokens.${win}=${v} 不是有限数`)
      continue
    }
    // token 数量级合理性：< 1000 几乎不可能（任何套餐至少百万级），> 1e13 也不现实
    if (v > 0 && v < 1000) {
      err(plan.plan_id, '铁律3', `tokens.${win}=${v} 太小（< 1000），可能单位错（YAML 应写完整数字，如 1800000000 而不是 "18亿"）`)
    }
    if (v > 1e13) {
      warn(plan.plan_id, '铁律3', `tokens.${win}=${v} 异常大（> 1e13），确认是否单位错`)
    }
  }
}

// ── 铁律 4：MiniMax/Kimi 不准有 requests_official ──
function checkTokenVendorsNoRequests(plan) {
  if (plan.vendor !== 'minimax' && plan.vendor !== 'kimi') return
  const lim = plan.limits || {}
  for (const win of ['window_5h', 'window_weekly', 'window_monthly']) {
    const req = lim[win]?.requests_official
    if (req != null) {
      err(plan.plan_id, '铁律4', `${plan.vendor} 不公布请求次数，但 limits.${win}.requests_official=${req}（MiniMax/Kimi 只用 tokens_official_claimed）`)
    }
  }
  // claimed.unit 应该是 tokens
  if (plan.claimed?.unit && plan.claimed.unit !== 'tokens') {
    err(plan.plan_id, '铁律4', `${plan.vendor} claimed.unit="${plan.claimed.unit}"，应该是 "tokens"`)
  }
}

// ── 铁律 6：月 ≤ 周 × 10 ──
function checkMonthlyWeeklyRatio(plan) {
  const t = plan.tokens || {}
  if (t.weekly == null || t.monthly == null) return
  if (t.monthly === 0 || t.weekly === 0) return
  // Kimi 月度无限，跳过
  if (plan.limits?.window_monthly?.is_unlimited) return
  const ratio = t.monthly / t.weekly
  if (ratio > 10) {
    err(plan.plan_id, '铁律6', `月度=${t.monthly} / 周度=${t.weekly} = ${ratio.toFixed(1)}× （> 10× 必错，查 B/亿 单位）`)
  } else if (ratio > 6) {
    warn(plan.plan_id, '铁律6', `月度=${t.monthly} / 周度=${t.weekly} = ${ratio.toFixed(1)}× （正常 2-5×，> 6× 警惕 estimate 或限时活动）`)
  }
}

// ── 铁律 9：tokens_measured 不准是 0 ──
function checkNoZeroMeasured(plan) {
  const t = plan.tokens || {}
  for (const win of ['h5', 'weekly', 'monthly']) {
    if (t[win] === 0) {
      err(plan.plan_id, '铁律9', `tokens.${win}=0（应该是 null，0 会被前端当"实测为 0"展示）`)
    }
  }
}

// ── 铁律 12：USD 套餐必须有 CNY 折算（防 USD/CNY 混淆历史 bug 回归）──
// 历史 bug：早期排序直接拿 original_monthly 比较，USD 72 跟 CNY 99 比，跨厂商排序全错
// 现在 priceFor() 用 original_monthly_cny 兜底，lint 必须保证 USD 套餐该字段存在
function checkUsdHasCnyConversion(plan) {
  const p = plan.pricing || {}
  if (p.currency !== 'USD') return
  if (p.original_monthly != null && p.original_monthly_in_cny == null) {
    err(plan.plan_id, '铁律12', `USD 套餐 original_monthly=${p.original_monthly} 但缺 original_monthly_in_cny（USD 必须有 CNY 折算，否则跨厂商价格排序错）`)
  }
  // is_usd 标志必须跟 currency 一致
  if (p.is_usd !== true) {
    err(plan.plan_id, '铁律12', `currency=USD 但 is_usd=${p.is_usd}（必须 is_usd=true）`)
  }
}

// ── 铁律 13：tier_multiplier 必须存在 ──
// 历史 bug：tierRank 字典只认 lite/pro/max，kimi/minimax 档位全乱
// 改用 tier_multiplier 数字字段后，每个套餐都必须有这个字段（除非新增厂商没配 TIER_RATIOS）
function checkTierMultiplier(plan) {
  const m = plan.tier_multiplier
  if (m == null) {
    err(plan.plan_id, '铁律13', `缺 tier_multiplier 字段（vendor 没配 TIER_RATIOS？vendor=${plan.vendor} tier=${plan.plan_tier}）`)
    return
  }
  if (typeof m !== 'number' || m <= 0) {
    err(plan.plan_id, '铁律13', `tier_multiplier=${m} 不合法（应是 > 0 的数字，最低档=1）`)
  }
}

// ── 铁律 16：Kimi 官方不公开绝对 token，tokens_official_claimed 必须 null ──
// 事故：上一个 AI 编造 Kimi 4 档 tokens_official_claimed（50M/200M/1000M/3000M）
// Kimi 官方只标倍数（1×/4×/20×/60×），从不公开绝对 token 数
function checkNoFakeOfficialClaimed(plan) {
  if (plan.vendor !== 'kimi') return
  // plans.json 里 claimed.weekly 来自 build 的 tokens_official_claimed
  // build-plans.mjs 第 326 行：isTokenVendor 时 claimed.weekly = lim.window_weekly?.tokens_official_claimed
  const claimed = plan.claimed || {}
  for (const win of ['h5', 'weekly', 'monthly']) {
    if (claimed[win] != null) {
      err(plan.plan_id, '铁律16', `Kimi 官方不公开绝对 token 数（只标倍数），但 claimed.${win}=${claimed[win]}（疑似编造的「官方标称」）`)
    }
  }
}

// ── 铁律 10：measurements.credibility 值合法 ──
// 注：build 输出里 measurements_credibility_max 是数字（0/1/2/3），这里检查 plan-level
function checkCredibility(plan) {
  const cred = plan.measurements_credibility_max
  if (cred == null) return
  if (![0, 1, 2, 3].includes(cred)) {
    err(plan.plan_id, '铁律10', `measurements_credibility_max=${cred} 不合法（应为 0/1/2/3）`)
  }
  // disputed 但 credibility 是 high（3），矛盾
  if (plan.measurements_disputed && cred === 3) {
    warn(plan.plan_id, '铁律10', `数据 disputed 但 credibility=high，矛盾（disputed 应该降低可信度）`)
  }
}

// ── schema：必填字段 ──
function checkRequiredFields(plan) {
  if (!plan.plan_id) err(plan.plan_id, 'schema', '缺 plan_id')
  if (!plan.vendor) err(plan.plan_id, 'schema', '缺 vendor')
  if (!plan.plan_name) err(plan.plan_id, 'schema', '缺 plan_name')
  if (!plan.plan_tier) err(plan.plan_id, 'schema', '缺 plan_tier')
  if (!plan.status) err(plan.plan_id, 'schema', '缺 status')
  if (!plan.last_verified) err(plan.plan_id, 'schema', '缺 last_verified')
  const p = plan.pricing || {}
  if (p.original_monthly == null && p.intro_monthly == null) {
    err(plan.plan_id, 'schema', 'pricing 缺 original_monthly 和 intro_monthly（至少要有一个）')
  }
  if (!['CNY', 'USD'].includes(p.currency)) {
    err(plan.plan_id, 'schema', `pricing.currency="${p.currency}" 不合法（应为 CNY 或 USD）`)
  }
  if (!['active', 'deprecated'].includes(plan.status)) {
    warn(plan.plan_id, 'schema', `status="${plan.status}" 不是 active/deprecated`)
  }
}

// ── 铁律 7：邀请码字段完整性 ──
function checkAffiliateSchema(plan) {
  const aff = plan.affiliate
  if (aff == null) return  // null 是合法的（无邀请码）
  const pid = plan.plan_id || '(unknown)'
  const required = ['code', 'url', 'discount']
  for (const f of required) {
    if (aff[f] == null) {
      err(pid, '铁律7', `affiliate 缺字段 ${f}（必填：code/url/discount）`)
    }
  }
  if (aff.discount != null) {
    if (typeof aff.discount !== 'number' || aff.discount <= 0 || aff.discount >= 1) {
      err(pid, '铁律7', `affiliate.discount=${aff.discount} 不合法（应是 0-1 之间的小数，如 0.95 = 95折）`)
    }
  }
  // 有 discount 但 stackable 未定义 → warning
  if (aff.discount != null && aff.stackable == null) {
    warn(pid, '铁律7', `affiliate 有 discount 但缺 stackable（明确写 true/false）`)
  }
  // 有邀请码但缺 expires（铁律 11）→ warning
  // 同 code 只 warn 一次（避免同厂商多套餐重复 warn）
  if (aff.code && aff.expires == null && !seenNoExpires.has(aff.code)) {
    seenNoExpires.add(aff.code)
    warn(pid, '铁律11', `affiliate code=${aff.code} expires=null（确认：是限时活动？还是永久？限时必须填日期；永久请显式写 expires: null 并在 vendor.yml 注释说明）`)
  }
}

// ── 铁律 8：原价 vs 首单价不能完全相同 ──
function checkOriginalVsIntro(plan) {
  const p = plan.pricing || {}
  if (p.original_monthly != null && p.intro_monthly != null) {
    if (p.original_monthly === p.intro_monthly) {
      warn(plan.plan_id, '铁律8', `original_monthly=${p.original_monthly} 跟 intro_monthly 相同（首单价应低于原价，否则不该填 intro_*）`)
    }
    if (p.intro_monthly > p.original_monthly) {
      err(plan.plan_id, '铁律8', `intro_monthly=${p.intro_monthly} > original_monthly=${p.original_monthly}（首单价比原价贵，逻辑错）`)
    }
  }
}

// ── 跑全部检查 ──
for (const plan of plans) {
  checkUnitSanity(plan)
  checkTokenVendorsNoRequests(plan)
  checkMonthlyWeeklyRatio(plan)
  checkNoZeroMeasured(plan)
  checkUsdHasCnyConversion(plan)   // 铁律 12
  checkTierMultiplier(plan)         // 铁律 13
  checkNoFakeOfficialClaimed(plan)  // 铁律 16
  checkCredibility(plan)
  checkRequiredFields(plan)
  checkAffiliateSchema(plan)
  checkOriginalVsIntro(plan)
}

// ── 输出 ──
console.log('')
console.log('═══ Ledger Data Lint ═══')
console.log(`  检查 ${plans.length} 个套餐`)
console.log(`  ${errors.length} errors / ${warnings.length} warnings`)
console.log('')

if (warnings.length > 0) {
  console.log('── warnings ──')
  for (const w of warnings) {
    console.log(`  ⚠ [${w.plan_id}] ${w.rule}: ${w.msg}`)
  }
  console.log('')
}

if (errors.length > 0) {
  console.log('── errors ──')
  for (const e of errors) {
    console.log(`  ✗ [${e.plan_id}] ${e.rule}: ${e.msg}`)
  }
  console.log('')
  console.log(`❌ ${errors.length} 个 error，必须修复后再 build`)
  process.exit(1)
}

if (warnings.length > 0) {
  console.log(`⚠ ${warnings.length} 个 warning，建议核查（不阻塞 build）`)
  process.exit(0)  // warning 不阻塞
}

console.log('✓ 全部通过')
process.exit(0)
