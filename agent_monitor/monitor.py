#!/usr/bin/env python3
"""Optimus Agent Monitor: local-only, read-only event monitor (stdlib)."""
import argparse
import json
import os
import sqlite3
import sys
import time
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

HOME = Path(os.environ.get("OPTIMUS_MONITOR_HOME", str(Path.home() / ".local/share/optimus-monitor")))
DB = HOME / "events.sqlite3"
ALLOWED = {"SessionStart", "SessionEnd", "SubagentStart", "SubagentStop", "PreToolUse", "PostToolUse", "PostToolUseFailure"}
SCHEMA = """CREATE TABLE IF NOT EXISTS events(
id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT NOT NULL, event TEXT NOT NULL,
session_id TEXT NOT NULL, agent_id TEXT NOT NULL, tool TEXT NOT NULL
)"""

def connect():
    HOME.mkdir(mode=0o700, parents=True, exist_ok=True)
    os.chmod(HOME, 0o700)
    con = sqlite3.connect(DB, timeout=5)
    con.execute(SCHEMA)
    con.commit()
    try: os.chmod(DB, 0o600)
    except OSError: pass
    return con

def clean(value, limit=96):
    return str(value or "")[:limit].replace("\n", " ").replace("\r", " ")

def ingest(raw):
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError("Expected JSON object")
    event = data.get("hook_event_name", "")
    if event not in ALLOWED:
        return False
    session = clean(data.get("session_id"))
    agent = clean(data.get("agent_id") or data.get("agent_type") or "main")
    tool = clean(data.get("tool_name"))
    with connect() as con:
        con.execute("INSERT INTO events(ts,event,session_id,agent_id,tool) VALUES (?,?,?,?,?)",
                    (datetime.now(timezone.utc).isoformat(), event, session, agent, tool))
    return True

def latest(limit=100):
    with connect() as con:
        rows = con.execute("SELECT ts,event,session_id,agent_id,tool FROM events ORDER BY id DESC LIMIT ?",
                           (max(1, min(int(limit), 500)),)).fetchall()
    return [dict(zip(("ts", "event", "session_id", "agent_id", "tool"), row)) for row in rows]

HTML = """<!doctype html><html lang="es"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Optimus Agent Monitor (staging)</title><style>
body{background:#0b1220;color:#e5e7eb;font:16px system-ui;margin:20px}
header{padding:16px;border:1px solid #334155;border-radius:12px}
article{border-bottom:1px solid #334155;padding:10px}small{color:#94a3b8}
</style><header><h1>Optimus Agent Monitor</h1><p>Vista móvil preparada · Solo localhost · No producción</p></header>
<main id="events" aria-live="polite"></main><script>
async function refresh(){try{let r=await fetch('/api/events',{cache:'no-store'});
if(!r.ok)throw Error('API');let rows=await r.json();let root=document.getElementById('events');
root.replaceChildren();for(let x of rows){let a=document.createElement('article');
let title=document.createElement('strong');title.textContent=x.event+' · '+x.agent_id;
let sub=document.createElement('small');sub.textContent=' · '+x.ts+' · '+x.tool;
a.append(title,sub);root.append(a)}}catch(e){document.getElementById('events').textContent='Sin conexión local';}}
refresh();setInterval(refresh,3000);
</script></html>"""

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/":
            body, typ = HTML.encode(), "text/html; charset=utf-8"
        elif path == "/api/events":
            body, typ = json.dumps(latest()).encode(), "application/json"
        else:
            self.send_error(404); return
        self.send_response(200)
        self.send_header("Content-Type", typ)
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", "default-src 'self' 'unsafe-inline'; connect-src 'self'")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
    def log_message(self, *args): pass

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["ingest", "watch", "web", "json"])
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    if args.command == "ingest":
        try: ingest(sys.stdin.read(1024 * 1024))
        except (ValueError, json.JSONDecodeError, sqlite3.Error) as exc:
            print("Monitor ingestion error: " + type(exc).__name__, file=sys.stderr)
        return  # Never block Claude Code due to monitoring failures.
    if args.command == "json":
        print(json.dumps(latest(), indent=2)); return
    if args.command == "watch":
        try:
            while True:
                os.system("clear")
                print("OPTIMUS AGENT MONITOR | Ctrl+C para salir\n")
                for item in latest(25):
                    print(f"{item['ts'][11:19]}  {item['event']:<19} {item['agent_id']:<20} {item['tool']}")
                time.sleep(2)
        except KeyboardInterrupt: return
    if args.command == "web":
        if not 1024 <= args.port <= 65535:
            parser.error("port must be between 1024 and 65535")
        print(f"STAGING LOCAL ONLY: http://127.0.0.1:{args.port}")
        ThreadingHTTPServer(("127.0.0.1", args.port), Handler).serve_forever()

if __name__ == "__main__":
    main()
