#!/usr/bin/env python3
"""
临时静态服务器：支持 vitepress base path + SPA fallback
用于 headless chrome 截图（避免 vitepress preview 不做 base path rewrite）

用法：
  python scripts/_screenshot-server.py [ROOT] [PORT]
  python scripts/_screenshot-server.py docs/.vitepress/dist 4173
"""

import http.server
import sys
from urllib.parse import urlparse

PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 4173
ROOT = sys.argv[1] if len(sys.argv) > 1 else 'docs/.vitepress/dist'
BASE_PREFIX = '/llm-api-ledger/'


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=ROOT, **kwargs)

    def do_GET(self):
        # 不带 /llm-api-ledger/ 前缀的页面路径 → 302 补前缀
        # （否则 SSR 能返回内容，但前端 router 因 base 不匹配 hydration 后跳 404）
        path_only = self.path.split('?')[0]
        if not path_only.startswith(BASE_PREFIX) and '.' not in path_only.split('/')[-1] and path_only != '/':
            self.send_response(302)
            self.send_header('Location', BASE_PREFIX.rstrip('/') + path_only)
            self.end_headers()
            return
        # 去掉 /llm-api-ledger/ 前缀，转发给实际文件
        if self.path.startswith(BASE_PREFIX):
            self.path = self.path[len(BASE_PREFIX):]
        # 路径不含 . ：先试 cleanUrls 的 <path>.html（如 /intel → intel.html），否则 fallback index.html
        path = self.path.split('?')[0]
        if '.' not in path.split('/')[-1]:
            import os
            candidate = path.rstrip('/') + '.html'
            if os.path.exists(os.path.join(ROOT, candidate.lstrip('/'))):
                self.path = candidate
            else:
                self.path = 'index.html'
        return super().do_GET()


if __name__ == '__main__':
    print(f'Serving {ROOT} on http://127.0.0.1:{PORT}{BASE_PREFIX}')
    http.server.HTTPServer(('127.0.0.1', PORT), Handler).serve_forever()