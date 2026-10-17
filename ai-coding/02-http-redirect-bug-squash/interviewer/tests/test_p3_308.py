import io
import unittest

import minireq
from fakebin import TIMEOUT, HttpbinTestCase


class Part3PermanentRedirect(HttpbinTestCase):
    def post(self, data, status):
        return minireq.post(self.httpbin("redirect-to"), data=data,
                            params={"url": "anything", "status_code": status}, timeout=TIMEOUT)

    def test_308_keeps_post_and_string_body(self):
        r = self.post("export-batch-7", 308)
        self.assertEqual(r.history[0].status_code, 308)
        self.assertEqual((r.json()["method"], r.json()["data"]), ("POST", "export-batch-7"))

    def test_308_keeps_post_and_partial_stream(self):
        stream = io.BytesIO(b"hello world")
        stream.read(5)
        r = self.post(stream, 308)
        self.assertEqual((r.json()["method"], r.json()["data"]), ("POST", " world"))

    def test_308_reaches_post_only_endpoint(self):
        r = minireq.post(self.httpbin("redirect-to"), data="x",
                         params={"url": "post", "status_code": 308}, timeout=TIMEOUT)
        self.assertEqual(r.status_code, 200)

    def test_301_still_turns_post_into_get(self):
        r = self.post("x", 301)
        self.assertEqual((r.json()["method"], r.json()["data"]), ("GET", ""))

    def test_307_still_keeps_post(self):
        r = self.post("x", 307)
        self.assertEqual(r.json()["method"], "POST")

    def test_is_permanent_redirect_unchanged(self):
        r = minireq.post(self.httpbin("redirect-to"), data="x", allow_redirects=False,
                         params={"url": "anything", "status_code": 308}, timeout=TIMEOUT)
        self.assertTrue(r.is_permanent_redirect)


if __name__ == "__main__":
    unittest.main()
