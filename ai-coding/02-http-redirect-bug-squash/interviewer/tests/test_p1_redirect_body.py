import io
import tempfile
import unittest

import minireq
from fakebin import TIMEOUT, HttpbinTestCase


class Part1RedirectBody(HttpbinTestCase):
    def post_307(self, data, url="post", status=307, method="post"):
        return minireq.request(method, self.httpbin("redirect-to"), data=data,
                               params={"url": url, "status_code": status}, timeout=TIMEOUT)

    def test_HTTP_307_ALLOW_REDIRECT_POST_DATA(self):
        r = self.post_307("test")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.history[0].status_code, 307)
        self.assertTrue(r.history[0].is_redirect)
        self.assertEqual(r.json()["data"], "test")

    def test_HTTP_307_ALLOW_REDIRECT_POST_WITH_SEEKABLE(self):
        r = self.post_307(io.BytesIO(b"test"))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.history[0].status_code, 307)
        self.assertEqual(r.json()["data"], "test")

    def test_HTTP_307_ALLOW_REDIRECT_POST_WITH_PARTIAL_SEEKABLE(self):
        stream = io.BytesIO(b"hello world")
        stream.read(5)
        r = self.post_307(stream)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["data"], " world")

    def test_307_put_with_seekable(self):
        r = self.post_307(io.BytesIO(b"payload"), url="anything", method="put")
        self.assertEqual((r.json()["method"], r.json()["data"]), ("PUT", "payload"))

    def test_308_put_with_partial_seekable(self):
        stream = io.BytesIO(b"skip-me:keep-me")
        stream.read(8)
        r = self.post_307(stream, url="anything", status=308, method="put")
        self.assertEqual((r.json()["method"], r.json()["data"]), ("PUT", "keep-me"))

    def test_partial_seekable_through_two_307_hops(self):
        stream = io.BytesIO(b"hello world")
        stream.read(5)
        r = self.post_307(stream, url="/redirect-to?url=/post&status_code=307")
        self.assertEqual([h.status_code for h in r.history], [307, 307])
        self.assertEqual(r.json()["data"], " world")

    def test_real_file_partially_read(self):
        with tempfile.TemporaryFile() as f:
            f.write(b"0123456789")
            f.seek(3)
            r = self.post_307(f)
        self.assertEqual(r.json()["data"], "3456789")

    def test_json_body_survives_307(self):
        r = minireq.post(self.httpbin("redirect-to"), json={"amount": 1200},
                         params={"url": "post", "status_code": 307}, timeout=TIMEOUT)
        self.assertEqual(r.json()["json"], {"amount": 1200})

    def test_303_still_drops_seekable_body_and_headers(self):
        r = self.post_307(io.BytesIO(b"test"), url="anything", status=303)
        echoed = r.json()
        self.assertEqual((echoed["method"], echoed["data"]), ("GET", ""))
        for header in ("Content-Length", "Transfer-Encoding", "Content-Type"):
            self.assertNotIn(header, echoed["headers"])

    def test_302_still_drops_seekable_body(self):
        r = self.post_307(io.BytesIO(b"test"), url="anything", status=302)
        self.assertEqual((r.json()["method"], r.json()["data"]), ("GET", ""))

    def test_301_still_turns_post_into_get(self):
        r = self.post_307(io.BytesIO(b"test"), url="anything", status=301)
        self.assertEqual((r.json()["method"], r.json()["data"]), ("GET", ""))


if __name__ == "__main__":
    unittest.main()
