#!/usr/bin/env python3
"""Local fake of the MapDraw render API (see docs/MAPDRAW_API.md).

    python3 tools/mapdraw_server.py                    # http://127.0.0.1:8080
    python3 tools/mapdraw_server.py --port 9000 -v     # log every request
    python3 tools/mapdraw_server.py --fault-rate 0.4   # random 429 / 503 / dropped responses

It validates requests the way the real API does, draws a real PNG, bills one
credit per new render, and honours Idempotency-Key. Treat it as the vendor:
read it if you like, but do not change it.
"""
import argparse
import collections
import hashlib
import itertools
import json
import math
import random
import re
import struct
import threading
import time
import zlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

API_KEYS = ("md_test_ridemap",)
MAX_BODY = 256 * 1024
LIMITS = {"markers": 10, "paths": 100, "points_per_path": 500, "points_total": 5000, "label": 16}
SIZE_RANGE = (64, 1280)
ZOOM_RANGE = (1, 18)
COLORS = {
    "black": (20, 20, 20), "white": (255, 255, 255), "red": (220, 38, 38),
    "orange": (234, 88, 12), "yellow": (202, 138, 4), "green": (22, 163, 74),
    "blue": (37, 99, 235), "purple": (124, 58, 237), "brown": (146, 64, 14),
    "gray": (107, 114, 128),
}
HEX = re.compile(r"^#[0-9a-fA-F]{6}$")


class Invalid(Exception):
    def __init__(self, message, param=None):
        super().__init__(message)
        self.param = param


# ---------------------------------------------------------------- validation

def _number(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)


def _int(v):
    return isinstance(v, int) and not isinstance(v, bool)


def _only(obj, allowed, where):
    for k in obj:
        if k not in allowed:
            raise Invalid(f"Unknown parameter: {where}{k}", f"{where}{k}")


def _latlon(obj, where):
    if not isinstance(obj, dict):
        raise Invalid(f"{where} must be an object with lat and lon", where)
    for k in ("lat", "lon"):
        if k not in obj:
            raise Invalid(f"Missing required param: {where}.{k}", f"{where}.{k}")
        if not _number(obj[k]):
            raise Invalid(f"{where}.{k} must be a number", f"{where}.{k}")
    if not -90 <= obj["lat"] <= 90:
        raise Invalid(f"{where}.lat must be between -90 and 90", f"{where}.lat")
    if not -180 <= obj["lon"] <= 180:
        raise Invalid(f"{where}.lon must be between -180 and 180", f"{where}.lon")


def _color(v, where):
    if not isinstance(v, str) or not (v in COLORS or HEX.match(v)):
        raise Invalid(f"{where} must be a named color or #rrggbb", where)


def validate(body):
    if not isinstance(body, dict):
        raise Invalid("Request body must be a JSON object")
    _only(body, ("size", "center", "zoom", "markers", "paths", "format"), "")
    for k in ("size", "center", "zoom"):
        if k not in body:
            raise Invalid(f"Missing required param: {k}", k)
    size = body["size"]
    if not isinstance(size, dict):
        raise Invalid("size must be an object with width and height", "size")
    _only(size, ("width", "height"), "size.")
    for k in ("width", "height"):
        v = size.get(k)
        if not _int(v) or not SIZE_RANGE[0] <= v <= SIZE_RANGE[1]:
            raise Invalid(f"size.{k} must be an integer from {SIZE_RANGE[0]} to {SIZE_RANGE[1]}", f"size.{k}")
    _latlon(body["center"], "center")
    _only(body["center"], ("lat", "lon"), "center.")
    if not _int(body["zoom"]) or not ZOOM_RANGE[0] <= body["zoom"] <= ZOOM_RANGE[1]:
        raise Invalid(f"zoom must be an integer from {ZOOM_RANGE[0]} to {ZOOM_RANGE[1]}", "zoom")
    if body.get("format", "png") != "png":
        raise Invalid("format must be png", "format")

    markers = body.get("markers", [])
    if not isinstance(markers, list):
        raise Invalid("markers must be an array", "markers")
    if len(markers) > LIMITS["markers"]:
        raise Invalid(f"markers: at most {LIMITS['markers']} per request", "markers")
    for i, m in enumerate(markers):
        where = f"markers[{i}]"
        _latlon(m, where)
        _only(m, ("lat", "lon", "label", "color"), where + ".")
        if "label" in m:
            if not isinstance(m["label"], str) or not m["label"]:
                raise Invalid(f"{where}.label must be a non-empty string", f"{where}.label")
            if len(m["label"]) > LIMITS["label"]:
                raise Invalid(f"{where}.label must be at most {LIMITS['label']} characters", f"{where}.label")
        if "color" in m:
            _color(m["color"], f"{where}.color")

    paths = body.get("paths", [])
    if not isinstance(paths, list):
        raise Invalid("paths must be an array", "paths")
    if len(paths) > LIMITS["paths"]:
        raise Invalid(f"paths: at most {LIMITS['paths']} per request", "paths")
    total = 0
    for i, p in enumerate(paths):
        where = f"paths[{i}]"
        if not isinstance(p, dict):
            raise Invalid(f"{where} must be an object", where)
        _only(p, ("points", "color", "width"), where + ".")
        pts = p.get("points")
        if not isinstance(pts, list) or not 2 <= len(pts) <= LIMITS["points_per_path"]:
            raise Invalid(f"{where}.points must be an array of 2 to {LIMITS['points_per_path']} points", f"{where}.points")
        for j, pt in enumerate(pts):
            _latlon(pt, f"{where}.points[{j}]")
            _only(pt, ("lat", "lon"), f"{where}.points[{j}].")
        total += len(pts)
        if "color" in p:
            _color(p["color"], f"{where}.color")
        if "width" in p and (not _int(p["width"]) or not 1 <= p["width"] <= 8):
            raise Invalid(f"{where}.width must be an integer from 1 to 8", f"{where}.width")
    if total > LIMITS["points_total"]:
        raise Invalid(f"paths: at most {LIMITS['points_total']} points per request", "paths")


# ---------------------------------------------------------------- drawing

def _rgb(color, default):
    if color is None:
        return default
    if color in COLORS:
        return COLORS[color]
    return tuple(int(color[i:i + 2], 16) for i in (1, 3, 5))


def _world(lat, lon, zoom):
    scale = 256 * 2 ** zoom
    s = math.sin(math.radians(max(min(lat, 85.0511), -85.0511)))
    x = (lon + 180) / 360 * scale
    y = (0.5 - math.log((1 + s) / (1 - s)) / (4 * math.pi)) * scale
    return x, y


def draw_png(body):
    w, h, zoom = body["size"]["width"], body["size"]["height"], body["zoom"]
    cx, cy = _world(body["center"]["lat"], body["center"]["lon"], zoom)
    px = bytearray(b"\xf4\xf1\xea" * (w * h))  # paper background

    def to_px(pt):
        x, y = _world(pt["lat"], pt["lon"], zoom)
        return int(round(x - cx + w / 2)), int(round(y - cy + h / 2))

    def dot(x, y, r, rgb):
        for yy in range(y - r, y + r + 1):
            if 0 <= yy < h:
                for xx in range(x - r, x + r + 1):
                    if 0 <= xx < w:
                        i = (yy * w + xx) * 3
                        px[i:i + 3] = bytes(rgb)

    for gx in range(0, w, 64):  # faint grid so an empty map is still visibly a map
        for y in range(h):
            i = (y * w + gx) * 3
            px[i:i + 3] = b"\xe2\xdd\xd2"
    for p in body.get("paths", []):
        rgb, r = _rgb(p.get("color"), COLORS["blue"]), max(0, p.get("width", 3) // 2)
        pts = [to_px(q) for q in p["points"]]
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            steps = max(abs(x1 - x0), abs(y1 - y0), 1)
            for k in range(steps + 1):
                dot(x0 + (x1 - x0) * k // steps, y0 + (y1 - y0) * k // steps, r, rgb)
    for m in body.get("markers", []):
        x, y = to_px(m)
        dot(x, y, 5, COLORS["black"])
        dot(x, y, 3, _rgb(m.get("color"), COLORS["red"]))

    raw = b"".join(b"\x00" + bytes(px[y * w * 3:(y + 1) * w * 3]) for y in range(h))

    def chunk(tag, data):
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw, 6)) + chunk(b"IEND", b""))


# ---------------------------------------------------------------- state

Render = collections.namedtuple("Render", "id created idempotency_key body_hash png")


class State:
    """Everything the server remembers. Tests read it to assert on traffic and billing."""

    def __init__(self, api_keys=API_KEYS, fault_rate=0.0, seed=0):
        self.lock = threading.Lock()
        self.api_keys = set(api_keys)
        self.requests = []          # dicts: method, path, headers (lower-case keys), body, json
        self.renders = {}           # id -> Render
        self.by_key = {}            # (api_key, idempotency_key) -> render id
        self.billed = 0
        self.faults = collections.deque()
        self.fault_rate = fault_rate
        self.rng = random.Random(seed)
        self.ids = itertools.count(1)

    def inject(self, *faults):
        """Queue faults for the next POST /v1/render calls, in order.

        A fault is {"status": 429, "retry_after": 2}, {"status": 503},
        {"drop": "after_accept"} (render and bill, then close the connection
        with no response) or {"drop": "before_accept"}.
        """
        with self.lock:
            self.faults.extend(faults)

    def next_fault(self):
        with self.lock:
            if self.faults:
                return self.faults.popleft()
            if self.fault_rate and self.rng.random() < self.fault_rate:
                return self.rng.choice([{"status": 429, "retry_after": 1}, {"status": 503}, {"drop": "after_accept"}])
        return None

    def render_posts(self):
        return [r for r in self.requests if r["method"] == "POST" and r["path"] == "/v1/render"]


# ---------------------------------------------------------------- HTTP

class Handler(BaseHTTPRequestHandler):
    server_version = "MapDraw/1.4"
    state = None      # set by make_server
    verbose = False

    def log_message(self, fmt, *args):
        if self.verbose:
            super().log_message(fmt, *args)

    # -- helpers
    def _send(self, status, body, ctype, extra=None):
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Request-Id", f"req_{next(self.state.ids):06d}")
        for k, v in (extra or {}).items():
            self.send_header(k, str(v))
        self.end_headers()
        self.wfile.write(body)

    def _json(self, status, obj, extra=None):
        self._send(status, json.dumps(obj).encode(), "application/json", extra)

    def _error(self, status, etype, message, param=None, extra=None):
        err = {"type": etype, "message": message}
        if param:
            err["param"] = param
        self._json(status, {"error": err}, extra)

    def _record(self, body=b""):
        try:
            parsed = json.loads(body) if body else None
        except ValueError:
            parsed = None
        entry = {"method": self.command, "path": self.path,
                 "headers": {k.lower(): v for k, v in self.headers.items()}, "body": body, "json": parsed}
        with self.state.lock:
            self.state.requests.append(entry)

    def _auth(self):
        """Return the API key, or send 401 and return None."""
        header = self.headers.get("Authorization", "")
        if not header:
            self._error(401, "authentication_error",
                        "No API key provided. See https://docs.mapdraw.example/auth")
            return None
        scheme, _, key = header.partition(" ")
        if scheme != "Bearer" or key.strip() not in self.state.api_keys:
            self._error(401, "authentication_error", "Invalid API key provided.")
            return None
        return key.strip()

    def _render_meta(self, r):
        return {"id": r.id, "object": "render", "created": r.created, "idempotency_key": r.idempotency_key,
                "bytes": len(r.png), "image_url": f"/v1/renders/{r.id}/image"}

    # -- routes
    def do_GET(self):
        self._record()
        key = self._auth()
        if key is None:
            return
        path, _, query = self.path.partition("?")
        m = re.fullmatch(r"/v1/renders/(rnd_\w+)(/image)?", path)
        if m:
            r = self.state.renders.get(m.group(1))
            if r is None:
                return self._error(404, "invalid_request_error", f"No such render: {m.group(1)}")
            if m.group(2):
                return self._send(200, r.png, "image/png", {"X-Render-Id": r.id})
            return self._json(200, self._render_meta(r))
        if path == "/v1/renders":
            params = dict(p.split("=", 1) for p in query.split("&") if "=" in p)
            ikey = params.get("idempotency_key")
            if not ikey:
                return self._error(400, "invalid_request_error", "Missing required param: idempotency_key",
                                   "idempotency_key")
            rid = self.state.by_key.get((key, ikey))
            data = [self._render_meta(self.state.renders[rid])] if rid else []
            return self._json(200, {"object": "list", "data": data})
        self._error(404, "invalid_request_error", f"Unrecognized request URL (GET: {path})")

    def do_POST(self):
        length = int(self.headers.get("Content-Length") or 0)
        if length > MAX_BODY:
            self._record()
            self.close_connection = True
            return self._error(413, "invalid_request_error", f"Request body larger than {MAX_BODY} bytes")
        raw = self.rfile.read(length) if length else b""
        self._record(raw)
        if self.path != "/v1/render":
            return self._error(404, "invalid_request_error", f"Unrecognized request URL (POST: {self.path})")
        key = self._auth()
        if key is None:
            return
        fault = self.state.next_fault()
        if fault and "status" in fault:
            if fault["status"] == 429:
                return self._error(429, "rate_limit_error", "Too many requests. Retry after the time in Retry-After.",
                                   extra={"Retry-After": fault.get("retry_after", 1)})
            return self._error(fault["status"], "api_error", "MapDraw had a problem rendering. Try again.")
        if fault and fault.get("drop") == "before_accept":
            self.close_connection = True
            return
        ctype = self.headers.get("Content-Type", "")
        if not ctype.split(";")[0].strip().lower() == "application/json":
            return self._error(400, "invalid_request_error", "Content-Type must be application/json")
        try:
            body = json.loads(raw)
        except ValueError:
            return self._error(400, "invalid_request_error", "Request body is not valid JSON")
        try:
            validate(body)
        except Invalid as e:
            return self._error(400, "invalid_request_error", str(e), e.param)

        ikey = self.headers.get("Idempotency-Key")
        if ikey is not None and not 1 <= len(ikey) <= 255:
            return self._error(400, "invalid_request_error", "Idempotency-Key must be 1 to 255 characters")
        body_hash = hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()
        with self.state.lock:
            rid = self.state.by_key.get((key, ikey)) if ikey else None
            replay = self.state.renders.get(rid) if rid else None
        if replay is not None:
            if replay.body_hash != body_hash:
                return self._error(409, "idempotency_error",
                                   "Keys for idempotent requests can only be used with the same parameters "
                                   "they were first used with.")
            return self._send(200, replay.png, "image/png",
                              {"X-Render-Id": replay.id, "X-Billed-Credits": 0, "Idempotent-Replayed": "true"})

        png = draw_png(body)
        with self.state.lock:
            rid = f"rnd_{len(self.state.renders) + 1:05d}"
            self.state.renders[rid] = Render(rid, int(time.time()), ikey, body_hash, png)
            if ikey:
                self.state.by_key[(key, ikey)] = rid
            self.state.billed += 1
        if fault and fault.get("drop") == "after_accept":
            self.close_connection = True
            return
        self._send(200, png, "image/png", {"X-Render-Id": rid, "X-Billed-Credits": 1})


def make_server(port=8080, host="127.0.0.1", state=None, verbose=False):
    state = state or State()
    handler = type("BoundHandler", (Handler,), {"state": state, "verbose": verbose})
    server = ThreadingHTTPServer((host, port), handler)
    server.daemon_threads = True
    return server, state


class Running:
    def __init__(self, server, state, thread):
        self.server, self.state, self.thread = server, state, thread
        self.url = f"http://127.0.0.1:{server.server_address[1]}"

    def stop(self):
        self.server.shutdown()
        self.server.server_close()


def start_in_thread(port=0, **state_kw):
    """Start on a free port in a daemon thread. Returns an object with .url, .state, .stop()."""
    server, state = make_server(port, state=State(**state_kw))
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    return Running(server, state, t)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--port", type=int, default=8080)
    ap.add_argument("--fault-rate", type=float, default=0.0, help="share of renders that fail (0 to 1)")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("-v", "--verbose", action="store_true")
    a = ap.parse_args()
    server, state = make_server(a.port, state=State(fault_rate=a.fault_rate, seed=a.seed), verbose=a.verbose)
    print(f"MapDraw fake on http://127.0.0.1:{a.port}  test key: {API_KEYS[0]}  fault rate: {a.fault_rate}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        print(f"\nbilled renders: {state.billed}")


if __name__ == "__main__":
    main()
