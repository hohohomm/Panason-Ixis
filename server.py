#!/usr/bin/env python3
"""
Panasonixis Static Site + Waitlist API Server
- Serves static files on port 5124
- POST /api/waitlist → saves email to waitlist.json
- GET /api/waitlist → returns count of waitlist signups
"""
import json, os
from http.server import HTTPServer, SimpleHTTPRequestHandler
from datetime import datetime, timezone

PORT = 5124
SITE_DIR = os.path.dirname(os.path.abspath(__file__))
WAITLIST_FILE = os.path.join(SITE_DIR, "waitlist.json")

class PanasonixisHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/api/waitlist":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            try:
                with open(WAITLIST_FILE, "r") as f:
                    data = json.load(f)
            except:
                data = []
            count = len(data)
            self.wfile.write(json.dumps({
                "count": count,
                "message": f"{count} {'people are' if count != 1 else 'person is'} on the waitlist."
            }).encode())
            return

        # Serve static files
        return SimpleHTTPRequestHandler.do_GET(self)

    def do_POST(self):
        if self.path == "/api/waitlist":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length)
            try:
                payload = json.loads(body)
                email = payload.get("email", "").strip()
            except:
                email = ""

            if not email or "@" not in email:
                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Invalid email"}).encode())
                return

            # Load existing waitlist
            try:
                with open(WAITLIST_FILE, "r") as f:
                    entries = json.load(f)
            except:
                entries = []

            # Add new entry (deduplicate by email)
            already = any(e.get("email") == email for e in entries)
            if not already:
                entries.append({
                    "email": email,
                    "joined": datetime.now(timezone.utc).isoformat()
                })
                with open(WAITLIST_FILE, "w") as f:
                    json.dump(entries, f, indent=2)

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            msg = "You're on the list. We'll be in touch. ♡" if not already else "You're already on the list."
            self.wfile.write(json.dumps({"message": msg, "count": len(entries)}).encode())
            return

        self.send_response(404)
        self.end_headers()

    def log_message(self, format, *args):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {args[0]}")

if __name__ == "__main__":
    os.chdir(SITE_DIR)
    server = HTTPServer(("127.0.0.1", PORT), PanasonixisHandler)
    print(f"  Panasonixis Site")
    print(f"  ──────────────────────────────")
    print(f"  Site:     http://localhost:{PORT}")
    print(f"  API:      http://localhost:{PORT}/api/waitlist")
    print(f"  Waitlist: {WAITLIST_FILE}")
    print(f"  Serving files from: {SITE_DIR}")
    server.serve_forever()
