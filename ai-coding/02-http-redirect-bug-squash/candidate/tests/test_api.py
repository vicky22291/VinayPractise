import io
import socket
import unittest

import minireq
from minireq.exceptions import ConnectionError, HTTPError
from tests.httpbin import TIMEOUT, HttpbinTestCase


class ApiTests(HttpbinTestCase):
    def test_get_with_params(self):
        r = minireq.get(self.httpbin("get") + "?a=1", params={"b": "2"}, timeout=TIMEOUT)
        self.assertEqual(r.json()["args"], {"a": "1", "b": "2"})

    def test_post_form(self):
        r = minireq.post(self.httpbin("post"), data={"amount": "1200"}, timeout=TIMEOUT)
        self.assertEqual(r.json()["form"], {"amount": "1200"})
        self.assertEqual(r.json()["headers"]["Content-Type"], "application/x-www-form-urlencoded")

    def test_post_json(self):
        r = minireq.post(self.httpbin("post"), json={"ids": [1, 2]}, timeout=TIMEOUT)
        self.assertEqual(r.json()["json"], {"ids": [1, 2]})

    def test_post_bytes(self):
        r = minireq.post(self.httpbin("post"), data=b"raw-bytes", timeout=TIMEOUT)
        self.assertEqual(r.json()["data"], "raw-bytes")

    def test_put_file_body(self):
        r = minireq.put(self.httpbin("put"), data=io.BytesIO(b"abc"), timeout=TIMEOUT)
        self.assertEqual(r.json()["data"], "abc")
        self.assertEqual(r.json()["headers"]["Content-Length"], "3")

    def test_generator_body_is_chunked(self):
        r = minireq.post(self.httpbin("post"), data=(b for b in [b"ab", b"cd"]), timeout=TIMEOUT)
        self.assertEqual(r.json()["data"], "abcd")
        self.assertEqual(r.json()["headers"]["Transfer-Encoding"], "chunked")

    def test_custom_and_default_headers(self):
        r = minireq.get(self.httpbin("headers"), headers={"X-Trace-Id": "abc"}, timeout=TIMEOUT)
        headers = r.json()["headers"]
        self.assertEqual(headers["X-Trace-Id"], "abc")
        self.assertTrue(headers["User-Agent"].startswith("python-minireq/"))

    def test_session_headers_merge(self):
        with minireq.Session() as s:
            s.headers["X-Team"] = "payments"
            r = s.get(self.httpbin("headers"), headers={"X-Req": "1"}, timeout=TIMEOUT)
        headers = r.json()["headers"]
        self.assertEqual((headers["X-Team"], headers["X-Req"]), ("payments", "1"))

    def test_basic_auth(self):
        url = self.httpbin("basic-auth", "user", "pass")
        self.assertEqual(minireq.get(url, auth=("user", "pass"), timeout=TIMEOUT).status_code, 200)
        r = minireq.get(url, auth=("user", "wrong"), timeout=TIMEOUT)
        self.assertEqual(r.status_code, 401)
        self.assertFalse(r.ok)
        with self.assertRaises(HTTPError):
            r.raise_for_status()

    def test_session_cookies_follow_redirect(self):
        with minireq.Session() as s:
            r = s.get(self.httpbin("cookies", "set") + "?flavor=oat", timeout=TIMEOUT)
            self.assertEqual(r.json()["cookies"], {"flavor": "oat"})
            self.assertEqual(s.cookies.get("flavor"), "oat")

    def test_connection_refused(self):
        sock = socket.socket()
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
        sock.close()
        with self.assertRaises(ConnectionError):
            minireq.get(f"http://127.0.0.1:{port}/", timeout=TIMEOUT)


if __name__ == "__main__":
    unittest.main()
