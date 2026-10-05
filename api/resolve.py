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
        fmt = query.get("f", [""])[0]
        
        if not target.startswith(("http://", "https://")):
            return self._send(400, {"error": "use ?url=http(s)://..."})
        
        # DEFAULT: Try merged format first (returns actual URL)
        if not fmt or fmt == 'best':
            fmt = 'best'  # Single merged format
        
        opts = {
            "quiet": True,
            "no_warnings": True,
            "noplaylist": True,
            "skip_download": True,
            "cache_dir": False,
            "socket_timeout": 15,
            "format": fmt,
            "prefer_free_formats": False,
            # Add this to handle age-restricted/private videos better
            "extract_flat": False,
        }
        
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(target, download=False)
            
            # Get the actual URL from the response
            url = info.get("url") or info.get("http_url")
            
            if not url:
                # Try to find a playable URL in formats list
                formats = info.get("formats", [])
                for f in formats:
                    if f.get("url"):
                        url = f["url"]
                        break
            
            if not url:
                raise Exception("No playable URL found")
                
            hdrs = info.get("http_headers") or {}
            
            self._send(200, {
                "url": url, 
                "title": info.get("title"),
                "thumbnail": info.get("thumbnail"),
                "duration": info.get("duration"),
                "referer": hdrs.get("Referer") or info.get("webpage_url"),
            })
        except Exception as e:
            error_msg = str(e).splitlines()[-1][:300]
            self._send(502, {"error": error_msg})
    
    def log_message(self, format, *args):
        pass
