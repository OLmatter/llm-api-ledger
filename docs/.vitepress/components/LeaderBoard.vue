<script setup>
import { ref, computed } from 'vue'
import plansData from '../plans.json'

const plans = ref(plansData.plans)

// 排序选项
// vendor（默认，厂商分组）/ credibility / price_asc / price_desc / tokens / value
// 除 vendor 外，其他都是跨厂商排（不保留厂商分组）
const sortKey = ref('vendor')
function setSort(k) { sortKey.value = k }

// 排序用的"用量"：优先 monthly（无限流量如 Kimi 月度算 Infinity 排最后）
function tokensFor(plan) {
  const m = plan.tokens?.monthly
  if (m == null) return -1  // 没数据排到有数据的后面
  return m
}
// 性价比 = 周用量 / 月费（CNY 口径）。值越大越划算
// 用 weekly 不用 monthly：Kimi 月度无限，用 weekly 才有可比性
function valueFor(plan) {
  const w = plan.tokens?.weekly
  const price = priceFor(plan)
  if (w == null || !isFinite(price) || price === 0) return -1
  return w / price
}

const sortedPlans = computed(() => {
  const arr = [...plans.value]
  const k = sortKey.value
  if (k === 'vendor') {
    // 厂商分组 + tier_multiplier 升序（用数字字段，不准用 tierRank 字典——
    // 历史 bug：tierRank 只认 lite/pro/max，kimi/minimax 档位全乱）
    arr.sort((a, b) => {
      if (a.vendor !== b.vendor) return a.vendor.localeCompare(b.vendor)
      const ma = a.tier_multiplier ?? 99
      const mb = b.tier_multiplier ?? 99
      if (ma !== mb) return ma - mb
      return priceFor(a) - priceFor(b)
    })
  } else if (k === 'credibility') {
    // 跨厂商：按可信度降序，平手按价格升序
    arr.sort((a, b) => b.measurements_credibility_max - a.measurements_credibility_max
      || priceFor(a) - priceFor(b))
  } else if (k === 'price_asc') {
    arr.sort((a, b) => priceFor(a) - priceFor(b))
  } else if (k === 'price_desc') {
    arr.sort((a, b) => priceFor(b) - priceFor(a))
  } else if (k === 'tokens') {
    // 跨厂商：按月度用量降序，没数据排后面
    arr.sort((a, b) => tokensFor(b) - tokensFor(a))
  } else if (k === 'value') {
    // 跨厂商：按性价比（周用量/月费）降序，没数据排后面
    arr.sort((a, b) => valueFor(b) - valueFor(a))
  }
  return arr
})

// 同厂商分组（用于厂商列 + 邀请码列 rowspan 合并）
// 按排序后的顺序，连续相同 vendor 合并厂商列；
// 连续相同 vendor + 同邀请码 合并邀请码列。
const groupedRows = computed(() => {
  const rows = []
  const sorted = sortedPlans.value
  for (let i = 0; i < sorted.length; i++) {
    const p = sorted[i]
    const prev = i > 0 ? sorted[i - 1] : null
    const sameVendorAsPrev = prev && prev.vendor === p.vendor
    const sameAffAsPrev = prev
      && prev.vendor === p.vendor
      && (prev.affiliate?.code || null) === (p.affiliate?.code || null)
    // 厂商列 rowspan
    const isVendorStart = !sameVendorAsPrev
    let vendorSpan = 1
    if (isVendorStart) {
      for (let j = i + 1; j < sorted.length; j++) {
        if (sorted[j].vendor === p.vendor) vendorSpan++
        else break
      }
    }
    // 邀请码列 rowspan
    const isAffStart = !sameAffAsPrev
    let affSpan = 1
    if (isAffStart) {
      for (let j = i + 1; j < sorted.length; j++) {
        const next = sorted[j]
        if (next.vendor === p.vendor
            && (next.affiliate?.code || null) === (p.affiliate?.code || null)) {
          affSpan++
        } else break
      }
    }
    rows.push({ plan: p, isVendorStart, vendorSpan, isAffStart, affSpan })
  }
  return rows
})

// 邀请码复制（复制整条链接）
const copiedId = ref(null)
async function copyAffiliate(plan) {
  if (!plan.affiliate) return
  const text = plan.affiliate.url
  try {
    await navigator.clipboard.writeText(text)
  } catch (e) {
    const ta = document.createElement('textarea')
    ta.value = text
    document.body.appendChild(ta)
    ta.select()
    document.execCommand('copy')
    document.body.removeChild(ta)
  }
  copiedId.value = plan.plan_id
  setTimeout(() => { copiedId.value = null }, 1500)
}

function fmtPrice(plan, p) {
  if (p == null) return '—'
  return sym(plan) + p
}

// 货币符号：根据当前 currencyUnit + plan.pricing.currency 切换
// cny 模式下统一用 ¥；native 模式下 USD 用 $，CNY 用 ¥
function sym(plan) {
  return currencyUnit.value === 'cny' || plan.pricing.currency === 'CNY'
    ? '¥' : '$'
}

// 根据当前 currencyUnit 取价格字段
// native 模式：原值；cny 模式：USD 套餐用 _in_cny 字段（已有 fx 折算），CNY 套餐不变
function pickPrice(plan, field) {
  if (currencyUnit.value === 'cny' && plan.pricing.is_usd) {
    return plan.pricing[field + '_in_cny']
  }
  return plan.pricing[field]
}

// 排序用的"价格"统一口径：USD 套餐用 build-plans 算好的折算价（CNY），CNY 套餐直接用原价
// 没有价格时返回 Infinity（排到最后）
function priceFor(plan) {
  return plan.pricing.original_monthly_cny
    ?? plan.pricing.original_monthly
    ?? Infinity
}

// 模型 tag 落点：每个有数字的列独立显示（v-if 在 template 里直接判断 tokens.*.!= null）
// 不需要单独 helper，函数定义已删除

function fmtReq(n) {
  if (n == null) return '—'
  if (n >= 10000) return (n / 10000).toFixed(n % 10000 === 0 ? 0 : 1) + '万'
  return String(n)
}

// 格式化折扣：0.95 → "95折"，0.9 → "9折"
function fmtDiscount(d) {
  if (d == null) return ''
  // 中国习惯：95折 = 0.95，9折 = 0.9
  // 0.95 → 95，0.9 → 90 → 但 9折应该显示 9 不是 90
  const pct = Math.round(d * 100)
  if (pct % 10 === 0) return (pct / 10).toString() + '折'
  return pct.toString() + '折'
}

// 格式化宣称用量：按 plan.claimed_unit 自动选择格式
// unit='次' → 1200 → "1200"，9000 → "9000"，45000 → "4.5万"
// unit='tokens' → 用 fmtTokens
function fmtClaimed(plan, n) {
  if (n == null) return '—'
  if (plan.claimed_unit === 'tokens') return fmtTokens(n)
  // 次数格式
  if (n >= 10000) return (n / 10000).toFixed(n % 10000 === 0 ? 0 : 1) + '万'
  return String(n)
}

// 格式化 token 数：893800000 → "894M"，1234567 → "1.2M"
// 单位由 tokenUnit 控制：'m_b' 默认(M/B/K) | 'yi' 中文习惯(亿/万/K)
const tokenUnit = ref('m_b')  // 'm_b' | 'yi'
function fmtTokens(n) {
  if (n == null || n === 0) return '—'
  return tokenUnit.value === 'yi' ? fmtTokensYi(n) : fmtTokensMB(n)
}

// 货币单位：'native' 默认（套餐本身货币）| 'cny' 统一折算成人民币
// cny 模式下，USD 套餐按汇率折算显示 ¥；CNY 套餐保持不变
const currencyUnit = ref('native')  // 'native' | 'cny'
const showDSEquiv = ref(false)      // DS V4 按量等价换算开关
const dsVariant = ref('flash')      // 'flash' | 'pro'
const dsCacheRate = ref(0.95)       // DS V4 等价换算的缓存命中率（默认 95%）
// DS V4 官网原价（元/百万 tokens）
const DS_V4_PRICES = {
  flash: { input: 1.0, output: 2.0, cache_read: 0.02 },
  pro:   { input: 3.0, output: 6.0, cache_read: 0.025 },
}
// 剩余非缓存部分按 input:output = 8.8:1.2 分（来自 MiniMax 实测分布）
function dsV4MixedPricePerM(variant, cacheRate) {
  const p = DS_V4_PRICES[variant]
  const nonCache = 1 - cacheRate
  const inRatio = nonCache * 0.88
  const outRatio = nonCache * 0.12
  return inRatio * p.input + outRatio * p.output + cacheRate * p.cache_read
}
// 前端动态计算某套餐的 DS V4 等价 tokens（按当前 dsCacheRate）
function dsEquivForPlan(plan) {
  const monthlyCny = plan.pricing.original_monthly_in_cny
    ?? (plan.pricing.currency === 'USD' && plan.pricing.original_monthly
        ? plan.pricing.original_monthly * (plan.pricing.fx_rate || 7.15)
        : plan.pricing.original_monthly)
  if (!monthlyCny) return null
  const price = dsV4MixedPricePerM(dsVariant.value, dsCacheRate.value)
  return Math.round(monthlyCny / price * 1e6)
}
const dsCacheOptions = [0.5, 0.7, 0.85, 0.95, 0.99]
function fmtTokensMB(n) {
  const abs = Math.abs(n)
  if (abs >= 1e9) return (n / 1e9).toFixed(2) + 'B'
  if (abs >= 1e6) return (n / 1e6).toFixed(abs >= 1e8 ? 0 : 1) + 'M'
  if (abs >= 1e3) return (n / 1e3).toFixed(0) + 'K'
  return String(n)
}
function fmtTokensYi(n) {
  // 中文习惯：>= 1 亿用亿，< 1 亿用万，< 1 万用 K
  const abs = Math.abs(n)
  if (abs >= 1e8) {
    const yi = n / 1e8
    if (abs >= 1e10) return yi.toFixed(0) + '亿'        // >= 100 亿
    if (abs >= 1e9)  return yi.toFixed(1) + '亿'        // 10 - 100 亿
    return yi.toFixed(2) + '亿'                          // 1 - 10 亿
  }
  if (abs >= 1e4) {
    const wan = n / 1e4
    if (abs >= 1e6) return wan.toFixed(0) + '万'        // >= 100 万
    return wan.toFixed(1) + '万'                          // 1 - 100 万
  }
  if (abs >= 1e3) return (n / 1e3).toFixed(0) + 'K'     // < 1 万
  return String(n)
}
</script>

<template>
  <div class="ledger">
    <!-- 排序条 -->
    <div class="sort-bar">
      <span class="sort-label">排序：</span>
      <button
        v-for="opt in [
          { k: 'vendor', label: '厂商分组', title: '按厂商字母序 + tier 倍率升序（默认，保留厂商分组视觉）' },
          { k: 'price_asc', label: '价格↑', title: '按月费升序，跨厂商（USD 已折算 ¥）' },
          { k: 'price_desc', label: '价格↓', title: '按月费降序，跨厂商（USD 已折算 ¥）' },
          { k: 'tokens', label: '用量', title: '按实测月度用量降序，跨厂商（没数据的排最后）' },
          { k: 'value', label: '性价比', title: '按「周用量 ÷ 月费」降序，跨厂商（数值越大越划算）' },
          { k: 'credibility', label: '可信度', title: '按实测可信度降序（high > medium > low > none），跨厂商' },
        ]"
        :key="opt.k"
        :class="['sort-btn', { active: sortKey === opt.k }]"
        :title="opt.title"
        @click="setSort(opt.k)"
      >{{ opt.label }}</button>
      <span class="bar-divider">·</span>
      <span class="sort-label">单位：</span>
      <button
        :class="['sort-btn', { active: tokenUnit === 'm_b' }]"
        @click="tokenUnit = 'm_b'"
        title="国际单位：M (百万) / B (十亿)"
      >M/B</button>
      <button
        :class="['sort-btn', { active: tokenUnit === 'yi' }]"
        @click="tokenUnit = 'yi'"
        title="中文单位：亿 / 万 / K"
      >亿</button>
      <span class="divider">|</span>
      <button
        :class="['sort-btn', { active: currencyUnit === 'native' }]"
        @click="currencyUnit = 'native'"
        title="按套餐原货币显示（CNY 套餐 ¥，USD 套餐 \$）"
      >原币</button>
      <button
        :class="['sort-btn', { active: currencyUnit === 'cny' }]"
        @click="currencyUnit = 'cny'"
        :title="`统一折算成人民币（USD 按 ${plans.plans && plans.length > 0 ? (plans[0].pricing.fx_rate || 7.15) : 7.15} 汇率）`"
      >¥统</button>
      <span class="divider">|</span>
      <button
        :class="['sort-btn', { active: showDSEquiv }]"
        @click="dsVariant = 'flash'; showDSEquiv = !showDSEquiv"
        title="DeepSeek V4 Flash 非高峰期按量等价（最便宜）"
      >DS Flash</button>
      <button
        :class="['sort-btn', { active: showDSEquiv && dsVariant === 'pro' }]"
        @click="dsVariant = 'pro'; showDSEquiv = true"
        title="DeepSeek V4 Pro 非高峰期按量等价（3 倍价）"
      >DS Pro</button>
      <span v-if="showDSEquiv" class="bar-divider">·</span>
      <span v-if="showDSEquiv" class="sort-label">缓存命中：</span>
      <template v-if="showDSEquiv">
        <button
          v-for="opt in dsCacheOptions"
          :key="opt"
          :class="['sort-btn', { active: Math.abs(dsCacheRate - opt) < 0.001 }]"
          @click="dsCacheRate = opt"
          :title="`缓存命中率 ${Math.round(opt*100)}%：越高 DS 等价越大（缓存 ¥0.02/M 几乎免费）`"
        >{{ Math.round(opt*100) }}%</button>
      </template>
      <span class="count">{{ plans.length }} 个套餐 · {{ plansData.vendors_count }} 个厂商</span>
    </div>

    <!-- 对比表 -->
    <div class="table-wrap">
      <table>
        <thead>
          <!-- 宣称用量（厂商公布，单位跟随厂商）+ 实测用量（统一 tokens）-->
          <tr>
            <th rowspan="2">厂商</th>
            <th rowspan="2">套餐</th>
            <th rowspan="2" class="num">包月</th>
            <th rowspan="2" class="num">包季</th>
            <th rowspan="2" class="num">包年</th>
            <th colspan="3" class="super-header">宣称用量 <span class="unit-inline">（厂商公布）</span></th>
            <th colspan="3" class="super-header alt">实测用量 <span class="unit-inline">（tokens）</span></th>
          </tr>
          <tr>
            <th class="num">5h</th>
            <th class="num">周</th>
            <th class="num">月</th>
            <th class="num">5h</th>
            <th class="num">周</th>
            <th class="num">月</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in groupedRows" :key="row.plan.plan_id">
            <!-- 厂商（同厂商合并 rowspan）+ 内嵌邀请码（同厂商同码也合并）-->
            <td v-if="row.isVendorStart" :rowspan="row.vendorSpan" class="vendor-cell">
              <a
                v-if="row.plan.subscribe_url"
                :href="row.plan.subscribe_url"
                target="_blank"
                rel="noopener noreferrer"
                class="vendor-link"
                :title="row.plan.subscribe_url"
              >
                <span class="vendor-dot" :style="{ background: row.plan.brand_color || '#86868b' }"></span>
                {{ row.plan.vendor_display }}
                <svg class="vendor-ext" viewBox="0 0 12 12" aria-hidden="true">
                  <path d="M4.5 2.5h-2a1 1 0 0 0-1 1v6a1 1 0 0 0 1 1h6a1 1 0 0 0 1-1v-2M7 2h3v3M10 2 5.5 6.5" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
                </svg>
              </a>
              <template v-else>
                <span class="vendor-dot" :style="{ background: row.plan.brand_color || '#86868b' }"></span>
                {{ row.plan.vendor_display }}
              </template>
              <!-- 邀请码（嵌在厂商下方，小字，仅 isAffStart 行渲染）-->
              <div v-if="row.isAffStart" class="vendor-aff">
                <template v-if="row.plan.affiliate">
                  <button
                    class="aff-btn-mini"
                    :class="{ copied: copiedId === row.plan.plan_id }"
                    @click="copyAffiliate(row.plan)"
                    :title="`复制邀请链接（${fmtDiscount(row.plan.affiliate.discount)}）`"
                  >
                    <span>{{ copiedId === row.plan.plan_id ? '✓' : '🎁' }} 复制邀请码 {{ fmtDiscount(row.plan.affiliate.discount) }}</span>
                  </button>
                </template>
                <span v-else class="aff-none">无邀请码</span>
              </div>
            </td>

            <!-- 套餐 -->
            <td class="plan-cell">
              <div class="plan-name">{{ row.plan.plan_name }}</div>
              <div class="plan-meta">
                <span v-if="row.plan.tier_multiplier != null" :class="['tier-mult', { 'is-base': row.plan.tier_multiplier === 1 }]" :title="`本档用量 = 同厂商最低档 × ${row.plan.tier_multiplier}（基于厂商官方产品定义）`">{{ row.plan.tier_multiplier === 1 ? '基础档' : '×' + row.plan.tier_multiplier }}</span>
                <span class="tier-name">{{ row.plan.plan_tier }}</span>
              </div>
            </td>

            <!-- 包月：原价 + 用邀请码子行 -->
            <td class="num">
              {{ sym(row.plan) }}{{ pickPrice(row.plan, 'original_monthly') }}<span class="unit">/月</span>
              <div v-if="currencyUnit === 'native' && row.plan.pricing.original_monthly_cny != null" class="cny-equiv">≈ ¥{{ row.plan.pricing.original_monthly_cny }}</div>
              <div v-if="pickPrice(row.plan, 'intro_with_affiliate') != null" class="intro-aff">
                <span class="intro-aff-label" title="邀请码首单优惠（少付钱），跟 ZCode 1.5x 额度加成独立，可同时享受。">{{ row.plan.pricing.intro_tag }}</span>
                <span class="intro">{{ sym(row.plan) }}{{ pickPrice(row.plan, 'intro_with_affiliate') }}</span>
              </div>
            </td>

            <!-- 包季：原价 + 用邀请码子行 -->
            <td class="num">
              <template v-if="pickPrice(row.plan, 'original_quarterly') != null">
                {{ sym(row.plan) }}{{ pickPrice(row.plan, 'original_quarterly') }}<span class="unit">/季</span>
                <div v-if="pickPrice(row.plan, 'intro_quarterly_with_affiliate') != null" class="intro-aff">
                  <span class="intro-aff-label">{{ row.plan.pricing.intro_tag }}</span>
                  <span class="intro">{{ sym(row.plan) }}{{ pickPrice(row.plan, 'intro_quarterly_with_affiliate') }}</span>
                </div>
              </template>
              <span v-else class="muted">—</span>
            </td>

            <!-- 包年：原价 + 用邀请码子行 -->
            <td class="num">
              <template v-if="pickPrice(row.plan, 'original_yearly') != null">
                {{ sym(row.plan) }}{{ pickPrice(row.plan, 'original_yearly') }}<span class="unit">/年</span>
                <div v-if="pickPrice(row.plan, 'yearly_monthly_equivalent') != null" class="year-equiv">≈ {{ sym(row.plan) }}{{ pickPrice(row.plan, 'yearly_monthly_equivalent') }}/月</div>
                <div v-if="pickPrice(row.plan, 'yearly_with_affiliate') != null" class="intro-aff">
                  <span class="intro-aff-label">{{ row.plan.pricing.intro_tag }}</span>
                  <span class="intro">{{ sym(row.plan) }}{{ pickPrice(row.plan, 'yearly_with_affiliate') }}</span>
                </div>
              </template>
              <span v-else class="muted">—</span>
            </td>

            <!-- 宣称用量（单位跟随厂商：火山/智谱=次，MiniMax=tokens） -->
            <td class="num claimed">
              <template v-if="row.plan.claimed.h5 != null">
                <span class="claimed-val">{{ fmtClaimed(row.plan, row.plan.claimed.h5) }}</span>
                <div class="claimed-unit">{{ row.plan.claimed_unit }}</div>
              </template>
              <span v-else class="muted">—</span>
            </td>
            <td class="num claimed">
              <template v-if="row.plan.claimed.weekly != null">
                <span class="claimed-val">{{ fmtClaimed(row.plan, row.plan.claimed.weekly) }}</span>
                <div class="claimed-unit">{{ row.plan.claimed_unit }}</div>
              </template>
              <span v-else class="muted">—</span>
            </td>
            <td class="num claimed">
              <template v-if="row.plan.claimed.monthly != null">
                <span class="claimed-val">{{ fmtClaimed(row.plan, row.plan.claimed.monthly) }}</span>
                <div class="claimed-unit">{{ row.plan.claimed_unit }}</div>
              </template>
              <span v-else class="muted">—</span>
            </td>

            <!-- 实测用量（tokens） -->
            <td class="num tok">
              {{ fmtTokens(row.plan.tokens.h5) }}<span v-if="row.plan.primary_model && row.plan.tokens.h5 != null" class="model-tag">@{{ row.plan.primary_model }}</span>
              <div v-if="row.plan.tokens.zcode_applicable && row.plan.tokens.zcode_h5" class="zcode-aff">
                <span class="zcode-label">ZCode×1.5</span>
                <span class="zcode-val">{{ fmtTokens(row.plan.tokens.zcode_h5) }}</span>
              </div>
            </td>
            <td class="num tok" :class="{ disputed: row.plan.tokens.weekly_disputed }">
              {{ fmtTokens(row.plan.tokens.weekly) }}<span v-if="row.plan.primary_model && row.plan.tokens.weekly != null" class="model-tag">@{{ row.plan.primary_model }}</span><span v-if="row.plan.tokens.weekly_disputed" class="dispute-warn" :title="row.plan.tokens.dispute_note || '数据存在较大不确定性'">⚠</span><span v-if="row.plan.tokens.weekly_aggregate_note" class="info-tooltip-wrap info-down"><span class="info-icon info-warn" aria-hidden="true">!</span><span class="info-tooltip">{{ row.plan.tokens.weekly_aggregate_note }}</span></span>
              <div v-if="row.plan.tokens.weekly_disputed" class="dispute-text">数据有争议</div>
              <div v-if="row.plan.tokens.zcode_applicable && row.plan.tokens.zcode_weekly" class="zcode-aff">
                <span class="zcode-label" title="ZCode 客户端限时活动，全周期 0.67 折算（等效 1.5x 额度）。跟邀请码独立，可同时享受。活动截止 2026-07-31。">ZCode×1.5</span>
                <span class="zcode-val">{{ fmtTokens(row.plan.tokens.zcode_weekly) }}</span>
              </div>
            </td>
            <td class="num tok">
              {{ fmtTokens(row.plan.tokens.monthly) }}<span v-if="row.plan.primary_model && row.plan.tokens.monthly != null" class="model-tag">@{{ row.plan.primary_model }}</span>
              <div v-if="row.plan.tokens.zcode_applicable && row.plan.tokens.zcode_monthly" class="zcode-aff">
                <span class="zcode-label">ZCode×1.5</span>
                <span class="zcode-val">{{ fmtTokens(row.plan.tokens.zcode_monthly) }}</span>
              </div>
              <div v-if="showDSEquiv" class="ds-equiv">
                <span class="ds-label">DS V4 {{ dsVariant === 'pro' ? 'Pro' : 'Flash' }} 等价</span>
                <span class="ds-val">{{ dsEquivForPlan(row.plan) != null ? fmtTokens(dsEquivForPlan(row.plan)) : '—' }}</span>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- 口径说明 -->
    <div class="disclaimer">
      <p>
        <strong>口径纪律：</strong>
        次数限额来自厂商官方公布（厂商可改定义，仅参考）；
        token 总额度来自探针实测，<strong>未实测的套餐直接显示 —</strong>。
      </p>
      <p>
        <strong>邀请码：</strong>同厂商通用。点击「复制邀请码」复制完整邀请链接，不影响榜单排序。
      </p>
    </div>
  </div>
</template>

<style scoped>
.ledger { margin: 24px 0; }

.sort-bar {
  display: flex; align-items: center; gap: 8px;
  margin-bottom: 16px; flex-wrap: wrap;
}
.sort-label { font-size: 13px; color: var(--vp-c-text-2); }
.sort-btn {
  padding: 5px 12px; border-radius: 7px;
  border: 1px solid var(--vp-c-divider);
  background: var(--vp-bg);
  font-size: 12px; color: var(--vp-c-text-2);
  cursor: pointer; transition: all .15s;
}
.sort-btn:hover { border-color: var(--vp-c-brand); color: var(--vp-c-brand); }
.sort-btn.active {
  background: var(--vp-c-brand); color: white;
  border-color: var(--vp-c-brand);
}
.count { margin-left: auto; font-size: 12px; color: var(--vp-c-text-3); }
.bar-divider { color: var(--vp-c-divider); margin: 0 4px; font-size: 12px; user-select: none; }
.divider { color: var(--vp-c-divider); margin: 0 2px; font-size: 14px; user-select: none; }

.table-wrap { overflow-x: auto; border-radius: 12px; border: 1px solid var(--vp-c-divider); }
.table-wrap table { width: max-content; min-width: 100%; }  /* 表格宽度按内容撑开，至少占满容器 */
table { border-collapse: collapse; font-size: 13px; background: var(--vp-bg); }
thead { background: var(--vp-c-bg-soft); }
th {
  padding: 10px 12px; text-align: left;
  font-size: 11px; font-weight: 600;
  color: var(--vp-c-text-3); text-transform: uppercase;
  letter-spacing: .3px; border-bottom: 1px solid var(--vp-c-divider);
  white-space: nowrap;
}
th.num, td.num { text-align: right; }
th.super-header {
  text-align: center;
  font-size: 11px;
  color: var(--vp-c-text-2);
  background: var(--vp-c-bg-soft-up);
  border-bottom: 1px solid var(--vp-c-divider);
}
th.super-header.alt {
  background: rgba(0, 113, 227, 0.06);
  color: var(--vp-c-brand);
}
th.super-header .unit-inline {
  font-size: 9px; font-weight: 400;
  color: var(--vp-c-text-3); text-transform: none; letter-spacing: 0;
}
thead tr:nth-child(2) th {
  border-bottom: 2px solid var(--vp-c-divider);
  padding-top: 6px; padding-bottom: 6px;
}

/* tokens 列样式 */
.tok { font-weight: 600; color: var(--vp-c-brand); }
.tok.disputed { color: #ff3b30; }
.dispute-warn {
  color: #ff3b30;
  font-weight: 700;
  margin-left: 4px;
  cursor: help;
}
.dispute-text {
  font-size: 9px;
  color: #ff3b30;
  font-weight: 600;
  margin-top: 2px;
  text-transform: uppercase;
  letter-spacing: .3px;
}

/* 月度无限样式 */
.tok.unlimited {
  color: #34c759;
}
.unlimited-val {
  font-size: 22px;
  font-weight: 700;
  color: #34c759;
  line-height: 1;
}
.unlimited-mark {
  font-size: 9px; color: #34c759;
  margin-top: 2px;
  text-transform: uppercase; letter-spacing: .3px;
  font-weight: 600;
}

/* 模型 tag（行内 @模型名，紧跟数字后面，附属信息样式） */
.model-tag {
  font-size: 10px;
  font-weight: 500;
  color: var(--vp-c-text-3);
  font-family: monospace;
  margin-left: 4px;
  letter-spacing: .2px;
}

/* hover tooltip 标记 — 红色感叹号 ! + 下方弹出 tooltip */
.info-tooltip-wrap {
  position: relative;
  display: inline-block;
  margin-left: 3px;
  cursor: help;
}
.info-icon {
  font-size: 16px;
  font-weight: 900;
  user-select: none;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 14px;
  height: 14px;
  line-height: 1;
  transition: transform .15s;
}
.info-warn {
  color: #e60012;                /* 纯红色大字感叹号,无背景 */
  background: transparent;
}
.info-tooltip-wrap:hover .info-icon {
  transform: scale(1.15);
}
.info-tooltip {
  position: absolute;
  left: 50%;
  /* 固定深色背景 + 白字，不依赖 VitePress 主题变量（暗色主题下 --vp-c-text-1 会变白导致白底白字） */
  background: #1a1a1a;
  color: #ffffff;
  padding: 6px 10px;
  border-radius: 6px;
  font-size: 11px;
  font-weight: 400;
  line-height: 1.5;
  white-space: nowrap;
  opacity: 0;
  pointer-events: none;
  transition: opacity .15s, transform .15s;
  transform: translateX(-50%);
  z-index: 100;
  max-width: 320px;
  white-space: normal;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.35);
  /* 加边框，亮色主题下也能看清边缘 */
  border: 1px solid rgba(0, 0, 0, 0.5);
}
/* 默认 tooltip 在上方(info-down 修饰符放下方,避开表格横向 overflow 截断) */
.info-tooltip-wrap:not(.info-down) .info-tooltip {
  bottom: calc(100% + 8px);
  transform: translateX(-50%) translateY(4px);
}
.info-tooltip-wrap:not(.info-down):hover .info-tooltip {
  opacity: 1;
  transform: translateX(-50%) translateY(0);
}
/* info-down:tooltip 显示在数字下方 */
.info-tooltip-wrap.info-down .info-tooltip {
  top: calc(100% + 8px);
  transform: translateX(-50%) translateY(-4px);
}
.info-tooltip-wrap.info-down:hover .info-tooltip {
  opacity: 1;
  transform: translateX(-50%) translateY(0);
}

/* ZCode 子行样式（参考「用邀请码」chip 样式） */
.zcode-aff {
  display: flex; align-items: center; gap: 5px;
  margin-top: 4px; justify-content: flex-end;
}
.zcode-label {
  font-size: 9px; font-weight: 600;
  color: #af52de;
  background: rgba(175, 82, 222, 0.1);
  padding: 2px 6px; border-radius: 4px;
  text-transform: uppercase; letter-spacing: .3px;
  white-space: nowrap;
}

/* DS V4 等价换算子行 */
.ds-equiv {
  display: flex; align-items: center; gap: 5px;
  margin-top: 4px; justify-content: flex-end;
}
.ds-label {
  font-size: 9px; font-weight: 600;
  color: #1a73e8;
  background: rgba(26, 115, 232, 0.08);
  padding: 2px 6px; border-radius: 4px;
  white-space: nowrap;
}
.ds-val {
  font-size: 11px; font-weight: 700;
  color: #1a73e8;
}
.zcode-val {
  font-size: 11px; font-weight: 700;
  color: #af52de;
}
td { padding: 12px; border-bottom: 1px solid var(--vp-c-divider); vertical-align: middle; }
tbody tr:last-child td { border-bottom: none; }
tbody tr:hover td { background: var(--vp-c-bg-soft-up); }

.vendor-cell { min-width: 130px; vertical-align: top; padding-top: 14px; }
.vendor-link {
  display: inline-flex; align-items: center;
  color: inherit; text-decoration: none;
  border-radius: 4px; padding: 1px 2px; margin: -1px -2px;
  transition: color .15s, background .15s;
}
.vendor-link:hover {
  color: var(--vp-c-brand);
  background: var(--vp-c-brand-soft);
  text-decoration: underline; text-underline-offset: 2px;
}
.vendor-ext {
  width: 10px; height: 10px; margin-left: 3px;
  color: var(--vp-c-text-3); opacity: 0.55; transition: opacity .15s, color .15s;
}
.vendor-link:hover .vendor-ext { opacity: 1; color: var(--vp-c-brand); }
.vendor-dot {
  display: inline-block;
  width: 8px; height: 8px; border-radius: 50%;
  margin-right: 6px; vertical-align: middle;
}

.plan-cell { min-width: 140px; }
.plan-name { font-weight: 600; font-size: 13px; }
.plan-meta { display: flex; align-items: center; gap: 6px; margin-top: 3px; }
/* 用量倍率标签：×1 / ×4 / ×20 / ×60 ——一眼看出档位差距 */
.tier-mult {
  font-size: 10px; font-weight: 700;
  color: var(--vp-c-brand);
  background: var(--vp-c-brand-soft);
  padding: 1px 6px; border-radius: 4px;
  font-family: ui-monospace, monospace;
  white-space: nowrap;
}
/* 最低档（×1）弱化，避免一堆 ×1 抢视觉 */
.tier-mult.is-base { color: var(--vp-c-text-3); background: var(--vp-c-bg-soft); font-weight: 500; }
.tier-name { font-size: 10px; color: var(--vp-c-text-3); font-family: monospace; text-transform: uppercase; letter-spacing: .3px; }

.unit { font-size: 10px; color: var(--vp-c-text-3); margin-left: 2px; }
.intro-aff {
  display: flex; align-items: center; gap: 6px;
  margin-top: 4px; justify-content: flex-end;
}
.intro-aff-label {
  font-size: 9px; font-weight: 600;
  color: var(--vp-c-brand);
  background: var(--vp-c-brand-soft);
  padding: 2px 6px; border-radius: 4px;
  text-transform: uppercase; letter-spacing: .3px;
  white-space: nowrap;
}
.intro-aff-label.yearly {
  color: #ff9500;
  background: rgba(255, 149, 0, 0.1);
}
.intro-yearly {
  display: flex; align-items: center; gap: 5px;
  margin-top: 3px; justify-content: flex-end;
}
.intro-small {
  font-size: 11px; color: #ff9500; font-weight: 600;
}
.intro { font-weight: 700; color: #34c759; font-size: 14px; }
.intro-sub { font-size: 10px; color: var(--vp-c-text-3); margin-top: 2px; }

/* USD 折算人民币（对比参考，弱化展示） */
.cny-equiv {
  font-size: 10px;
  color: var(--vp-c-text-3);
  font-weight: 400;
  margin-top: 2px;
  font-family: monospace;
}

/* 年折月（包年列下面，显示按月均摊价格） */
.year-equiv {
  font-size: 10px;
  color: var(--vp-c-text-3);
  font-weight: 400;
  margin-top: 2px;
  font-family: monospace;
}
.muted { color: var(--vp-c-text-3); }

/* 邀请码 mini 按钮（嵌在厂商 cell 下方）*/
.vendor-aff {
  margin-top: 8px;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 3px;
}
.aff-btn-mini {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  padding: 3px 8px;
  border-radius: 5px;
  border: 1px solid var(--vp-c-brand);
  background: var(--vp-c-brand-soft);
  color: var(--vp-c-brand);
  cursor: pointer;
  transition: all .15s;
  font-size: 10px;
  font-weight: 600;
  line-height: 1.3;
  white-space: nowrap;
}
.aff-btn-mini:hover { background: var(--vp-c-brand); color: white; }
.aff-btn-mini.copied { background: #34c759; color: white; border-color: #34c759; }
.aff-none {
  font-size: 9px;
  color: var(--vp-c-text-3);
  margin-top: 6px;
}

.disclaimer {
  margin-top: 20px; padding: 16px;
  background: var(--vp-c-bg-soft); border-radius: 10px;
  font-size: 12px; color: var(--vp-c-text-2); line-height: 1.7;
}
.disclaimer p { margin: 4px 0; }
.disclaimer strong { color: var(--vp-c-text-1); }
</style>
