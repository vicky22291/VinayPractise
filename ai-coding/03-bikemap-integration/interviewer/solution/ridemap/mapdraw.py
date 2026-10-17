"""Small client for the MapDraw render API. Reference: docs/MAPDRAW_API.md."""
import json
import logging
import time
import urllib.error
import urllib.request
import uuid

from ridemap.errors import MapDrawError

log = logging.getLogger(__name__)

RETRY_STATUSES = {500, 502, 503, 504}
MAX_ATTEMPTS = 5
FIRST_BACKOFF = 0.5


class MapDrawClient:
    def __init__(self, base_url, api_key, timeout=10, sleep=time.sleep):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self.sleep = sleep

    def _request(self, method, path, body=None, headers=None):
        """One HTTP call. Returns (status, headers, bytes). Network errors propagate."""
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(self.base_url + path, data=data, method=method)
        req.add_header("Authorization", f"Bearer {self.api_key}")
        if data is not None:
            req.add_header("Content-Type", "application/json")
        for k, v in (headers or {}).items():
            req.add_header(k, v)
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                return resp.status, resp.headers, resp.read()
        except urllib.error.HTTPError as e:  # subclass of URLError: catch it first
            return e.code, e.headers, e.read()

    def render(self, body):
        """POST /v1/render and return the PNG bytes.

        One idempotency key per call, reused on every retry, so a lost response
        costs no second credit.
        """
        key = str(uuid.uuid4())
        backoff = FIRST_BACKOFF
        for attempt in range(1, MAX_ATTEMPTS + 1):
            try:
                status, headers, payload = self._request("POST", "/v1/render", body, {"Idempotency-Key": key})
            except (urllib.error.URLError, ConnectionError, TimeoutError) as e:
                status, headers, payload, reason = None, {}, b"", f"network error: {e}"
            else:
                if status == 200:
                    log.info("render ok key=%s render=%s replayed=%s attempt=%d", key,
                             headers.get("X-Render-Id"), headers.get("Idempotent-Replayed", "false"), attempt)
                    return payload
                reason = _error_message(payload)
                if status != 429 and status not in RETRY_STATUSES:
                    raise MapDrawError(status, reason)
            if attempt == MAX_ATTEMPTS:
                raise MapDrawError(status or 0, f"gave up after {attempt} attempts: {reason}")
            if status == 429:
                wait = float(headers.get("Retry-After") or backoff)
            else:
                wait, backoff = backoff, backoff * 2
            log.warning("render retry key=%s attempt=%d status=%s wait=%.1fs: %s", key, attempt, status, wait, reason)
            self.sleep(wait)


def _error_message(payload):
    try:
        return json.loads(payload)["error"]["message"]
    except (ValueError, KeyError, TypeError):
        return payload[:200].decode("utf-8", "replace")
