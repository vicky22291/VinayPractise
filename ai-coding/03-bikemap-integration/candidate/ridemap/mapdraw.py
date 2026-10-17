"""Small client for the MapDraw render API. Reference: docs/MAPDRAW_API.md."""
import json
import urllib.error
import urllib.request

from ridemap.errors import MapDrawError


class MapDrawClient:
    def __init__(self, base_url, api_key, timeout=10):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout

    def _request(self, method, path, body=None):
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(self.base_url + path, data=data, method=method)
        req.add_header("X-Api-Key", self.api_key)
        req.add_header("Content-Type", "application/json")
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                return resp.status, resp.read().decode("utf-8")
        except urllib.error.HTTPError as e:
            raise MapDrawError(e.code, e.read().decode("utf-8")) from None

    def render(self, body):
        """POST /v1/render."""
        _, payload = self._request("POST", "/v1/render", body)
        return payload
