<script setup>
import { computed } from 'vue'
import plansData from '../plans.json'

const kindLabel = (k) => ({ deal: '优惠', warning: '坑点', note: '备注' }[k] || k)

// 按厂商分组，组内平铺（HN 式：标题行 + 灰色 meta 行）
const groups = computed(() => {
  const map = new Map()
  for (const it of plansData.intel || []) {
    if (!map.has(it.vendor)) {
      map.set(it.vendor, { vendor: it.vendor, target: it.target, items: [] })
    }
    map.get(it.vendor).items.push(it)
  }
  return [...map.values()]
})

let seq = 0
const flat = computed(() => {
  const rows = []
  for (const g of groups.value) {
    for (const it of g.items) rows.push({ ...it, vendorTarget: g.target, n: ++seq })
  }
  return rows
})

// 相对时间（HN 式 "N days ago" 的中文版）
function ageOf(it) {
  const d = it.expires ? Math.ceil((new Date(it.expires) - Date.now()) / 86400000) : null
  if (d == null || isNaN(d)) return '时限未核实'
  if (d <= 0) return '已过期'
  return `${d} 天后到期`
}
</script>

<template>
  <div class="hn-board">
    <div class="hn-header">
      <span class="hn-logo">📢</span>
      <span class="hn-title">情报板</span>
      <span class="hn-nav">
        <a :href="'#submit'">submit</a>
        <span class="hn-sep">|</span>
        <a href="https://github.com/OLmatter/llm-api-ledger" target="_blank" rel="noopener noreferrer">github</a>
      </span>
    </div>
    <div class="hn-list">
      <div v-if="!flat.length" class="hn-empty">暂无有效情报。有料？ submit 一条。</div>
      <div v-for="row in flat" :key="row.n" class="hn-row">
        <span class="hn-n">{{ row.n }}.</span>
        <div class="hn-main">
          <div class="hn-titleline">
            <span class="hn-vendor">{{ row.vendorTarget }}</span>
            <span class="hn-kind">[{{ kindLabel(row.kind) }}]</span>
            {{ row.text }}
          </div>
          <div class="hn-meta">
            {{ row.scope === 'plan' ? `${row.target}（仅该套餐）` : '该厂商全部套餐' }}
            | 渠道：{{ row.channel || '—' }}
            | {{ row.source === 'official' ? '官方' : '社区情报' }}
            | 登记于 {{ (row.date || '?').slice(0, 10) }}
            | {{ ageOf(row) }}
          </div>
        </div>
      </div>
    </div>
    <div id="submit" class="hn-submit">
      有情报要报？→
      <a href="https://github.com/OLmatter/llm-api-ledger/issues" target="_blank" rel="noopener noreferrer">提 Issue</a>
      或提 PR：在 <code>data/vendors/&lt;厂商&gt;.yml</code>（厂商通用）或
      <code>data/plans/&lt;套餐&gt;.yml</code>（挂具体套餐）加 <code>intel:</code> 字段。
      每条必填 <code>date</code>（登记时间，情报会过时）；限时情报必填 <code>expires</code>（铁律 11，过期自动摘）。灰色渠道一律标风险，榜单不背书。
    </div>
  </div>
</template>

<style scoped>
/* Hacker News 风格：橙头条 / 白底 / Verdana / 紧凑行 / 灰 meta */
.hn-board {
  font-family: Verdana, Geneva, 'Microsoft YaHei', sans-serif;
  font-size: 13.333px;
  color: #000;
  background: #fff;              /* 自带白底：暗色模式下保持 HN 白盒，黑字不随主题 */
  border: 1px solid #e0e0d0;
  padding: 8px;
  max-width: 900px;
}
.hn-header {
  background: #ff6600;
  color: #000;
  padding: 4px 8px;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13.333px;
}
.hn-logo { font-size: 15px; }
.hn-title { font-weight: 700; }
.hn-nav { margin-left: auto; font-size: 12px; }
.hn-nav a, .hn-titleline a { color: #000; text-decoration: none; }
.hn-nav a:hover { text-decoration: underline; }
.hn-sep { margin: 0 4px; color: rgba(0,0,0,0.4); }
.hn-list { padding: 8px 8px 0; }
.hn-empty { color: #828282; padding: 8px; }
.hn-row { display: flex; gap: 4px; padding: 5px 0; align-items: flex-start; }
.hn-row + .hn-row { border-top: 1px solid #f2f2f2; }
.hn-n { color: #828282; min-width: 20px; text-align: right; }
.hn-main { flex: 1; }
.hn-titleline { line-height: 1.45; }
.hn-vendor { font-weight: 700; color: #ff6600; margin-right: 4px; }
.hn-kind { color: #ff6600; margin-right: 4px; font-size: 12px; }
.hn-meta { color: #828282; font-size: 11px; margin-top: 2px; }
.hn-submit {
  margin: 16px 8px 8px;
  padding: 10px 12px;
  background: #f6f6ef;
  border: 1px solid #e0e0d0;
  font-size: 12px;
  color: #000;
  line-height: 1.6;
}
.hn-submit a { color: #ff6600; text-decoration: none; }
.hn-submit a:hover { text-decoration: underline; }
.hn-submit code { background: #eee; padding: 0 3px; font-size: 11px; }
</style>
