// 烧 MiniMax 5h 额度测试脚本
// 大 input + 小 output 策略：每请求 200K input tokens，1 token 输出
// 100M 额度只需 ~500 请求（约 17 分钟）
//
// 用法：node scripts/burn-quota.mjs

const PROBE_URL = 'http://127.0.0.1:8080'
const KEY_PATH = '/minimax/2/v1/chat/completions'
const MONITOR_URL = `${PROBE_URL}/__ledger__/api/keys/3/test-monitor`

const CONCURRENCY = 3
const MAX_OUTPUT_TOKENS = 1
const REPORT_EVERY = 5

// 预生成大 input（中文 ~2 char/token，约 160K tokens）
const FILLER = '人工智能技术在当今社会发展中扮演着越来越重要的角色，它正在改变我们的生活方式。'.repeat(8000)

let totalRequests = 0
let totalInputTokens = 0
let totalOutputTokens = 0
let errorStreak = 0
const startTs = Date.now()

async function sendRequest() {
  const body = JSON.stringify({
    model: 'MiniMax-M3',
    messages: [{ role: 'user', content: FILLER + '\n\n请回复 OK' }],
    max_tokens: MAX_OUTPUT_TOKENS,
    stream: false,
  })
  try {
    const resp = await fetch(`${PROBE_URL}${KEY_PATH}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body,
    })
    if (!resp.ok) {
      return { ok: false, status: resp.status, body: (await resp.text()).slice(0, 200) }
    }
    const data = await resp.json()
    const u = data.usage || {}
    return {
      ok: true,
      input: u.prompt_tokens || 0,
      output: u.completion_tokens || 0,
    }
  } catch (e) {
    return { ok: false, status: 0, body: String(e).slice(0, 200) }
  }
}

async function checkMonitor() {
  try {
    const r = await fetch(MONITOR_URL)
    const d = await r.json()
    const h5 = (d.periods || []).find(p => p.period_type === 'tokens_5h')
    return h5 ? { remainingPct: 100 - h5.percentage * 100 } : null
  } catch { return null }
}

function fmt(n) {
  if (n >= 1e9) return (n / 1e9).toFixed(2) + 'B'
  if (n >= 1e6) return (n / 1e6).toFixed(2) + 'M'
  if (n >= 1e3) return (n / 1e3).toFixed(1) + 'K'
  return String(n)
}

function printFinal(reason) {
  const el = (Date.now() - startTs) / 1000
  console.log(`\n=== 最终统计 (${reason}) ===`)
  console.log(`耗时: ${el.toFixed(0)}s`)
  console.log(`总请求: ${totalRequests}`)
  console.log(`入 tokens: ${fmt(totalInputTokens)}`)
  console.log(`出 tokens: ${fmt(totalOutputTokens)}`)
  console.log(`总 tokens: ${fmt(totalInputTokens + totalOutputTokens)}`)
}

async function worker(workerId) {
  while (true) {
    const r = await sendRequest()
    totalRequests++
    if (r.ok) {
      totalInputTokens += r.input
      totalOutputTokens += r.output
      errorStreak = 0
    } else {
      errorStreak++
      console.log(`[w${workerId}] err#${errorStreak} status=${r.status} body=${r.body}`)
      if (errorStreak >= 5) {
        printFinal('连续 5 次错误')
        process.exit(1)
      }
    }
    if (totalRequests % REPORT_EVERY === 0) {
      const el = (Date.now() - startTs) / 1000
      const rate = totalRequests / el
      const mon = await checkMonitor()
      const pctStr = mon ? `5h剩 ${mon.remainingPct.toFixed(0)}%` : 'mon?'
      console.log(
        `[${el.toFixed(0)}s] req=${totalRequests} (${rate.toFixed(2)}/s) ` +
        `入=${fmt(totalInputTokens)} 出=${fmt(totalOutputTokens)} ` +
        `总=${fmt(totalInputTokens + totalOutputTokens)} ${pctStr}`
      )
      if (mon && mon.remainingPct <= 1) {
        printFinal('5h 触顶')
        process.exit(0)
      }
    }
  }
}

console.log(`=== MiniMax 5h 烧额度测试 ===`)
console.log(`策略: 大 input(${(FILLER.length / 2 / 1000).toFixed(0)}K tokens 估) + 小 output(${MAX_OUTPUT_TOKENS} token)`)
console.log(`并发: ${CONCURRENCY}, 每 ${REPORT_EVERY} 请求报一次`)
console.log(`Ctrl+C 中止\n`)

const workers = []
for (let i = 0; i < CONCURRENCY; i++) workers.push(worker(i))
await Promise.all(workers)
printFinal('完成')
