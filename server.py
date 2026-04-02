#!/usr/bin/env python3
"""
Panasonixis Static Site + Waitlist API Server
- Serves static files on port 5124
- POST /api/waitlist → saves email to waitlist.json (with rate limiting + honeypot)
- GET /api/waitlist → returns count only (no email exposure)
"""
import json, os, time
from http.server import HTTPServer, SimpleHTTPRequestHandler
from datetime import datetime, timezone
from urllib.parse import urlparse

PORT = 5124
SITE_DIR = os.path.dirname(os.path.abspath(__file__))
WAITLIST_FILE = os.path.join(SITE_DIR, "waitlist.json")

# ─── Security: Rate Limiting (in-memory, per IP) ───
# Sliding window: max SUBMISSIONS_PER_WINDOW from each IP
SUBMISSIONS_PER_WINDOW = 3
WINDOW_SECONDS = 3600  # 1 hour

_rate_limit_store = {}  # ip → [(timestamp, count), ...]

def _is_rate_limited(ip: str) -> bool:
    now = time.time()
    # Clean old entries
    _rate_limit_store[ip] = [
        ts for ts in _rate_limit_store.get(ip, [])
        if now - ts < WINDOW_SECONDS
    ]
    if len(_rate_limit_store[ip]) >= SUBMISSIONS_PER_WINDOW:
        return True
    _rate_limit_store[ip].append(now)
    return False

def _get_client_ip() -> str:
    # Check X-Forwarded-For first (for reverse proxy setups)
    forwarded = os.environ.get("X_FORWARDED_FOR", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return "127.0.0.1"

# ─── Email Validation ───
import re
_email_re = re.compile(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$")

def _is_valid_email(email: str) -> bool:
    if not email or "@" not in email:
        return False
    if len(email) > 254:
        return False
    local, domain = email.rsplit("@", 1)
    if len(local) > 64:
        return False
    return bool(_email_re.match(email))

class PanasonixisHandler(SimpleHTTPRequestHandler):

    def _send_json(self, status: int, data: dict):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def do_GET(self):
        if self.path == "/api/waitlist":
            # Only returns COUNT — no email data exposed
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("X-Content-Type-Options", "nosniff")
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
        return SimpleHTTPRequestHandler.do_GET(self)

    def do_POST(self):
        if self.path == "/api/waitlist":
            client_ip = _get_client_ip()

            # ─── Rate Limiting ───
            if _is_rate_limited(client_ip):
                self._send_json(429, {
                    "error": "Too many requests. Please try again later.",
                    "retry_after": WINDOW_SECONDS
                })
                return

            length = int(self.headers.get("Content-Length", 0))
            if length > 2048:  # Prevent body bloat
                self._send_json(400, {"error": "Request too large."})
                return

            body = self.rfile.read(length)
            try:
                payload = json.loads(body)
            except json.JSONDecodeError:
                self._send_json(400, {"error": "Invalid request body."})
                return

            # ─── Honeypot CAPTCHA ───
            # Hidden field 'website' should be empty — bots fill it, humans don't
            honeypot = payload.get("website", "")
            if honeypot:
                # Silently accept but don't save — it's a bot
                self._send_json(200, {
                    "message": "You're on the list. We'll be in touch. ♡",
                    "count": 0,
                    "airtable": False
                })
                return

            email = payload.get("email", "").strip()
            source = payload.get("source", "website")

            # ─── Email Validation ───
            if not _is_valid_email(email):
                self._send_json(400, {"error": "Please enter a valid email address."})
                return

            # ─── Airtable (optional) ───
            added_to_airtable = False
            try:
                import urllib.request
                AIRTABLE_PAT = os.environ.get("AIRTABLE_PAT", "")
                AIRTABLE_BASE = os.environ.get("AIRTABLE_BASE_ID", "")
                if AIRTABLE_PAT and AIRTABLE_BASE:
                    url = f"https://api.airtable.com/v0/{AIRTABLE_BASE}/Waitlist"
                    at_payload = json.dumps({
                        "records": [{
                            "fields": {
                                "Email": email,
                                "Timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                                "Source": source,
                                "Status": "new",
                            }
                        }]
                    }).encode()
                    req = urllib.request.Request(
                        url, data=at_payload,
                        headers={"Authorization": f"Bearer {AIRTABLE_PAT}", "Content-Type": "application/json"},
                        method="POST"
                    )
                    with urllib.request.urlopen(req, timeout=15) as resp:
                        if resp.status == 200:
                            added_to_airtable = True
            except Exception:
                pass  # Airtable not configured — fall back to JSON only

            # ─── Save to JSON (local backup) ───
            try:
                with open(WAITLIST_FILE, "r") as f:
                    entries = json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                entries = []

            already = any(e.get("email", "").lower() == email.lower() for e in entries)
            if not already:
                entries.append({
                    "email": email,
                    "joined": datetime.now(timezone.utc).isoformat(),
                    "source": source,
                    "airtable": added_to_airtable,
                    "ip_hash": hash(client_ip)  # hashed so we can't read IP back
                })
                with open(WAITLIST_FILE, "w") as f:
                    json.dump(entries, f, indent=2)

            self._send_json(200, {
                "message": "You're on the list. We'll be in touch. ♡",
                "count": len(entries),
                "airtable": added_to_airtable
            })
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
    print(f"  Security: rate limit 3/hr, honeypot, email validation, IP hashing")
    server.serve_forever()
