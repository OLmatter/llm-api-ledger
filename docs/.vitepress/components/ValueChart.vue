<script setup>
import { computed, ref } from 'vue'
import { useData } from 'vitepress'
import plansData from '../plans.json'

const { isDark } = useData()

// ── 数据分组 ──
const all = computed(() => plansData.model_value || [])
const groups = computed(() => ({
  sub: all.value.filter(d => d.series === 'sub'),
  api: all.value.filter(d => d.series === 'api'),
}))
const active = ref('sub')

// 排名模式：standard=标准用量（全高峰下限/探针实测） / extreme=极限用量（全非高峰上限）
const mode = ref('standard')
const valOf = (d) => (mode.value === 'standard'
  ? (d.conservative_tokens_per_cny ?? d.tokens_per_cny)
  : d.tokens_per_cny)

// 厂商筛选（空 Set = 全部显示）
const hiddenVendors = ref(new Set())
function toggleVendor(v) {
  const s = new Set(hiddenVendors.value)
  s.has(v) ? s.delete(v) : s.add(v)
  hiddenVendors.value = s
}

// 排序键严格随模式：标准=保守/实测值，极限=含活动加成的上限值。
// 柱长、标签、排序三者必须同源（同一口径值），否则必然「看着乱序」。
const sortVal = (d) => (mode.value === 'extreme' ? Math.max(valOf(d), d.ghost_tokens_per_cny || 0) : valOf(d))
const rows = computed(() => (groups.value[active.value] || [])
  .filter(d => !hiddenVendors.value.has(d.vendor))
  .sort((a, b) => sortVal(b) - sortVal(a)))

// 当前视图实际出现的厂商（图例只显示存在的）
const presentVendors = computed(() => [...new Set(rows.value.map(d => d.vendor))])

// ── 口径标注 ──
function caliberOf(d) {
  const anns = d.annotations || []
  if (anns.some(a => a.value === 'full_offpeak')) {
    return mode.value === 'standard' ? '全高峰下限' : '全非高峰期'
  }
  if (anns.some(a => a.label === 'Go 观测' || a.value === 'opencode-go-client')) return 'Go 观测'
  if (anns.some(a => a.value === 'probe_inferred') || d.monthly_source) return '实测反推'
  return ''
}

// ── 布局（横向柱状：左列名称 + 右侧柱体）──
const barMax = 560
const rowH = 34

const scaleLog = ref(true)
const valMax = computed(() => Math.max(...rows.value.map(d => sortVal(d)), 1))
const valMin = computed(() => Math.min(...rows.value.map(d => valOf(d)), valMax.value * 0.02))
function valScale(v) {
  if (!scaleLog.value) return (v / valMax.value) * barMax
  const lo = Math.log10(Math.max(valMin.value, 1)), hi = Math.log10(valMax.value * 1.05)
  return ((Math.log10(Math.max(v, 1)) - lo) / (hi - lo)) * barMax
}
function gridLines() {
  const lines = []
  if (scaleLog.value) {
    for (const decade of [1, 10, 100, 1000, 10000]) {
      if (decade >= valMin.value * 0.9 && decade <= valMax.value * 1.05) {
        lines.push({ v: decade, px: valScale(decade), label: decade.toLocaleString('zh-CN') })
      }
    }
  } else {
    for (let i = 1; i <= 4; i++) {
      const v = (valMax.value * i) / 4
      lines.push({ v, px: valScale(v), label: Math.round(v).toLocaleString('zh-CN') })
    }
  }
  return lines
}
const grid = computed(() => gridLines())

const fmt = (v) => (v == null ? '—' : v >= 1 ? v.toLocaleString('zh-CN', { maximumFractionDigits: 0 }) : v.toFixed(2))
const fmtB = (n) => (n >= 1e9 ? (n / 1e9).toFixed(2) + 'B' : (n / 1e6).toFixed(0) + 'M')

// 悬停行
const hover = ref('')
const hoverRow = computed(() => rows.value.find(d => d.plan_id + '/' + d.model === hover.value) || null)

const modeDesc = computed(() => (mode.value === 'extreme'
  ? '极限用量口径：全部流量集中在错峰时段（每日 23:00–次日 09:00 及周末，积分 5 折）+ 95% 缓存命中，智谱 v3 另叠加「夜间畅用」活动（GLM-5.3-Flash 在 ZCode 端 0 消耗、其他 Agent 额度 ×2，9/3–9/20）。'
  : '标准用量口径：全高峰时段（工作日 14:00–18:00，积分 1 倍）+ 95% 缓存命中的下限值；智谱 v2 为探针实测反推（普通客户端口径），ChatGPT/Claude Code 为等效美元折算。'))

const vendorName = (v) => ({ zhipu:'智谱', zai:'Z.AI', anthropic:'Anthropic', openai:'OpenAI', kimi:'Kimi', minimax:'MiniMax', tencent:'腾讯云', volcengine:'火山', alibaba:'阿里', opencode:'OpenCode' }[v] || v)
function colorOf(vendor) {
  const c = {
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
  }[vendor]
  if (!c) return '#86868b'
  return isDark.value ? c.dark : c.light
}
</script>

<template>
  <div class="vc3">
    <p class="vc3-desc">
      指标：<b>榜单表格里的「月度用量 ÷ 包月原价」</b>——每 1 元人民币能跑多少 tokens（USD 套餐按汇率折算）。
      横向柱越长性价比越高。
    </p>

    <!-- 工具栏 -->
    <div class="vc3-toolbar">
      <button :class="['vc3-tab', { active: active === 'sub' }]" @click="active = 'sub'">
        订阅套餐 <span class="vc3-n">{{ groups.sub.filter(d => !d.virtual).length }}</span>
      </button>
      <button :class="['vc3-tab', { active: active === 'api' }]" @click="active = 'api'">
        API 额度型 <span class="vc3-n">{{ groups.api.filter(d => !d.virtual).length }}</span>
      </button>
      <span class="vc3-sep">|</span>
      <span class="vc3-label">排名：</span>
      <button :class="['vc3-tab', { active: mode === 'standard' }]" @click="mode = 'standard'"
        title="全高峰下限（保守）与探针实测口径">标准用量</button>
      <button :class="['vc3-tab', { active: mode === 'extreme' }]" @click="mode = 'extreme'"
        title="全非高峰上限（错峰 5 折 + 95% cache）口径">极限用量</button>
      <span class="vc3-sep">|</span>
      <span class="vc3-label">轴：</span>
      <button :class="['vc3-tab', { active: !scaleLog }]" @click="scaleLog = false" title="线性比例">线性</button>
      <button :class="['vc3-tab', { active: scaleLog }]" @click="scaleLog = true" title="对数比例：数值悬殊时让所有柱可见">log</button>
    </div>

    <!-- 常驻口径说明（随模式联动） -->
    <div class="vc3-modedesc">{{ modeDesc }}</div>

    <!-- 厂商筛选 chips（仅显示当前组实际存在的厂商） -->
    <div class="vc3-chips">
      <button
        v-for="v in presentVendors" :key="v"
        class="vc3-chip" :class="{ off: hiddenVendors.has(v) }"
        :style="hiddenVendors.has(v) ? {} : { borderColor: colorOf(v), color: colorOf(v) }"
        @click="toggleVendor(v)"
        :title="hiddenVendors.has(v) ? '点击显示' : '点击隐藏该厂商'"
      >{{ vendorName(v) }}</button>
    </div>

    <!-- 横向柱状图 -->
    <div class="vc3-scalehint">log 轴刻度：{{ grid.map(g => g.label).join(' / ') }} 万 tokens</div>
    <div class="vc3-chart" :style="{ height: chartH + 'px' }">
      <div class="vc3-axis">
        <span v-for="g in grid" :key="g.label" class="vc3-gridline" :style="{ top: (barMax - g.px + 8) + 'px' }">
          <i class="vc3-grid" :style="{ width: barMax + 'px' }"></i>
        </span>
      </div>
      <div
        v-for="(d, i) in rows" :key="d.plan_id + d.model"
        class="vc3-row" :class="{ 'vc3-virtual': d.virtual }"
        @mouseenter="hover = d.plan_id + '/' + d.model"
      >
        <span class="vc3-rank">{{ i + 1 }}</span>
        <span class="vc3-dot" :style="{ background: colorOf(d.vendor) }"></span>
        <span class="vc3-name" :title="d.label">{{ [d.vendor_display, d.plan_name, d.model].filter(Boolean).join(' · ').replace(/ GLM Coding Plan /, ' ') }}<em v-if="d.virtual" class="vc3-vtag">等效折算</em></span>
        <span class="vc3-barzone">
          <i class="vc3-bar" :style="{ width: Math.max(3, valScale(valOf(d))) + 'px', background: colorOf(d.vendor) }"></i>
          <i v-if="mode === 'extreme' && d.ghost_tokens_per_cny && d.ghost_tokens_per_cny > valOf(d)"
            class="vc3-bar vc3-ext"
            :style="{ left: valScale(valOf(d)) + 'px', width: Math.max(2, valScale(d.ghost_tokens_per_cny) - valScale(valOf(d))) + 'px' }"
            title="夜间畅用×2 等活动加成增量（叠加在标准口径之上）"></i>
          <b class="vc3-val">{{ fmt(sortVal(d)) }}</b>
          <em v-if="caliberOf(d)" class="vc3-caliber">{{ caliberOf(d) }}</em>
        </span>
      </div>
    </div>

    <!-- 悬停明细卡 -->
    <div v-if="hoverRow" class="vc3-tip">
      <div class="vc3-tip-title">{{ hoverRow.label }}</div>
      <div class="vc3-tip-line">
        {{ mode === 'standard' ? '标准用量' : '极限用量' }}：<b>{{ fmt(valOf(hoverRow)) }}</b> 万 tokens / ¥1
        <template v-if="mode === 'extreme' && hoverRow.conservative_tokens_per_cny">（标准口径 {{ fmt(hoverRow.conservative_tokens_per_cny) }}）</template>
      </div>
      <div class="vc3-tip-line muted" v-if="hoverRow.monthly_tokens != null">月用量 {{ fmtB(hoverRow.monthly_tokens) }} tokens · 包月原价 ¥{{ hoverRow.price_cny }}</div>
      <div class="vc3-tip-line muted" v-else>官方按量价：输入 ¥{{ hoverRow.input }}/M · 缓存命中 ¥{{ hoverRow.cached_input }}/M · 输出 ¥{{ hoverRow.output }}/M{{ hoverRow.limited_until ? '（限时至 ' + hoverRow.limited_until + '）' : '' }}</div>
      <div v-for="a in (hoverRow.annotations || [])" :key="a.label" class="vc3-tip-line muted">{{ a.label }}：{{ a.tooltip }}</div>
    </div>



    <p class="vc3-note">
      口径：智谱/Z.AI v3 为官方场景估算双口径（极限=全非高峰上限，标准=全高峰下限）；v2 为探针实测反推；
      opencode 为 Go 客户端观测；ChatGPT 等效折算行为虚数口径参考（列表尾部单独归档）。包月均取原价（非首月/邀请码价）。
      方法论详见 <a href="/llm-api-ledger/methodology">数据口径</a> 页。
    </p>
  </div>
</template>

<style scoped>
.vc3 { max-width: 1400px; font-size: 13px; }
.vc3-desc { color: var(--vp-c-text-2); line-height: 1.7; }
.vc3-desc b { color: var(--vp-c-text-1); }
.vc3-toolbar { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; margin: 12px 0 4px; }
.vc3-tab {
  border: 1px solid var(--vp-c-divider); background: var(--vp-c-bg);
  color: var(--vp-c-text-2); padding: 4px 12px; border-radius: 6px;
  font: inherit; font-size: 13px; cursor: pointer;
}
.vc3-tab.active { border-color: #ff6600; color: #ff6600; font-weight: 600; }
.vc3-n { opacity: 0.7; font-size: 11px; }
.vc3-sep { color: var(--vp-c-divider); }
.vc3-label { font-size: 13px; color: var(--vp-c-text-2); }
.vc3-modedesc {
  font-size: 12px; color: var(--vp-c-text-2); line-height: 1.6;
  background: var(--vp-c-bg-soft); border-radius: 6px; padding: 6px 10px; margin: 6px 0;
}
.vc3-chips { display: flex; flex-wrap: wrap; gap: 6px; margin: 6px 0; }
.vc3-chip {
  border: 1px solid var(--vp-c-divider); background: var(--vp-c-bg);
  color: var(--vp-c-text-2); padding: 2px 10px; border-radius: 999px;
  font: inherit; font-size: 12px; cursor: pointer;
}
.vc3-chip.off { opacity: 0.35; text-decoration: line-through; }
.vc3-scalehint { font-size: 11px; color: var(--vp-c-text-3); margin: 4px 0 2px 460px; }
.vc3-chart { position: relative; margin: 8px 0 4px; }
.vc3-axis { position: absolute; inset: 0; pointer-events: none; }
.vc3-gridline { position: absolute; left: 0; height: 0; }
.vc3-grid { display: block; height: 1px; background: var(--vp-c-divider); opacity: 0.6; }
.vc3-gridlabel { position: absolute; right: 8px; top: -14px; font-size: 11px; color: var(--vp-c-text-3); font-style: normal; }
.vc3-row { display: flex; align-items: center; gap: 8px; height: 34px; padding: 0 4px; }
.vc3-row:hover { background: var(--vp-c-bg-soft); }
.vc3-row.dim { opacity: 0.25; }
.vc3-rank { color: var(--vp-c-text-3); min-width: 22px; text-align: right; font-size: 11px; }
.vc3-dot { width: 9px; height: 9px; border-radius: 50%; flex-shrink: 0; }
.vc3-name {
  width: 420px; flex-shrink: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
  color: var(--vp-c-text-1);
}
.vc3-barzone { position: relative; flex: 1; height: 22px; display: flex; align-items: center; }
.vc3-bar { display: block; height: 16px; border-radius: 0 3px 3px 0; }
.vc3-ext {
  background: repeating-linear-gradient(45deg, transparent 0 3px, rgba(255,102,0,0.5) 3px 5px) !important;
  border: 1px dashed #ff6600; border-radius: 0 3px 3px 0;
}
.vc3-val { margin-left: 8px; font-size: 12px; font-weight: 600; color: var(--vp-c-text-1); white-space: nowrap; }
.vc3-caliber { margin-left: 8px; font-size: 11px; color: #d97706; opacity: 0.85; white-space: nowrap; }
.vc3-vrow .vc3-bar { opacity: 0.45; }
.vc3-vrow { opacity: 0.85; }
.vc3-vtag {
  font-size: 10px; font-style: normal; color: #d97706;
  border: 1px solid #d97706; border-radius: 3px; padding: 0 3px; margin-left: 4px;
}
.vc3-sub { font-size: 14px; margin: 20px 0 8px; color: var(--vp-c-text-2); }
.vc3-tip {
  position: sticky; bottom: 8px;
  background: var(--vp-c-bg); border: 1px solid var(--vp-c-divider); border-radius: 8px;
  padding: 8px 12px; margin-top: 8px; font-size: 12px;
  box-shadow: 0 4px 16px rgba(0,0,0,0.2);
}
.vc3-tip-title { font-weight: 600; color: var(--vp-c-text-1); margin-bottom: 2px; }
.vc3-tip-line { color: var(--vp-c-text-2); line-height: 1.6; }
.vc3-tip-line b { color: #ff6600; }
.vc3-tip-line.muted { color: var(--vp-c-text-3); }
.vc3-note { font-size: 12px; color: var(--vp-c-text-3); margin-top: 12px; line-height: 1.7; }
.vc3-note a { color: var(--vp-c-link); }
</style>
