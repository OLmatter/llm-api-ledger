"""
CDP-based dump for SPA pages that Chrome --dump-dom can't capture.
Usage: python scripts/_cdp_dump.py <url> <wait_seconds> <output_path>

Examples:
  python scripts/_cdp_dump.py "https://platform.openai.com/docs/pricing" 25 data/openai/official/2026-07-31_openai_api_pricing.txt
  python scripts/_cdp_dump.py "https://help.openai.com/en/articles/8914235" 30 /tmp/help.txt

Why this exists:
- Chrome --dump-dom only returns the initial HTML (skeleton) for SPA pages
- pages behind Cloudflare Turnstile may show "Please wait..." title even after long waits
- This script uses Chrome DevTools Protocol via websocket, waits for JS to render,
  then extracts document.body.innerText and saves it
"""
import subprocess
import time
import os
import sys
import urllib.request
import json

try:
    import websocket
except ImportError:
    print('pip install websocket-client', file=sys.stderr)
    sys.exit(1)


def main():
    url = sys.argv[1] if len(sys.argv) > 1 else 'https://platform.openai.com/docs/pricing'
    wait = int(sys.argv[2]) if len(sys.argv) > 2 else 25
    output = sys.argv[3] if len(sys.argv) > 3 else 'C:/Users/520hh/AppData/Local/Temp/cdp_dump.txt'

    user_data_dir = 'C:\\Users\\520hh\\AppData\\Local\\Temp\\chrome_cdp_' + str(int(time.time()))
    chrome_proc = subprocess.Popen([
        r'C:\Program Files\Google\Chrome\Application\chrome.exe',
        '--headless=new', '--disable-gpu', '--no-sandbox',
        '--remote-debugging-port=9222',
        '--remote-allow-origins=*',
        f'--user-data-dir={user_data_dir}',
        url
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    time.sleep(5)
    try:
        tabs = json.loads(urllib.request.urlopen('http://localhost:9222/json').read())
        target = next((t for t in tabs if t.get('type') == 'page'), tabs[0])
        ws = websocket.create_connection(target['webSocketDebuggerUrl'])

        msg_id = [1]
        def send(method, params=None):
            msg = {'id': msg_id[0], 'method': method}
            if params: msg['params'] = params
            msg_id[0] += 1
            ws.send(json.dumps(msg))
            while True:
                r = json.loads(ws.recv())
                if r.get('id') == msg['id']:
                    return r

        print(f'Waiting {wait}s for JS render...', file=sys.stderr)
        time.sleep(wait)

        result = send('Runtime.evaluate', {
            'expression': '({title: document.title, bodyLen: document.body ? document.body.innerText.length : 0, bodyText: document.body ? document.body.innerText : ""})',
            'returnByValue': True
        })
        val = result['result']['result']['value']
        print(f"Title: {val['title']}", file=sys.stderr)
        print(f"Body text length: {val['bodyLen']}", file=sys.stderr)

        os.makedirs(os.path.dirname(output) or '.', exist_ok=True)
        with open(output, 'w', encoding='utf-8') as f:
            f.write(f"# Title: {val['title']}\n")
            f.write(f"# Body length: {val['bodyLen']}\n")
            f.write(f"# Source URL: {url}\n")
            f.write(f"# Captured at: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(val['bodyText'])
        print(f'Saved to {output}', file=sys.stderr)
    finally:
        chrome_proc.terminate()
        time.sleep(1)
        if chrome_proc.poll() is None:
            chrome_proc.kill()


if __name__ == '__main__':
    main()