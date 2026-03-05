#!/usr/bin/env python3
"""HTTP server for test container: HTML page, JSON info, health check."""

import json
import os
import socket
import time
from http.server import BaseHTTPRequestHandler, HTTPServer

START_TIME = time.time()

HTML_PAGE = """<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Serverless Container</title>
    <style>
        * {{ box-sizing: border-box; }}
        body {{ font-family: system-ui, -apple-system, sans-serif; max-width: 600px; margin: 2rem auto; padding: 0 1rem; line-height: 1.6; color: #333; }}
        h1 {{ color: #389f74; font-size: 1.5rem; }}
        .status {{ display: inline-block; padding: 0.25rem 0.5rem; background: #e6f4ee; color: #389f74; border-radius: 4px; font-weight: 500; }}
        .block {{ margin: 1.5rem 0; padding: 1rem; background: #f5f5f5; border-radius: 8px; }}
        .block h2 {{ margin: 0 0 0.5rem; font-size: 1rem; color: #555; }}
        code {{ background: #eee; padding: 0.1rem 0.3rem; border-radius: 3px; font-size: 0.9em; }}
        ul {{ margin: 0.5rem 0; padding-left: 1.25rem; }}
        a {{ color: #0066cc; }}
    </style>
</head>
<body>
    <h1>Serverless Container</h1>
    <p>Статус: <span class="status">Running</span></p>

    <div class="block">
        <h2>Подключение по SSH</h2>
        <ul>
            <li>Порт: <code>2222</code></li>
            <li>Пользователь: <code>jovyan</code></li>
            <li>См. <a href="https://cloud.ru/docs/container-apps-evolution/ug/topics/guides__ssh-access">инструкцию по настройке SSH</a>.</li>
        </ul>
        <p>Выполните команду:</p>
        <p><code>ssh -i &lt;SSH key&gt; &lt;container&gt;.&lt;project ID&gt;@ssh.containers.cloud.ru -p 2222</code></p>
        <ul>
            <li>&lt;SSH key&gt; — сохранённый SSH-ключ.</li>
            <li>&lt;container&gt; — название контейнера.</li>
            <li>&lt;project ID&gt; — идентификатор проекта, в котором размещён контейнер. <a href="https://cloud.ru/docs/container-apps-evolution/ug/topics/api-ref__project-id">Как найти идентификатор проекта</a></li>
        </ul>
    </div>

    <div class="block">
        <h2>Информация</h2>
        <p>Контейнер: <code>{container_name}</code></p>
        <p>Uptime: <code>{uptime}</code> сек</p>
    </div>
</body>
</html>
"""


def get_uptime() -> int:
    return int(time.time() - START_TIME)


def get_container_display_name() -> str:
    """Имя контейнера без суффикса ревизии (container-app-xxx вместо полного hostname)."""
    name = os.environ.get("CONTAINER_NAME", "")
    if name:
        return name
    hostname = socket.gethostname()
    # Убираем суффикс ревизии Knative (например -00001-abc12)
    parts = hostname.rsplit("-", 2)
    if len(parts) >= 3 and parts[-1].isalnum() and parts[-2].isdigit():
        return "-".join(parts[:-2])
    return hostname


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # Suppress default logging

    def send_json(self, data: dict, status: int = 200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_html(self, html: str, status: int = 200):
        body = html.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_text(self, text: str, status: int = 200):
        body = text.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = self.path.split("?")[0].rstrip("/") or "/"

        if path == "/health":
            self.send_text("ok", 200)
            return

        if path == "/info":
            self.send_json(
                {
                    "status": "ok",
                    "service": "Serverless Container (Test)",
                    "description": "Serverless Container",
                    "container_name": get_container_display_name(),
                    "uptime_seconds": get_uptime(),
                    "ssh": {
                        "port": 2222,
                        "user": "jovyan",
                        "portal_host": "ssh.containers.cloud.ru",
                        "hint": "Включите SSH в настройках контейнера, сгенерируйте ключ и сохраните приватный ключ.",
                    },
                },
                200,
            )
            return

        # Default: HTML page
        html = HTML_PAGE.format(
            container_name=get_container_display_name(),
            uptime=get_uptime(),
        )
        self.send_html(html, 200)


def main():
    port = int(os.environ.get("PORT", "8080"))
    server = HTTPServer(("0.0.0.0", port), Handler)
    server.serve_forever()


if __name__ == "__main__":
    main()
