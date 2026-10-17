"""Regression tests a strong candidate adds while fixing tickets SEC-212 and SUP-418."""
import io
import unittest

import minireq
from minireq.exceptions import UnrewindableBodyError
from tests.httpbin import TIMEOUT, HttpbinTestCase


class RedirectRegressionTests(HttpbinTestCase):
    def test_sec_212_auth_not_sent_to_other_host(self):
        other_host = f"http://localhost:{self.bin.port}/headers"
        r = minireq.get(self.httpbin("redirect-to"), params={"url": other_host},
                        headers={"Authorization": "Bearer secret"}, timeout=TIMEOUT)
        self.assertNotIn("Authorization", r.json()["headers"])

    def test_sec_212_auth_kept_on_same_host(self):
        r = minireq.get(self.httpbin("redirect-to"), params={"url": "headers"},
                        headers={"Authorization": "Bearer secret"}, timeout=TIMEOUT)
        self.assertEqual(r.json()["headers"]["Authorization"], "Bearer secret")

    def test_sup_418_308_keeps_post_and_body(self):
        r = minireq.post(self.httpbin("redirect-to"), data="export",
                         params={"url": "anything", "status_code": 308}, timeout=TIMEOUT)
        self.assertEqual((r.json()["method"], r.json()["data"]), ("POST", "export"))

    def test_generator_body_on_307_raises(self):
        with self.assertRaises(UnrewindableBodyError):
            minireq.post(self.httpbin("redirect-to"), data=(b for b in [b"a"]),
                         params={"url": "post", "status_code": 307}, timeout=TIMEOUT)

    def test_partial_stream_through_two_307s(self):
        inner = "/redirect-to?url=/post&status_code=307"
        stream = io.BytesIO(b"hello world")
        stream.read(5)
        r = minireq.post(self.httpbin("redirect-to"), data=stream,
                         params={"url": inner, "status_code": 307}, timeout=TIMEOUT)
        self.assertEqual(r.json()["data"], " world")


if __name__ == "__main__":
    unittest.main()
