#!/usr/bin/env python3
"""Base44 sandbox dev server for Web Dashers — setup helper, not part of the app.

Static file server for the repository root (same behaviour as the plain
`python -m http.server` it replaces, threaded, reading files from the bind-mounted
clone per request). Two extras are added, and BOTH are inert unless
BASE44_PREVIEW_MODE is exactly "1":

  1. The app's account routes (/api/auth/*, /api/saves) are answered by a
     same-origin development stub. The real account server is a separate service
     whose source is not in this repository (see AGENTS.md), and the hosted
     backend at https://webdasher-backend.itzar.dev sends no CORS headers for a
     preview origin — the client's automatic session check therefore fails with a
     CORS/network error there. The stub answers "not signed in" ({"user": null}),
     which is the truth in an environment that has no account backend, and never
     authenticates anybody.
  2. `window.__previewLocalApi = true` is injected into index.html so that
     assets/scripts/utils/api-config.js uses that same-origin stub instead of the
     hosted backend, exactly as the app already does on localhost. Nothing else
     is rewritten.

With BASE44_PREVIEW_MODE unset (or any other value) this is a plain, unmodified
static file server and the app keeps talking to the hosted backend.
"""

import json
import os
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

PREVIEW_MODE = os.environ.get("BASE44_PREVIEW_MODE") == "1"
ROOT = os.environ.get("WEB_ROOT") or os.getcwd()
HOST = os.environ.get("WEB_HOST", "0.0.0.0")
PORT = int(os.environ.get("WEB_PORT", "3000"))

API_PREFIX = "/api/"
PREVIEW_FLAG = b'<script>window.__previewLocalApi = true;</script>'


def read_index_html():
    with open(os.path.join(ROOT, "index.html"), "rb") as handle:
        return handle.read()


class DevHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=ROOT, **kwargs)

    def _send_json(self, status, payload):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def _api_stub(self, route):
        """Development answers for the account API — no accounts live here."""
        if route == "/api/auth/me":
            self._send_json(200, {"user": None})
        elif route == "/api/auth/logout":
            self._send_json(200, {"ok": True})
        else:
            self._send_json(
                503,
                {"error": "The Web Dashers account server is not available in this preview environment."},
            )

    def _send_index(self):
        try:
            body = read_index_html()
        except OSError as exc:
            self.send_error(404, "index.html not readable: %s" % exc)
            return
        if PREVIEW_FLAG not in body:
            if b"<head>" in body:
                body = body.replace(b"<head>", b"<head>\n    " + PREVIEW_FLAG, 1)
            else:
                print(
                    "dev_server: WARNING could not inject the preview API flag into index.html",
                    file=sys.stderr,
                )
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if PREVIEW_MODE:
            route = self.path.split("?")[0]
            if route.startswith(API_PREFIX):
                return self._api_stub(route.rstrip("/"))
            if route in ("/", "/index.html"):
                return self._send_index()
        return super().do_GET()

    def do_HEAD(self):
        if PREVIEW_MODE and self.path.split("?")[0].startswith(API_PREFIX):
            return self._api_stub(self.path.split("?")[0].rstrip("/"))
        return super().do_HEAD()

    def do_POST(self):
        if PREVIEW_MODE:
            route = self.path.split("?")[0]
            if route.startswith(API_PREFIX):
                return self._api_stub(route.rstrip("/"))
        self.send_error(501, "Unsupported method ('POST')")


if __name__ == "__main__":
    if not os.path.isfile(os.path.join(ROOT, "index.html")):
        sys.exit("dev_server: no index.html found in %s" % ROOT)
    print(
        "dev_server: serving %s on http://%s:%d (BASE44_PREVIEW_MODE=%r)"
        % (ROOT, HOST, PORT, os.environ.get("BASE44_PREVIEW_MODE")),
        flush=True,
    )
    ThreadingHTTPServer((HOST, PORT), DevHandler).serve_forever()
