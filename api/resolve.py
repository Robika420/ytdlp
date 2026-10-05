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
        
        # CLI-like flags
        fmt = query.get("f", ["best"])[0]
        cookies_browser = query.get("cookies", [None])[0]
        referer_hdr = query.get("r", [None])[0]
        prefer_hls = query.get("hls", ["false"])[0].lower() == "true"
        
        if not target.startswith(("http://", "https://")):
            return self._send(400, {"error": "use ?url=http(s)://..."})
        
        # Build opts
        opts = {
            "quiet": True,
            "no_warnings": True,
            "noplaylist": True,
            "skip_download": True,
            "cache_dir": False,
            "socket_timeout": 15,
            "format": fmt,
        }
        
        # Optional headers
        if referer_hdr:
            opts["http_headers"] = {"Referer": referer_hdr}
        
        # Optional browser cookies (requires browser-data package)
        if cookies_browser:
            opts["cookiefrombrowser"] = cookies_browser
        
        # HLS preference
        if prefer_hls:
            opts.setdefault("http_headers", {})["User-Agent"] = "Mozilla/5.0"
            opts["format"] = "bestvideo+bestaudio/best"
        
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(target, download=False)
            hdrs = info.get("http_headers") or {}
            
            self._send(200, {
                "url": info.get("url"), 
                "title": info.get("title"),
                "thumbnail": info.get("thumbnail"),
                "duration": info.get("duration"),
                "referer": hdrs.get("Referer") or info.get("webpage_url"),
                "formats_available": len(info.get("formats", [])),
            })
        except Exception as e:
            self._send(502, {"error": str(e).splitlines()[-1][:300]})
    
    def log_message(self, format, *args):
        pass  # Silence logs
