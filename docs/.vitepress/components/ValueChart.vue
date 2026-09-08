<script setup>
import { computed } from 'vue'
import plansData from '../plans.json'

// 每模型:tokens/元 降序排布,画成一条下坡曲线
const data = computed(() => plansData.model_value || [])

const W = 1200, H = 460
const M = { top: 30, right: 20, bottom: 110, left: 70 }

const yMax = computed(() => {
  const vals = data.value.map(d => d.tokens_per_cny)
  return vals.length ? Math.max(...vals) * 1.08 : 1
})
const x = (i) => M.left + (i * (W - M.left - M.right)) / Math.max(1, data.value.length - 1)
const y = (v) => H - M.bottom - (v / yMax.value) * (H - M.top - M.bottom)

const pathLine = computed(() => data.value.map((d, i) => `${i ? 'L' : 'M'}${x(i)},${y(d.tokens_per_cny)}`).join(' '))
const pathArea = computed(() => `${pathLine.value} L${x(data.value.length - 1)},${H - M.bottom} L${M.left},${H - M.bottom} Z`)

const vendorColor = { zhipu: '#4f6ef7', zai: '#7c5cff', openai: '#10a37f', anthropic: '#d97757', kimi: '#16a34a', minimax: '#f59e0b', tencent: '#0ea5e9', volcengine: '#2563eb', alibaba: '#ff6600', opencode: '#8b5cf6' }
const dotColor = (v) => vendorColor[v] || '#86868b'

// y 轴刻度:5 档
const yTicks = computed(() => {
  const t = []
  for (let i = 0; i <= 5; i++) {
    const val = (yMax.value * i) / 5
    t.push({ y: y(val), label: val.toFixed(1) + ' 万' })
  }
  return t
})
</script>

<template>
  <div class="vc-wrap">
    <p class="vc-desc">
      指标：<b>每 1 元人民币能跑多少 tokens</b>（编程场景口径：92% 缓存命中 + 7.3% 新输入 + 0.7% 输出，USD 按汇率折算 CNY）。
      从左到右性价比递减——斜率越陡，头尾差距越大。限 时促销价（如 GLM-5.3-Flash 5 折）按现价计，到期后点位会自然下移。
    </p>
    <svg :viewBox="`0 0 ${W} ${H}`" class="vc-svg" role="img" aria-label="模型性价比排行榜曲线">
      <!-- y 网格与刻度 -->
      <g v-for="t in yTicks" :key="t.y">
        <line :x1="M.left" :x2="W - M.right" :y1="t.y" :y2="t.y" stroke="#e5e7eb" stroke-width="1" />
        <text :x="M.left - 8" :y="t.y + 4" text-anchor="end" font-size="12" fill="#828282">{{ t.label }}</text>
      </g>
      <!-- 面积 + 折线 -->
      <path :d="pathArea" fill="url(#vcGrad)" opacity="0.35" />
      <path :d="pathLine" fill="none" stroke="#ff6600" stroke-width="2.5" stroke-linejoin="round" />
      <defs>
        <linearGradient id="vcGrad" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stop-color="#ff6600" stop-opacity="0.45" />
          <stop offset="1" stop-color="#ff6600" stop-opacity="0.02" />
        </linearGradient>
      </defs>
      <!-- 数据点与标签 -->
      <g v-for="(d, i) in data" :key="d.vendor + d.model">
        <circle :cx="x(i)" :cy="y(d.tokens_per_cny)" r="4" :fill="dotColor(d.vendor)" stroke="#fff" stroke-width="1.5">
          <title>{{ d.vendor_display }} {{ d.model }}：{{ (d.tokens_per_cny).toFixed(2) }} 万 tokens/元（有效价 ¥{{ d.eff_cost_cny }}/M）</title>
        </circle>
        <text :x="x(i)" :y="y(d.tokens_per_cny) - 10" text-anchor="middle" font-size="11" fill="#d97706" font-weight="600">
          {{ d.tokens_per_cny >= 1 ? d.tokens_per_cny.toFixed(1) : d.tokens_per_cny.toFixed(2) }}
        </text>
        <text :x="x(i)" :y="H - M.bottom + 16" text-anchor="end" font-size="11" fill="#374151" :transform="`rotate(-40 ${x(i)} ${H - M.bottom + 16})`">
          {{ d.vendor_display }}·{{ d.model }}
        </text>
      </g>
      <!-- x 轴基线 -->
      <line :x1="M.left" :x2="W - M.right" :y1="H - M.bottom" :y2="H - M.bottom" stroke="#9ca3af" stroke-width="1.5" />
    </svg>
    <p class="vc-note">
      同模型国内外双列（智谱/Z.AI）为同价不同渠道。数据来源：各厂商官方价目页（captured_at 见 vendor.yml），
      GLM-5.3-Flash 为「5 折限时两周」促销价，到期后该点位将下移一半。
    </p>
  </div>
</template>

<style scoped>
.vc-wrap { max-width: 1200px; }
.vc-desc { font-size: 13px; color: #4b5563; }
.vc-svg { width: 100%; height: auto; }
.vc-note { font-size: 12px; color: #828282; }
</style>
