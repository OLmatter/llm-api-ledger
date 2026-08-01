"""
Playwright + stealth scraper for Cloudflare Turnstile-protected sites.

Why this exists:
- chrome --dump-dom and CDP Runtime.evaluate both fail on consumer-facing
  Cloudflare-protected domains (chatgpt.com, openai.com/, help.openai.com)
- The Cloudflare Turnstile JS challenge requires browser environment with
  full fingerprint (canvas, webgl, navigator plugins)
- playwright-stealth patches navigator.* / WebGL vendor / Chrome runtime
  to look like a real desktop Chrome

Caveats:
- Cloudflare IP rate-limits after 1 request: wait 5+ min between attempts
- Prices may still not render if API requires auth cookie or region
- Use scripts/_cdp_dump.py first (lighter, no stealth); only escalate to this

Usage:
  python scripts/_stealth_dump.py <url> <output.txt> <wait_seconds>

Examples:
  python scripts/_stealth_dump.py "https://chatgpt.com/pricing" /tmp/chatgpt.txt 60
  python scripts/_stealth_dump.py "https://openai.com/chatgpt/" /tmp/openai.txt 30
"""
import sys
import time
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth

URL = sys.argv[1] if len(sys.argv) > 1 else 'https://chatgpt.com/pricing'
OUTPUT = sys.argv[2] if len(sys.argv) > 2 else 'C:/Users/520hh/AppData/Local/Temp/stealth_dump.txt'
WAIT = int(sys.argv[3]) if len(sys.argv) > 3 else 30
SCREENSHOT = OUTPUT.replace('.txt', '.png')

stealth = Stealth(
    navigator_languages_override=('en-US', 'en'),
    navigator_platform_override='Win32',
    navigator_user_agent_override='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    webgl_vendor_override='Intel Inc.',
    webgl_renderer_override='ANGLE (Intel, Intel(R) UHD Graphics 620 Direct3D11 vs_5_0 ps_5_0)',
)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(
        viewport={'width': 1920, 'height': 1080},
        locale='en-US',
        timezone_id='America/Los_Angeles',
        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    )
    stealth.apply_stealth_sync(context)
    page = context.new_page()

    print(f'Navigating to {URL}...', file=sys.stderr)
    page.goto(URL, wait_until='domcontentloaded', timeout=60000)
    print(f'Waiting {WAIT}s for JS render...', file=sys.stderr)
    time.sleep(WAIT)

    title = page.title()
    body_text = page.evaluate('document.body ? document.body.innerText : ""')

    # Detect Turnstile block
    blocked = 'Just a moment' in body_text or '请稍候' in body_text

    print(f'Title: {title}', file=sys.stderr)
    print(f'Body length: {len(body_text)}', file=sys.stderr)
    if blocked:
        print('⚠ BLOCKED: Cloudflare Turnstile challenge detected', file=sys.stderr)

    with open(OUTPUT, 'w', encoding='utf-8') as f:
        f.write(f'# Title: {title}\n')
        f.write(f'# Body length: {len(body_text)}\n')
        f.write(f'# Source URL: {URL}\n')
        f.write(f'# Captured at: {time.strftime("%Y-%m-%d %H:%M:%S")}\n')
        f.write(f'# Method: playwright + stealth\n')
        f.write(f'# Blocked: {blocked}\n\n')
        f.write(body_text)
    print(f'Saved to {OUTPUT}', file=sys.stderr)

    page.screenshot(path=SCREENSHOT, full_page=True)
    print(f'Screenshot: {SCREENSHOT}', file=sys.stderr)

    browser.close()

    if blocked:
        sys.exit(1)