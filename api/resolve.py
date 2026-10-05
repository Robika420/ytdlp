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
        target = (parse_qs(urlparse(self.path).query).get("url") or [""])[0]
        if not target.startswith(("http://", "https://")):
            return self._send(400, {"error": "use ?url=http(s)://..."})
        
        # FIXED FORMAT SELECTOR - more compatible
        opts = {"quiet": True, "no_warnings": True, "noplaylist": True,
                "skip_download": True, "cache_dir": False, "socket_timeout": 15,
                "format": "best"}
        
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(target, download=False)
            hdrs = info.get("http_headers") or {}
            
            self._send(200, {
                "url": info.get("url"), 
                "title": info.get("title"),
                "thumbnail": info.get("thumbnail"),
                "duration": info.get("duration"),
                "referer": hdrs.get("Referer") or info.get("webpage_url")
            })
        except Exception as e:
            self._send(502, {"error": str(e).splitlines()[-1][:300]})
    
    # Suppress log messages (optional, makes console cleaner)
    def log_message(self, format, *args):
        pass
