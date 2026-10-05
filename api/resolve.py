import json
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import yt_dlp

class handler(BaseHTTPRequestHandler):
    def _send(self, code, obj=None):
        self.send_response(code)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        if obj is not None:
            self.wfile.write(json.dumps(obj).encode())

    def do_OPTIONS(self):
        self._send(204)

def do_GET(self):
    query = parse_qs(urlparse(self.path).query)
    target = query.get("url", [""])[0]
    
    # CLI-style flags as query params
    format_opt = query.get("f", ["best"])[0]           # -f or --format
    quality = query.get("q", [""])[0]                  # --quality preference
    cookies_from_browser = query.get("cookies", [None])[0]  # --cookies-from-browser
    referer = query.get("r", [None])[0]                # --referer
    
    if not target.startswith(("http://", "https://")):
        return self._send(400, {"error": "use ?url=http(s)://..."})
    
    opts = {"quiet": True, "no_warnings": True, "noplaylist": True,
            "skip_download": True, "cache_dir": False, "socket_timeout": 15,
            "format": format_opt}  # ← Use dynamic format
    
    # Optional: add browser cookies if provided
    if cookies_from_browser:
        opts["cookiefrombrowser"] = cookies_from_browser
    
    # Optional: add referer if provided
    if referer:
        opts["http_headers"] = {"Referer": referer}
    
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(target, download=False)
        hdrs = info.get("http_headers") or {}
        self._send(200, {"url": info.get("url"), "title": info.get("title"),
                         "referer": hdrs.get("Referer") or info.get("webpage_url")})
    except Exception as e:
        self._send(502, {"error": str(e).splitlines()[-1][:300]})
        
    # Suppress log messages (optional, makes console cleaner)
    def log_message(self, format, *args):
        pass
