// 截图工具：自动去掉底部多余空白
//
// 用法：
//   node scripts/screenshot.mjs <url> <out.png> [--width=1980] [--max-height=12000]
//
// 退出码：0 成功 / 1 失败

import { execSync, spawnSync } from 'node:child_process'
import { statSync, existsSync } from 'node:fs'
import { resolve as resolvePath, isAbsolute } from 'node:path'

const args = process.argv.slice(2)
if (args.length < 2) {
  console.error('用法: node scripts/screenshot.mjs <url> <out.png> [--width=1980] [--max-height=12000]')
  process.exit(1)
}

const url = args[0]
const outPath = isAbsolute(args[1]) ? args[1] : resolvePath(args[1])
const width = parseInt((args.find(a => a.startsWith('--width=')) || '--width=1980').slice(8), 10)
const maxHeight = parseInt((args.find(a => a.startsWith('--max-height=')) || '--max-height=12000').slice(13), 10)

const chrome = 'C:/Program Files/Google/Chrome/Application/chrome.exe'

// 1. 大图兜底截图
console.log(`[1/2] 大图兜底截图 ${width}x${maxHeight} ...`)
try {
  execSync(
    `"${chrome}" --headless --disable-gpu --no-sandbox --hide-scrollbars ` +
    `--window-size=${width},${maxHeight} ` +
    `--virtual-time-budget=20000 ` +
    `--run-all-compositor-stages-before-draw ` +
    `--screenshot="${outPath}" ` +
    `"${url}"`,
    { stdio: ['pipe', 'pipe', 'pipe'] }
  )
} catch (e) {
  console.error('chrome 截图失败:', e.message.slice(0, 200))
  process.exit(1)
}

if (!existsSync(outPath)) {
  console.error(`截图未生成: ${outPath}`)
  process.exit(1)
}

// 2. PIL 找最底部非白像素 + 裁剪
console.log('[2/2] PIL 裁剪底部空白 ...')
const pyResult = spawnSync('python', ['-c',
  `from PIL import Image
im = Image.open(r"${outPath.replace(/\\/g, '\\\\')}")
W, H = im.size
pixels = im.convert('L').load()
# 从底部往上找第一个有内容的行
last_content = 0
for y in range(H - 1, -1, -1):
    row_min = min(pixels[x, y] for x in range(0, W, 50))
    if row_min < 250:
        last_content = y
        break
trim_height = last_content + 100  # +100 padding
trim = im.crop((0, 0, W, trim_height))
trim.save(r"${outPath.replace(/\\/g, '\\\\')}")
print(f"trimmed to {W}x{trim_height}")`
], { encoding: 'utf-8' })

if (pyResult.status !== 0) {
  console.error('PIL 裁剪失败:', pyResult.stderr.slice(0, 200))
  process.exit(1)
}

const size = statSync(outPath).size
const match = pyResult.stdout.match(/trimmed to (\d+)x(\d+)/)
const finalH = match ? match[2] : '?'
console.log(`✓ ${outPath} (${width}x${finalH}, ${Math.round(size / 1024)} KB)`)