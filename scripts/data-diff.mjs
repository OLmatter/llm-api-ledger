// AIDASH 数据 Diff 工具（commit 前自动跑）
//
// 目的：对比 working tree vs HEAD 的 data/vendors/*.yml + data/plans/*.yml 改动
//       按「厂商 × 套餐粒度」列出「新增 / 消失 / 字段变化」三类，**默认只关注
//       用户最关心的字段**（价格、用量、限额、邀请码、状态），其他字段不报告
//       减少噪音。
//
// 用法：
//   node scripts/data-diff.mjs               # 对比 working tree vs HEAD
//   node scripts/data-diff.mjs --base <ref>  # 对比 working tree vs 指定 ref
//   node scripts/data-diff.mjs --all         # 显示所有字段变化（噪音模式）
//   node scripts/data-diff.mjs --json        # 输出 JSON 给脚本消费
//
// 退出码：
//   0 = 无数据改动 或 改动都在关注字段内
//   1 = 改动了但 build/lint 失败
//   2 = 改动了关注字段（仅在 CI/hook 模式下用，正常手动跑也返回 0）

import yaml from 'js-yaml'
import { readFileSync, existsSync } from 'node:fs'
import { execSync } from 'node:child_process'
import { join, dirname } from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = dirname(fileURLToPath(import.meta.url))
const root = join(__dirname, '..')
const args = process.argv.slice(2)
const baseRef = (args.find(a => a.startsWith('--base=')) || '--base=HEAD').slice(7)
const showAll = args.includes('--all')
const jsonOut = args.includes('--json')

// 关注的字段（用户最关心的——改这些会直接影响榜单）
const PLAN_FIELDS_WATCH = [
  'plan_name', 'plan_tier', 'status', 'vendor', 'tier_multiplier',
  'last_verified', 'tokens_inference_disabled',
]
const PRICING_FIELDS_WATCH = [
  'currency', 'original_monthly', 'original_quarterly', 'original_yearly',
  'intro_monthly', 'intro_quarterly', 'intro_yearly',
  'yearly_total', 'yearly_monthly_equivalent', 'price_warning',
]
const LIMITS_FIELDS_WATCH = [
  // 5h/周/月三个窗口都包含的子字段
  'requests_official', 'tokens_measured', 'tokens_official_claimed',
  'tokens_scenario_estimate', 'cost_limit_usd',
  'credits_5h', 'credits_weekly', 'credits_monthly', 'credits_monthly_estimated',
  'monthly_estimated', 'is_unlimited', 'cost_limit_disputed', 'cost_limit_credibility',
]

const VENDOR_FIELDS_WATCH = [
  'vendor_display', 'vendor_display_en', 'brand_color', 'last_verified', 'homepage',
  // affiliate 子字段
]

// 倍数 / 比率字段（铁律 13 关联：tier 排序用 tier_multiplier）
const RATIO_FIELDS_WATCH = [
  'tier_multiplier',     // plan.yml 顶部，整套餐的 tier 倍数
  'tier_ratio',          // measurement 内，sibling 反推的 tier 比例
  'ratio_note',          // 比率说明注释（lang 字符串，整段改动也算）
  'rate_multipliers',    // vendor.yml 内的高峰/非高峰倍率
]

// measurements 数组由 diffMeasurements() 单独精细处理（按 model_id 拆）
// 主 flatten 跳过 'measurements' 字段（避免冗余的 "[N items] → [N items]" 噪音）
// 所以这里不再需要 MODEL_FIELDS_WATCH

const C = {
  reset: '\x1b[0m', bold: '\x1b[1m', dim: '\x1b[2m',
  red: '\x1b[31m', green: '\x1b[32m', yellow: '\x1b[33m',
  blue: '\x1b[34m', magenta: '\x1b[35m', cyan: '\x1b[36m',
  gray: '\x1b[90m',
}

function readYmlAtRef(file, ref) {
  // 从 git 读指定 ref 的 yml 内容
  const rel = file.replace(/\\/g, '/').replace(/^.*?data\//, 'data/')
  try {
    const out = execSync(`git show ${ref}:${rel}`, { cwd: root, encoding: 'utf-8', stdio: ['pipe', 'pipe', 'ignore'] })
    return yaml.load(out) || {}
  } catch (e) {
    return null  // 文件在 ref 中不存在（新增）
  }
}

function readYmlAtWorking(file) {
  if (!existsSync(file)) return null
  return yaml.load(readFileSync(file, 'utf-8')) || {}
}

function getChangedFiles(ref) {
  // 返回 working tree 相对 ref 改动的 yml 文件路径列表（包含 intent-to-add 的新文件）
  const out = execSync(
    `git diff --name-only --diff-filter=AMDR ${ref} -- data/`,
    { cwd: root, encoding: 'utf-8', stdio: ['pipe', 'pipe', 'ignore'] }
  ).trim()
  // 补：未追踪但被删的 yml（曾经 `git add -N` 过的文件被 rm 了，git diff 看不到）
  // git status --porcelain 对这种状态输出 "D path"（D 在第一列 = staged-as-deleted，
  // 但因为 git add -N 没真正 add 内容，git diff 也看不到）。要兜住这个口子。
  const porcelain = execSync(
    `git status --porcelain -- data/`,
    { cwd: root, encoding: 'utf-8', stdio: ['pipe', 'pipe', 'ignore'] }
  ).trim()
  const deletedUntracked = []
  for (const line of porcelain.split('\n')) {
    // 两种删除格式（X 是 staged 状态，Y 是 working tree 状态）：
    //   "D  path" 或 " D path" 都表示文件被删
    // 用宽松正则：第 1 或第 2 字符是 D 即视为删除
    if (line.length >= 2 && (line[0] === 'D' || line[1] === 'D')) {
      const m = line.match(/\s(\S+\.yml)$/)
      if (m) deletedUntracked.push(m[1])
    }
  }
  const allFiles = out ? out.split('\n') : []
  const merged = [...new Set([...allFiles, ...deletedUntracked])]
  if (merged.length === 0) return []
  // 返回绝对路径（下游 readYmlAtWorking / readYmlAtRef 需要）
  return merged.map(f => join(root, f.replace(/\\/g, '/')))
}

function flatten(obj, prefix = '') {
  if (obj == null) return {}
  if (typeof obj !== 'object') return { [prefix]: obj }
  if (Array.isArray(obj)) {
    const out = {}
    obj.forEach((v, i) => {
      Object.assign(out, flatten(v, `${prefix}[${i}]`))
    })
    return out
  }
  const out = {}
  for (const [k, v] of Object.entries(obj)) {
    const key = prefix ? `${prefix}.${k}` : k
    if (v != null && typeof v === 'object' && !Array.isArray(v)) {
      Object.assign(out, flatten(v, key))
    } else {
      out[key] = v
    }
  }
  return out
}

function isWatched(field) {
  if (showAll) return true
  if (PLAN_FIELDS_WATCH.includes(field)) return true
  // pricing.<field> 形式
  if (field.startsWith('pricing.')) {
    const sub = field.slice('pricing.'.length)
    if (PRICING_FIELDS_WATCH.includes(sub)) return true
  }
  // limits.window_X.<field> 形式
  if (field.startsWith('limits.window_5h.') || field.startsWith('limits.window_weekly.') || field.startsWith('limits.window_monthly.')) {
    const sub = field.split('.', 3)[2]
    if (LIMITS_FIELDS_WATCH.includes(sub)) return true
  }
  // vendor.affiliate.* 形式（用 flatten 后的全路径）
  if (field.startsWith('affiliate.')) {
    return true
  }
  if (VENDOR_FIELDS_WATCH.includes(field)) return true
  if (RATIO_FIELDS_WATCH.includes(field)) return true
  return false
}

function diffPlans(oldPlans, newPlans) {
  const result = { added: [], removed: [], changed: [] }
  const oldMap = new Map(oldPlans.map(p => [p.plan_id, p]))
  const newMap = new Map(newPlans.map(p => [p.plan_id, p]))
  // added + changed
  for (const [id, np] of newMap) {
    const op = oldMap.get(id)
    if (!op) {
      result.added.push(np)
      continue
    }
    const of = flatten(op), nf = flatten(np)
    const changes = []
    for (const k of new Set([...Object.keys(of), ...Object.keys(nf)])) {
      if (JSON.stringify(of[k]) !== JSON.stringify(nf[k])) {
        // measurements 数组由下面 diffMeasurements 精细处理，主 flatten 跳过避免冗余
        if (k === 'measurements') continue
        if (isWatched(k)) {
          changes.push({ field: k, old: of[k], neu: nf[k] })
        }
      }
    }
    // 额外：measurements 数组按 model_id / measurement_id 做精细 diff
    // 解决 flatten 把整个数组压成 "measurements: [N items]" 看不到内部 model 增删的问题
    const modelChanges = diffMeasurements(op.measurements || [], np.measurements || [])
    if (modelChanges.length > 0) {
      changes.push(...modelChanges)
    }
    if (changes.length > 0) {
      result.changed.push({ plan_id: id, plan_name: np.plan_name, vendor: np.vendor, changes })
    }
  }
  // removed
  for (const [id, op] of oldMap) {
    if (!newMap.has(id)) {
      result.removed.push(op)
    }
  }
  return result
}

// 按 (model_id | measurement_id) 拆分 measurements 数组，返回扁平化改动列表
// 每条改动形如 { field: "@模型 deepseek-v4-flash.model_id", old, neu }
// 或者 { field: "@模型 kimi-k2.7 (新增)", ... }
function diffMeasurements(oldArr, newArr) {
  const changes = []
  const keyOf = (m) => m.model_id || m.measurement_id || JSON.stringify(m).slice(0, 50)
  const oldMap = new Map(oldArr.map(m => [keyOf(m), m]))
  const newMap = new Map(newArr.map(m => [keyOf(m), m]))
  // 新增
  for (const [k, nm] of newMap) {
    if (!oldMap.has(k)) {
      const label = nm.model_id ? `@模型 ${nm.model_id}` : `@measurement ${nm.measurement_id}`
      changes.push({ field: `${label} (新增)`, old: null, neu: `${nm.measurement_id ?? '?'}` })
    }
  }
  // 删除
  for (const [k, om] of oldMap) {
    if (!newMap.has(k)) {
      const label = om.model_id ? `@模型 ${om.model_id}` : `@measurement ${om.measurement_id}`
      changes.push({ field: `${label} (删除)`, old: `${om.measurement_id ?? '?'}`, neu: null })
    }
  }
  // 改字段
  for (const [k, nm] of newMap) {
    const om = oldMap.get(k)
    if (!om) continue
    const of = flatten(om), nf = flatten(nm)
    const watched = new Set(['model_id', 'requests_5h', 'requests_weekly', 'requests_monthly',
                              'window_5h_tokens', 'window_weekly_tokens', 'window_monthly_tokens',
                              'input_per_million', 'output_per_million', 'cached_per_million',
                              'cost_per_request', 'cost_per_million', 'credibility', 'disputed',
                              'source_kind', 'scope'])
    const label = nm.model_id ? `@模型 ${nm.model_id}` : `@measurement ${nm.measurement_id}`
    for (const f of new Set([...Object.keys(of), ...Object.keys(nf)])) {
      // 只看顶层字段（flatten 会出 measurements[0].x，这里我们只关心同名 measurement 内的顶层字段）
      const sub = f.includes('.') ? f.split('.').pop() : f
      if (JSON.stringify(of[f]) !== JSON.stringify(nf[f]) && watched.has(sub)) {
        changes.push({ field: `${label}.${sub}`, old: of[f], neu: nf[f] })
      }
    }
  }
  return changes
}

function diffVendors(oldVendors, newVendors) {
  const result = { added: [], removed: [], changed: [] }
  const oldMap = new Map(oldVendors.map(v => [v.vendor_id, v]))
  const newMap = new Map(newVendors.map(v => [v.vendor_id, v]))
  for (const [id, nv] of newMap) {
    const ov = oldMap.get(id)
    if (!ov) { result.added.push(nv); continue }
    const of = flatten(ov), nf = flatten(nv)
    const changes = []
    for (const k of new Set([...Object.keys(of), ...Object.keys(nf)])) {
      if (JSON.stringify(of[k]) !== JSON.stringify(nf[k])) {
        if (isWatched(k)) {
          changes.push({ field: k, old: of[k], neu: nf[k] })
        }
      }
    }
    if (changes.length > 0) {
      result.changed.push({ vendor_id: id, vendor_display: nv.vendor_display, changes })
    }
  }
  for (const [id, ov] of oldMap) {
    if (!newMap.has(id)) result.removed.push(ov)
  }
  return result
}

function fmtVal(v) {
  if (v == null) return C.gray + 'null' + C.reset
  if (typeof v === 'string') return `"${v.length > 40 ? v.slice(0, 40) + '...' : v}"`
  if (typeof v === 'number') return String(v)
  if (typeof v === 'boolean') return String(v)
  if (Array.isArray(v)) return `[${v.length} items]`
  return JSON.stringify(v).slice(0, 50)
}

function colorizeChange(old, neu) {
  // 数字类型 → 看增减
  if (typeof old === 'number' && typeof neu === 'number') {
    if (neu > old) return C.green + neu + C.reset + C.gray + ' (↑)' + C.reset
    if (neu < old) return C.red + neu + C.reset + C.gray + ' (↓)' + C.reset
  }
  return C.yellow + fmtVal(neu) + C.reset
}

function printReport(planDiff, vendorDiff, buildOk) {
  const lines = []
  const bar = '═'.repeat(60)
  lines.push('')
  lines.push(`${C.bold}📊 AIDASH 数据 Diff (vs ${baseRef})${C.reset}`)
  lines.push(bar)
  // 套餐
  const planChanged = planDiff.added.length + planDiff.removed.length + planDiff.changed.length
  if (planDiff.added.length > 0) {
    lines.push(`${C.green}${C.bold}🆕 新增套餐 (${planDiff.added.length})${C.reset}`)
    for (const p of planDiff.added) {
      const cur = p.limits?.window_5h?.cost_limit_usd ? `$${p.limits.window_5h.cost_limit_usd}` :
                  p.pricing?.original_monthly ? `${p.pricing.currency || '¥'}${p.pricing.original_monthly}` : ''
      const lim = p.limits?.window_5h?.requests_official
      const tok = p.limits?.window_5h?.tokens_measured || p.limits?.window_5h?.tokens_official_claimed
      const limStr = lim ? ` / 5h ${lim}次` : (tok ? ` / 5h ${(tok/1e6).toFixed(0)}M tok` : '')
      lines.push(`  ${C.green}+${C.reset} ${C.cyan}${p.vendor}/${p.plan_id}${C.reset}  ${cur}${limStr}`)
    }
    lines.push('')
  }
  if (planDiff.removed.length > 0) {
    lines.push(`${C.red}${C.bold}🗑️  消失套餐 (${planDiff.removed.length})${C.reset}`)
    for (const p of planDiff.removed) {
      lines.push(`  ${C.red}-${C.reset} ${C.cyan}${p.vendor}/${p.plan_id}${C.reset}  (${p.plan_name})`)
    }
    lines.push('')
  }
  if (planDiff.changed.length > 0) {
    lines.push(`${C.yellow}${C.bold}⚠️  套餐字段变化 (${planDiff.changed.length})${C.reset}`)
    for (const { plan_id, plan_name, vendor, changes } of planDiff.changed) {
      lines.push(`  ${C.cyan}${vendor}/${plan_id}${C.reset} ${C.dim}(${plan_name})${C.reset}`)
      for (const { field, old, neu } of changes) {
        lines.push(`    ${C.dim}${field}${C.reset}: ${fmtVal(old)} → ${colorizeChange(old, neu)}`)
      }
    }
    lines.push('')
  }
  // 厂商
  const vendorChanged = vendorDiff.added.length + vendorDiff.removed.length + vendorDiff.changed.length
  if (vendorChanged > 0) {
    lines.push(`${C.magenta}${C.bold}🔧 厂商字段变化 (${vendorChanged})${C.reset}`)
    for (const v of vendorDiff.added) {
      lines.push(`  ${C.green}+${C.reset} ${C.cyan}${v.vendor_id}${C.reset}  (${v.vendor_display})`)
    }
    for (const v of vendorDiff.removed) {
      lines.push(`  ${C.red}-${C.reset} ${C.cyan}${v.vendor_id}${C.reset}  (${v.vendor_display})`)
    }
    for (const { vendor_id, vendor_display, changes } of vendorDiff.changed) {
      lines.push(`  ${C.cyan}${vendor_id}${C.reset} ${C.dim}(${vendor_display})${C.reset}`)
      for (const { field, old, neu } of changes) {
        lines.push(`    ${C.dim}${field}${C.reset}: ${fmtVal(old)} → ${colorizeChange(old, neu)}`)
      }
    }
    lines.push('')
  }
  if (planChanged === 0 && vendorChanged === 0) {
    lines.push(`${C.gray}无关注的字段改动 (yml 改了但不在关注列表) — 跑 --all 看全部${C.reset}`)
    lines.push('')
  }
  // build 状态
  if (buildOk) {
    lines.push(`${C.green}✓${C.reset} plans.json build 成功`)
  } else {
    lines.push(`${C.red}✗${C.reset} plans.json build 失败（先跑 npm run build:plans 排查）`)
  }
  lines.push(bar)
  console.log(lines.join('\n'))
}

function main() {
  // 0. 校验 ref 存在（避免不存在的 ref 让 git 命令 crash）
  // 注意：不加 ^{commit} 后缀（Windows shell 解析 ^ 会失败）
  try {
    execSync(`git rev-parse --verify ${baseRef}`, { cwd: root, stdio: ['pipe', 'pipe', 'ignore'] })
  } catch (e) {
    console.error(`${C.red}✗${C.reset} ref "${baseRef}" 不存在或不是 commit。请检查：`)
    console.error(`  - HEAD / main（默认）`)
    console.error(`  - HEAD~N / HEAD@{N}（祖先提交 / reflog）`)
    console.error(`  - <branch-name> / <tag-name> / <commit-sha>`)
    process.exit(1)
  }
  // 1. 列改动文件
  const changedFiles = getChangedFiles(baseRef)
  // 2. 拆分 vendor / plan
  const oldVendors = []
  const newVendors = []
  const oldPlans = []
  const newPlans = []
  for (const f of changedFiles) {
    // 统一路径分隔符（Windows 反斜杠 → 斜杠），然后定位 data/ 部分
    const normalized = f.replace(/\\/g, '/')
    const base = normalized.replace(/^.*?data\//, 'data/')
    if (base.startsWith('data/vendors/') && base.endsWith('.yml')) {
      const ov = readYmlAtRef(f, baseRef)
      const nv = readYmlAtWorking(f)
      if (ov?.vendor_id) oldVendors.push(ov)
      if (nv?.vendor_id) newVendors.push(nv)
    } else if (base.startsWith('data/plans/') && base.endsWith('.yml')) {
      const op = readYmlAtRef(f, baseRef)
      const np = readYmlAtWorking(f)
      if (op?.plan_id) oldPlans.push(op)
      if (np?.plan_id) newPlans.push(np)
    }
  }
  // 3. 跑 build 验证
  let buildOk = true
  try {
    execSync('node scripts/build-plans.mjs 2>&1 | tail -3', { cwd: root, encoding: 'utf-8', stdio: ['pipe', 'pipe', 'pipe'] })
  } catch (e) {
    buildOk = false
  }
  // 4. diff
  const planDiff = diffPlans(oldPlans, newPlans)
  const vendorDiff = diffVendors(oldVendors, newVendors)
  // 5. 输出
  if (jsonOut) {
    console.log(JSON.stringify({ planDiff, vendorDiff, buildOk }, null, 2))
  } else {
    printReport(planDiff, vendorDiff, buildOk)
  }
  process.exit(buildOk ? 0 : 1)
}

main()
