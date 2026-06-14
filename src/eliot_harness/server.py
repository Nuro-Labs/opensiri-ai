"""Lightweight, secure zero-dependency HTTP execution gateway for OpenSiri-AI.

Allows cloud-based brains (like pi.dev) to safely automate local macOS capabilities
by routing requests through your exact user-configured permission profiles.
"""

from __future__ import annotations

import json
import os
import sys
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any

from .config import load_config
from .connectors.applescript import run_osa
from .connectors.memory import MemoryConnector
from .connectors.registry import build_registry
from .connectors.web import WebConnector
from .executor import Executor
from .hypersave import HypersaveClient
from .local_index import LocalIndex
from .permissions import PermissionState, Source
from .schema import Action


class OpenSiriGatewayHandler(BaseHTTPRequestHandler):
    executor: Executor
    perms: PermissionState

    def do_GET(self) -> None:
        if self.path in ("/", "/status", "/index.html"):
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(self._render_dashboard().encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Not Found")

    def do_POST(self) -> None:
        if self.path == "/execute":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else ""
            
            try:
                data = json.loads(body) if body else {}
            except json.JSONDecodeError:
                self._send_json({"status": "error", "message": "Invalid JSON"}, 400)
                return

            action_name = data.get("action")
            args = data.get("args") or {}

            if not action_name:
                self._send_json({"status": "error", "message": "Missing 'action' parameter"}, 400)
                return

            # Secure, explicit execution routing
            try:
                if action_name == "applescript":
                    script = str(args.get("script", ""))
                    if not script:
                        self._send_json({"status": "error", "message": "Missing 'script' argument for applescript execution"}, 400)
                        return
                    res_text = run_osa(script)
                    self._send_json({
                        "status": "success",
                        "result": res_text,
                        "terminal": True
                    })
                else:
                    # Leverage full canonical executor covering all 487 native Mac tools
                    action = Action(action_name, args)
                    res = self.executor.execute(action)
                    self._send_json({
                        "status": "success",
                        "result": res.output,
                        "terminal": res.terminal
                    })
            except Exception as e:
                self._send_json({"status": "error", "message": str(e)}, 500)
        else:
            self.send_response(404)
            self.end_headers()

    def do_OPTIONS(self) -> None:
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def _send_json(self, data: dict[str, Any], status: int = 200) -> None:
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode("utf-8"))

    def _render_dashboard(self) -> str:
        # Build premium glassmorphic visual status panel of local gateway permissions
        read_list = sorted([r.value for r in self.perms.read_sources])
        write_list = sorted([w.value for r in [self.perms.write_sources] for w in r])

        read_badges = "".join(f'<span class="badge badge-read">{r}</span>' for r in read_list)
        write_badges = "".join(f'<span class="badge badge-write">{w}</span>' for w in write_list)

        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>OpenSiri local gateway bridge</title>
    <style>
        body {{
            background: linear-gradient(135deg, #0d0f1a 0%, #17182c 100%);
            color: #e2e8f0;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            margin: 0;
            padding: 40px 20px;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 80vh;
        }}
        .card {{
            background: rgba(255, 255, 255, 0.03);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 24px;
            padding: 40px;
            max-width: 600px;
            width: 100%;
            box-shadow: 0 20px 40px rgba(0,0,0,0.4);
            text-align: center;
        }}
        .logo {{
            width: 64px;
            height: 64px;
            border-radius: 16px;
            background: linear-gradient(135deg, #00f2fe 0%, #4facfe 100%);
            margin: 0 auto 20px auto;
            box-shadow: 0 0 20px rgba(0, 242, 254, 0.4);
            display: flex;
            justify-content: center;
            align-items: center;
            font-size: 28px;
        }}
        h1 {{
            font-size: 24px;
            font-weight: 700;
            margin: 0 0 8px 0;
            background: linear-gradient(90deg, #ffffff 0%, #cbd5e1 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        .status {{
            font-size: 14px;
            color: #10b981;
            font-weight: 600;
            display: inline-flex;
            align-items: center;
            gap: 6px;
            background: rgba(16, 185, 129, 0.1);
            padding: 6px 16px;
            border-radius: 100px;
            margin-bottom: 30px;
        }}
        .status-dot {{
            width: 8px;
            height: 8px;
            background: #10b981;
            border-radius: 50%;
            box-shadow: 0 0 10px #10b981;
        }}
        p {{
            font-size: 14px;
            color: #94a3b8;
            line-height: 1.6;
            margin: 0 0 30px 0;
        }}
        .section {{
            text-align: left;
            margin-bottom: 24px;
        }}
        .section-title {{
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            color: #64748b;
            font-weight: 700;
            margin-bottom: 12px;
        }}
        .badge-container {{
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
        }}
        .badge {{
            font-size: 12px;
            padding: 6px 12px;
            border-radius: 8px;
            font-weight: 500;
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.08);
        }}
        .badge-read {{
            color: #60a5fa;
            border-color: rgba(96, 165, 250, 0.2);
            background: rgba(96, 165, 250, 0.05);
        }}
        .badge-write {{
            color: #fb923c;
            border-color: rgba(251, 146, 60, 0.2);
            background: rgba(251, 146, 60, 0.05);
        }}
        .footer {{
            margin-top: 40px;
            border-top: 1px solid rgba(255,255,255,0.06);
            padding-top: 20px;
            font-size: 12px;
            color: #475569;
        }}
    </style>
</head>
<body>
    <div class="card">
        <div class="logo">🎙️</div>
        <h1>OpenSiri Local Gateway Bridge</h1>
        <div class="status">
            <span class="status-dot"></span> Active & Secure
        </div>
        <p>Your local Mac system is securely bridged to your cloud developer agent (pi.dev). The agent can only execute local macOS actions that match your configured permission scopes below.</p>
        
        <div class="section">
            <div class="section-title">Enabled Read Sources</div>
            <div class="badge-container">
                {read_badges or '<span class="badge">None</span>'}
            </div>
        </div>

        <div class="section" style="margin-bottom: 0;">
            <div class="section-title">Enabled Write Permissions</div>
            <div class="badge-container">
                {write_badges or '<span class="badge">None</span>'}
            </div>
        </div>

        <div class="footer">
            Bound to localhost:8082 &bull; OpenSiri-AI 0.1.0
        </div>
    </div>
</body>
</html>
"""
        return html


def start_server(port: int = 8082) -> None:
    # 1. Load exact local configurations
    cfg = load_config()
    
    # 2. Extract allowed sources
    read_sources = set()
    write_sources = set()
    
    if cfg.sources["notes"].write:
        write_sources.add(Source.NOTES)
    if cfg.sources["reminders"].write:
        write_sources.add(Source.REMINDERS)
    if cfg.sources["finder"].write:
        write_sources.add(Source.FINDER)
        
    for source in ("mail", "messages", "browser", "system"):
        if cfg.sources[source].write:
            write_sources.add(Source(source))
            
    if cfg.sources["files"].read:
        read_sources.add(Source.FILES)
    if cfg.sources["finder"].read:
        read_sources.add(Source.FINDER)
    if cfg.sources["hypersave"].read:
        read_sources.add(Source.HYPERSAVE)
    if cfg.network_enabled:
        read_sources.add(Source.WEB)
        
    for source in ("mail", "messages", "reminders", "calendar", "contacts", "browser", "system", "photos", "visual", "maps", "music", "podcasts"):
        if cfg.sources[source].read:
            read_sources.add(Source(source))

    perms = PermissionState(
        read_sources=read_sources, 
        write_sources=write_sources, 
        network_enabled=cfg.network_enabled
    )
    
    # 3. Construct core engine components
    memory_client = HypersaveClient.from_env() if cfg.sources["hypersave"].read else None
    local_index = None # Will instantiate index dynamically if enabled
    registry = build_registry(cfg, memory_client, None)
    memory = MemoryConnector(memory_client)
    
    # 4. Instantiate final static Executor
    executor = Executor(
        memory=memory,
        web=WebConnector(enabled=cfg.network_enabled),
        permissions=perms,
        local_index=local_index,
        file_roots=None
    )
    
    # Inject references into handler class
    OpenSiriGatewayHandler.executor = executor
    OpenSiriGatewayHandler.perms = perms

    # 5. Serve locally
    server = HTTPServer(("127.0.0.1", port), OpenSiriGatewayHandler)
    print(f"===========================================================")
    print(f"🚀 OpenSiri Local Gateway Bridge running on http://127.0.0.1:{port}")
    print(f"===========================================================")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping Local Gateway Bridge...")
        server.server_close()


def main() -> None:
    port = 8082
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            pass
    start_server(port)


if __name__ == "__main__":
    main()
