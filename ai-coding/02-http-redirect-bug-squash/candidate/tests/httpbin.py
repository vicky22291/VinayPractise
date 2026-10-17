"""A small httpbin-style server for the test suite.

It listens on 127.0.0.1 on a free port, in a background thread. Every request
it receives is appended to `FakeBin.log` as a dict with method, path, headers
and body, so tests can check what actually reached the server.

Endpoints:
    /get /post /put /patch /delete   echo the request (405 on the wrong method)
    /anything[/...]                  echo the request, any method
    /headers                         {"headers": {...}}
    /redirect-to?url=..&status_code=..   redirect to `url` (default 302)
    /redirect/<n>                    n relative redirects, then /get
    /status/<code>                   empty body with that status
    /cookies                         {"cookies": {...}} from the Cookie header
    /cookies/set?name=value          Set-Cookie for each pair, then 302 to /cookies
    /basic-auth/<user>/<password>    200 if the Basic credentials match, else 401
"""
import base64
import json
import threading
import unittest
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qsl, urlsplit

TIMEOUT = 1  # seconds, for every request the suite sends

_ECHO_METHODS = {"/get": "GET", "/post": "POST", "/put": "PUT", "/patch": "PATCH", "/delete": "DELETE"}


class _Handler(BaseHTTPRequestHandler):
    server_version = "fakebin/1.0"

    def log_message(self, *args):
        pass

    def do_GET(self):
        self._dispatch()

    do_POST = do_PUT = do_PATCH = do_DELETE = do_HEAD = do_OPTIONS = do_GET

    def _read_body(self):
        if self.headers.get("Transfer-Encoding", "").lower() == "chunked":
            chunks = []
            while True:
                line = self.rfile.readline()
                if not line:
                    break
                size = int(line.split(b";")[0].strip() or b"0", 16)
                if size == 0:
                    self.rfile.readline()
                    break
                chunks.append(self.rfile.read(size))
                self.rfile.readline()
            return b"".join(chunks)
        length = int(self.headers.get("Content-Length") or 0)
        return self.rfile.read(length) if length else b""

    def _dispatch(self):
        parts = urlsplit(self.path)
        path = parts.path
        args = dict(parse_qsl(parts.query, keep_blank_values=True))
        body = self._read_body()
        self.server.log.append(
            {"method": self.command, "path": path, "headers": dict(self.headers.items()), "body": body}
        )

        if path in _ECHO_METHODS:
            if self.command != _ECHO_METHODS[path]:
                return self._send(405)
            return self._echo(args, body)
        if path == "/anything" or path.startswith("/anything/"):
            return self._echo(args, body)
        if path == "/headers":
            return self._json({"headers": self._headers()})
        if path == "/redirect-to":
            status = int(args.get("status_code", 302))
            return self._send(status, headers={"Location": args.get("url", "/get")})
        if path.startswith("/redirect/"):
            n = int(path.rsplit("/", 1)[1])
            target = f"/redirect/{n - 1}" if n > 1 else "/get"
            return self._send(302, headers={"Location": target})
        if path.startswith("/status/"):
            return self._send(int(path.rsplit("/", 1)[1]))
        if path == "/cookies":
            return self._json({"cookies": self._cookies()})
        if path == "/cookies/set":
            cookies = [f"{k}={v}; Path=/" for k, v in args.items()]
            return self._send(302, headers={"Location": "/cookies"}, cookies=cookies)
        if path.startswith("/basic-auth/"):
            _, _, user, password = path.split("/", 3)
            expected = "Basic " + base64.b64encode(f"{user}:{password}".encode()).decode()
            if self.headers.get("Authorization") == expected:
                return self._json({"authenticated": True, "user": user})
            return self._send(401, headers={"WWW-Authenticate": 'Basic realm="fakebin"'})
        return self._send(404)

    def _headers(self):
        return {k.title(): v for k, v in self.headers.items()}

    def _cookies(self):
        jar = SimpleCookie()
        jar.load(self.headers.get("Cookie", ""))
        return {name: morsel.value for name, morsel in jar.items()}

    def _echo(self, args, body):
        ctype = self.headers.get("Content-Type", "")
        form, parsed_json = {}, None
        if ctype.startswith("application/x-www-form-urlencoded"):
            form = dict(parse_qsl(body.decode("utf-8")))
        elif ctype.startswith("application/json"):
            parsed_json = json.loads(body or b"null")
        host = self.headers.get("Host", "")
        self._json(
            {
                "method": self.command,
                "args": args,
                "data": "" if form else body.decode("utf-8", "replace"),
                "form": form,
                "json": parsed_json,
                "headers": self._headers(),
                "url": f"http://{host}{self.path}",
            }
        )

    def _json(self, payload, status=200):
        self._send(status, json.dumps(payload).encode(), {"Content-Type": "application/json"})

    def _send(self, status, body=b"", headers=None, cookies=()):
        try:
            self.send_response(status)
            for name, value in (headers or {}).items():
                self.send_header(name, value)
            for cookie in cookies:
                self.send_header("Set-Cookie", cookie)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            if self.command != "HEAD":
                self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            pass


class _Server(ThreadingHTTPServer):
    daemon_threads = True

    def handle_error(self, request, client_address):
        pass  # clients that time out and hang up are expected in this suite


class FakeBin:
    def __init__(self):
        self.httpd = _Server(("127.0.0.1", 0), _Handler)
        self.httpd.log = []
        self.port = self.httpd.server_address[1]
        self._thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)

    def start(self):
        self._thread.start()
        return self

    def stop(self):
        self.httpd.shutdown()
        self.httpd.server_close()

    @property
    def log(self):
        return self.httpd.log

    def url(self, *parts):
        return f"http://127.0.0.1:{self.port}/" + "/".join(str(p).strip("/") for p in parts)


class HttpbinTestCase(unittest.TestCase):
    """Starts one FakeBin per test class. `self.httpbin("post")` builds a URL."""

    @classmethod
    def setUpClass(cls):
        cls.bin = FakeBin().start()

    @classmethod
    def tearDownClass(cls):
        cls.bin.stop()

    def setUp(self):
        self.bin.log.clear()

    def httpbin(self, *parts):
        return self.bin.url(*parts)
