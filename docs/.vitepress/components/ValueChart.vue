<script setup>
import { computed, ref } from 'vue'
import plansData from '../plans.json'

// ── 数据：sub=订阅套餐 / api=额度型（opencode-go，$ 额度跨模型）──
const all = computed(() => plansData.model_value || [])
const groups = computed(() => ({
  sub: all.value.filter(d => d.series === 'sub'),
  api: all.value.filter(d => d.series === 'api'),
}))
const active = ref('sub')
const rows = computed(() => groups.value[active.value] || [])

// ── 配色（子代理调查结论：厂商恒定色，深浅双值）──
const vendorColor = {
  anthropic:  { light: '#E07856', dark: '#E58B6C' },
  openai:     { light: '#0EA37F', dark: '#1FC39B' },
  alibaba:    { light: '#FF6A00', dark: '#FF8A33' },
  opencode:   { light: '#E5A800', dark: '#F0B429' },
  minimax:    { light: '#F0436E', dark: '#FF7089' },
  kimi:       { light: '#556575', dark: '#C9D1D9' },
  zhipu:      { light: '#3B82F6', dark: '#748FFC' },
  tencent:    { light: '#7C3AED', dark: '#A78BFA' },
  volcengine: { light: '#06B6D4', dark: '#22D3EE' },
  zai:        { light: '#8B5CF6', dark: '#A78BFA' },
}
function colorOf(vendor) {
  const c = vendorColor[vendor]
  if (!c) return '#86868b'
  return typeof document !== 'undefined' && document.documentElement.classList.contains('dark') ? c.dark : c.light
}

// ── 布局与柱状 ──
const W = 1400, H = 680
const M = { top: 40, right: 20, bottom: 150, left: 96 }
const yMax = computed(() => Math.max(1, ...rows.value.map(d => d.tokens_per_cny)) * 1.06)
const plotW = W - M.left - M.right
const barW = computed(() => Math.max(6, (plotW / Math.max(1, rows.value.length)) * 0.72))
const bx = (i) => M.left + (i * plotW) / Math.max(1, rows.value.length) + ((plotW / rows.value.length) - barW.value) / 2
const by = (v) => H - M.bottom - (v / yMax.value) * (H - M.top - M.bottom)
const bH = (v) => (v / yMax.value) * (H - M.top - M.bottom)

const hover = ref(-1)
const hoverData = computed(() => (hover.value >= 0 ? rows.value[hover.value] : null))
const hoverPct = computed(() => (hover.value >= 0 ? ((bx(hover.value) + barW.value / 2) / W) * 100 : 0))
const fmt = (v) => (v >= 1 ? v.toLocaleString('zh-CN', { maximumFractionDigits: 0 }) : v.toFixed(2))
const fmtB = (n) => (n >= 1e9 ? (n / 1e9).toFixed(2) + 'B' : (n / 1e6).toFixed(0) + 'M')
const yTicks = computed(() => {
  const t = []
  for (let i = 0; i <= 4; i++) {
    const val = (yMax.value * i) / 4
    t.push({ y: by(val), label: Math.round(val).toLocaleString('zh-CN') })
  }
  return t
})
</script>

<template>
  <div class="vc2">
    <p class="vc2-desc">
      指标：<b>榜单表格里的「月度用量 ÷ 包月原价」</b>——每 1 元人民币能跑多少 tokens（USD 套餐按汇率折算）。
      分两条线：<b class="c-sub">订阅套餐</b> 与 <b class="c-api">额度型（OpenCode Go，$ 额度跨模型，口径不同单独成线）</b>。
      柱高即性价比，从左到右递减；有多个 @模型的套餐逐模型拆柱。悬停查看明细，下方为完整排名。
    </p>

    <div class="vc2-legend">
      <span v-for="(v, vid) in vendorColor" :key="vid" class="vc2-lg">
        <span class="vc2-lg-dot" :style="{ background: colorOf(vid) }"></span>{{ { anthropic:'Anthropic', openai:'OpenAI', alibaba:'阿里', opencode:'OpenCode', minimax:'MiniMax', kimi:'Kimi', zhipu:'智谱', tencent:'腾讯云', volcengine:'火山', zai:'Z.AI' }[vid] }}
      </span>
    </div>

    <div class="vc2-ghost-note">柱顶虚线段 = 含临时加成（夜间畅用×2 / 用邀请码折扣）后的增量，悬停看各场景；活动结束或改价自动消失</div>

    <div class="vc2-tabs">
      <button :class="['vc2-tab', { active: active === 'sub' }]" @click="active = 'sub'; hover = -1">
        订阅套餐 <span class="vc2-tabn">{{ groups.sub.length }}</span>
      </button>
      <button :class="['vc2-tab', { active: active === 'api' }]" @click="active = 'api'; hover = -1">
        API 额度型 <span class="vc2-tabn">{{ groups.api.length }}</span>
      </button>
    </div>

    <div class="vc2-chart">
      <svg :viewBox="`0 0 ${W} ${H}`" class="vc2-svg" @mouseleave="hover = -1">
        <g v-for="t in yTicks" :key="t.y">
          <line class="vc2-grid" :x1="M.left" :x2="W - M.right" :y1="t.y" :y2="t.y" />
          <text class="vc2-tick" :x="M.left - 10" :y="t.y + 4" text-anchor="end">{{ t.label }}</text>
        </g>
        <text class="vc2-axis" :x="M.left - 10" :y="M.top - 16">万 tokens / ¥1（包月）</text>

        <g v-for="(d, i) in rows" :key="d.plan_id + d.model">
          <!-- 柱顶堆叠段：临时加成场景（基准 → 含加成），斜纹半透明；活动过期自动消失 -->
          <rect
            v-if="d.ghost_tokens_per_cny"
            :x="bx(i)" :y="by(d.ghost_tokens_per_cny)"
            :width="barW" :height="Math.max(2, bH(d.tokens_per_cny) - bH(d.ghost_tokens_per_cny))"
            :fill="colorOf(d.vendor)" fill-opacity="0.28"
            stroke="#ff6600" stroke-width="1.2" stroke-dasharray="4 3"
            :opacity="hover === -1 || hover === i ? 1 : 0.35"
            rx="2"
          />
          <rect
            :x="bx(i)" :y="by(d.tokens_per_cny)"
            :width="barW" :height="Math.max(2, bH(d.tokens_per_cny))"
            :fill="colorOf(d.vendor)"
            :opacity="hover === -1 || hover === i ? 1 : 0.35"
            rx="2"
          />
          <text
            v-if="hover === i || i < 3"
            :x="bx(i) + (d.ghost_tokens_per_cny ? barW + 1 : 0) + barW / 2" :y="by(d.ghost_tokens_per_cny || d.tokens_per_cny) - 6"
            text-anchor="middle" class="vc2-barval"
          >{{ fmt(d.ghost_tokens_per_cny || d.tokens_per_cny) }}</text>
          <text
            :x="bx(i) + barW / 2" :y="H - M.bottom + 14"
            text-anchor="end" class="vc2-xlab"
            :transform="`rotate(-40 ${bx(i) + barW / 2} ${H - M.bottom + 14})`"
            :opacity="hover === -1 || hover === i ? 1 : 0.45"
          >{{ d.vendor_display }}·{{ d.model }}</text>
          <rect
            :x="M.left + (i * plotW) / rows.length" y="0"
            :width="plotW / rows.length" :height="H - M.bottom"
            fill="transparent" @mouseenter="hover = i"
          />
        </g>

        <line :x1="M.left" :x2="W - M.right" :y1="H - M.bottom" :y2="H - M.bottom" class="vc2-baseline" />
      </svg>

      <div
        v-if="hoverData"
        class="vc2-tip"
        :style="{ left: `min(max(${hoverPct}%, 160px), calc(100% - 160px))` }"
      >
        <div class="vc2-tip-model">{{ hoverData.label }}</div>
        <div class="vc2-tip-big">{{ fmt(hoverData.tokens_per_cny) }} <span>万 tokens / ¥1（包月）</span></div>
        <div class="vc2-tip-meta">月用量 {{ fmtB(hoverData.monthly_tokens) }} tokens · 包月原价 ¥{{ hoverData.price_cny }}</div>
        <div v-for="g in (hoverData.ghosts || [])" :key="g.label" class="vc2-tip-boost">
          含{{ g.label }}：≈ {{ fmt(g.tokens_per_cny) }} 万/¥
        </div>
      </div>
    </div>

    <div class="vc2-xlabel">
      <template v-if="hoverData">{{ hoverData.label }}</template>
      <template v-else>共 {{ rows.length }} 个点 · 悬停柱子查看明细 · 完整排名见下</template>
    </div>

    <div class="vc2-rank">
      <button
        v-for="(d, i) in rows" :key="d.plan_id + d.model"
        class="vc2-rankrow"
        :class="{ hot: hover === i }"
        :style="{ borderLeft: `3px solid ${colorOf(d.vendor)}` }"
        @mouseenter="hover = i"
        @mouseleave="hover = -1"
      >
        <span class="vc2-rank-n">{{ i + 1 }}</span>
        <span class="vc2-rank-name">{{ d.label }}</span>
        <span class="vc2-rank-val">{{ fmt(d.tokens_per_cny) }} 万/¥</span>
      </button>
    </div>

    <p class="vc2-note">
      口径：月度用量含官方场景估算（智谱 v3 全非高峰 + 95% cache）与探针实测（v2「实测反推」），详见榜单各行备注；
      智谱 9/3-9/20 夜间畅用活动的 flash ×2 未计入（活动口径见情报板）；包月均取原价（非首月/邀请码价）。
      带「（等效折算）」的行是 ChatGPT/Claude Code Pro 的等效美元拆分口径（表格内有灰字说明）。
    </p>
  </div>
</template>

<style scoped>
.vc2 { max-width: 1400px; }
.vc2-desc { font-size: 14px; color: var(--vp-c-text-2); line-height: 1.7; }
.vc2-desc b { color: var(--vp-c-text-1); }
.c-sub { color: #ff6600; }
.c-api { color: #0b8aff; }
.vc2-legend { display: flex; flex-wrap: wrap; gap: 6px 14px; margin: 8px 0 4px; font-size: 12px; color: var(--vp-c-text-2); }
.vc2-lg { display: inline-flex; align-items: center; gap: 5px; }
.vc2-lg-dot { width: 9px; height: 9px; border-radius: 50%; display: inline-block; }
.vc2-ghost-note { font-size: 12px; color: var(--vp-c-text-3); margin: 6px 0 0; }
.vc2-tabs { display: flex; gap: 8px; margin: 10px 0 4px; }
.vc2-tab {
  border: 1px solid var(--vp-c-divider);
  background: var(--vp-c-bg);
  color: var(--vp-c-text-2);
  padding: 5px 14px;
  border-radius: 6px;
  font: inherit;
  font-size: 13px;
  cursor: pointer;
}
.vc2-tab.active { border-color: #ff6600; color: #ff6600; font-weight: 600; }
.vc2-tabn { opacity: 0.7; font-size: 11px; }
.vc2-chart { position: relative; margin-top: 8px; }
.vc2-svg { width: 100%; height: auto; display: block; }
.vc2-grid { stroke: var(--vp-c-divider); stroke-width: 1; stroke-dasharray: 3 4; opacity: 0.8; }
.vc2-tick { font-size: 13px; fill: var(--vp-c-text-3); }
.vc2-axis { font-size: 13px; fill: var(--vp-c-text-2); font-weight: 600; }
.vc2-barval { font-size: 12px; font-weight: 700; fill: #ff6600; }
.vc2-xlab { font-size: 11px; fill: var(--vp-c-text-2); }
.vc2-baseline { stroke: var(--vp-c-divider); stroke-width: 1.5; }
.vc2-tip {
  position: absolute;
  top: 8px;
  transform: translateX(-50%);
  background: var(--vp-c-bg);
  border: 1px solid var(--vp-c-divider);
  border-radius: 8px;
  padding: 10px 14px;
  pointer-events: none;
  box-shadow: 0 4px 16px rgba(0,0,0,0.25);
  min-width: 230px;
  z-index: 5;
}
.vc2-tip-model { font-size: 12px; color: var(--vp-c-text-3); margin-bottom: 2px; }
.vc2-tip-big { font-size: 24px; font-weight: 700; color: #ff6600; line-height: 1.2; }
.vc2-tip-big span { font-size: 13px; font-weight: 400; color: var(--vp-c-text-2); }
.vc2-tip-meta { font-size: 12px; color: var(--vp-c-text-2); margin-top: 2px; }
.vc2-tip-boost { font-size: 12px; color: #ff6600; margin-top: 2px; }
.vc2-xlabel {
  text-align: center;
  font-size: 14px;
  font-weight: 600;
  color: var(--vp-c-text-1);
  margin-top: 2px;
  min-height: 20px;
}
.vc2-rank {
  margin-top: 14px;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 2px 18px;
}
.vc2-rankrow {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 5px 8px;
  border: none;
  border-bottom: 1px solid var(--vp-c-divider);
  border-left: 3px solid transparent;
  background: transparent;
  font: inherit;
  font-size: 13px;
  color: var(--vp-c-text-1);
  text-align: left;
  cursor: default;
  border-radius: 4px;
}
.vc2-rankrow.hot { background: var(--vp-c-bg-soft); }
.vc2-rank-n { color: var(--vp-c-text-3); min-width: 20px; text-align: right; font-size: 11px; }
.vc2-rank-name { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.vc2-rank-val { color: #ff6600; font-weight: 600; }
.vc2-note { font-size: 12px; color: var(--vp-c-text-3); margin-top: 10px; }
</style>
