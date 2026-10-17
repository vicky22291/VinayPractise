import io
import unittest

import minireq
from minireq.exceptions import TooManyRedirects
from tests.httpbin import TIMEOUT, HttpbinTestCase


class RedirectTests(HttpbinTestCase):
    def test_HTTP_200_OK_GET(self):
        r = minireq.get(self.httpbin("get"), timeout=TIMEOUT)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.history, [])

    def test_HTTP_302_ALLOW_REDIRECT_GET(self):
        r = minireq.get(self.httpbin("redirect", "1"), timeout=TIMEOUT)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.history[0].status_code, 302)
        self.assertTrue(r.history[0].is_redirect)

    def test_redirect_history_is_oldest_first(self):
        r = minireq.get(self.httpbin("redirect", "3"), timeout=TIMEOUT)
        self.assertEqual([h.status_code for h in r.history], [302, 302, 302])
        self.assertEqual(
            [h.url.rsplit("/", 1)[1] for h in r.history], ["3", "2", "1"]
        )
        self.assertTrue(r.url.endswith("/get"))

    def test_HTTP_302_TOO_MANY_REDIRECTS(self):
        s = minireq.Session()
        s.max_redirects = 5
        with self.assertRaises(TooManyRedirects):
            s.get(self.httpbin("redirect", "20"), timeout=TIMEOUT)

    def test_allow_redirects_false(self):
        r = minireq.get(self.httpbin("redirect", "1"), allow_redirects=False, timeout=TIMEOUT)
        self.assertEqual(r.status_code, 302)
        self.assertTrue(r.is_redirect)
        self.assertEqual(r.history, [])

    def test_relative_location(self):
        r = minireq.get(self.httpbin("redirect-to"), params={"url": "get"}, timeout=TIMEOUT)
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.url.endswith("/get"))

    def test_HTTP_301_CHANGE_POST_TO_GET(self):
        r = minireq.post(self.httpbin("redirect-to"), data="x",
                         params={"url": "anything", "status_code": 301}, timeout=TIMEOUT)
        self.assertEqual(r.json()["method"], "GET")
        self.assertEqual(r.history[0].status_code, 301)

    def test_HTTP_302_CHANGE_POST_TO_GET(self):
        r = minireq.post(self.httpbin("redirect-to"), data="x",
                         params={"url": "get", "status_code": 302}, timeout=TIMEOUT)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["method"], "GET")

    def test_HTTP_303_DROPS_BODY(self):
        r = minireq.post(self.httpbin("redirect-to"), data="x",
                         params={"url": "anything", "status_code": 303}, timeout=TIMEOUT)
        echoed = r.json()
        self.assertEqual(echoed["method"], "GET")
        self.assertEqual(echoed["data"], "")
        self.assertNotIn("Content-Length", echoed["headers"])

    def test_HTTP_307_ALLOW_REDIRECT_POST_DATA(self):
        r = minireq.post(self.httpbin("redirect-to"), data="test",
                         params={"url": "post", "status_code": 307}, timeout=TIMEOUT)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.history[0].status_code, 307)
        self.assertTrue(r.history[0].is_redirect)
        self.assertEqual(r.json()["data"], "test")

    def test_HTTP_307_ALLOW_REDIRECT_POST_WITH_SEEKABLE(self):
        byte_str = b"test"
        r = minireq.post(self.httpbin("redirect-to"), data=io.BytesIO(byte_str),
                         params={"url": "post", "status_code": 307}, timeout=TIMEOUT)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.history[0].status_code, 307)
        self.assertTrue(r.history[0].is_redirect)
        self.assertEqual(r.json()["data"], byte_str.decode("utf-8"))

    def test_HTTP_307_ALLOW_REDIRECT_POST_WITH_PARTIAL_SEEKABLE(self):
        stream = io.BytesIO(b"hello world")
        stream.read(5)
        r = minireq.post(self.httpbin("redirect-to"), data=stream,
                         params={"url": "post", "status_code": 307}, timeout=TIMEOUT)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.history[0].status_code, 307)
        self.assertTrue(r.history[0].is_redirect)
        self.assertEqual(r.json()["data"], " world")


if __name__ == "__main__":
    unittest.main()
