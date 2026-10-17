import unittest

import minireq
from fakebin import TIMEOUT, HttpbinTestCase


class Part2ShouldStripAuth(unittest.TestCase):
    def setUp(self):
        self.s = minireq.Session()

    def strip(self, old, new):
        return self.s.should_strip_auth(old, new)

    def test_different_host_strips(self):
        self.assertTrue(self.strip("https://api.internal.example/v1/export", "https://files.partner-cdn.example/x"))
        self.assertTrue(self.strip("http://a.example/x", "http://b.example/y"))

    def test_lookalike_hosts_strip(self):
        self.assertTrue(self.strip("https://api.example.com/", "https://api.example.com.evil.net/"))
        self.assertTrue(self.strip("https://example.com/", "https://notexample.com/"))
        self.assertTrue(self.strip("https://example.com/", "https://sub.example.com/"))

    def test_upgrade_to_https_on_other_host_strips(self):
        self.assertTrue(self.strip("http://example.com/", "https://other.example/"))

    def test_same_host_keeps(self):
        self.assertFalse(self.strip("http://example.com/a", "http://example.com/b"))
        self.assertFalse(self.strip("http://Example.COM/a", "http://example.com/b"))
        self.assertFalse(self.strip("http://example.com/", "http://example.com:80/"))

    def test_same_host_https_upgrade_keeps(self):
        self.assertFalse(self.strip("http://example.com/", "https://example.com/"))

    def test_same_host_other_port_or_downgrade_strips(self):
        self.assertTrue(self.strip("http://example.com:8080/", "http://example.com:9090/"))
        self.assertTrue(self.strip("https://example.com/", "http://example.com/"))


class Part2EndToEnd(HttpbinTestCase):
    def other_host(self, path):
        return f"http://localhost:{self.bin.port}/{path}"

    def test_bearer_header_not_sent_to_other_host(self):
        r = minireq.get(self.httpbin("redirect-to"), params={"url": self.other_host("headers")},
                        headers={"Authorization": "Bearer sk_live_secret"}, timeout=TIMEOUT)
        self.assertEqual(r.status_code, 200)
        self.assertNotIn("Authorization", r.json()["headers"])

    def test_basic_auth_not_sent_to_other_host(self):
        r = minireq.get(self.httpbin("redirect-to"), params={"url": self.other_host("headers")},
                        auth=("user", "pass"), timeout=TIMEOUT)
        self.assertNotIn("Authorization", r.json()["headers"])

    def test_same_host_redirect_keeps_auth(self):
        r = minireq.get(self.httpbin("redirect-to"), params={"url": "headers"},
                        headers={"Authorization": "Bearer t"}, timeout=TIMEOUT)
        self.assertEqual(r.json()["headers"]["Authorization"], "Bearer t")


if __name__ == "__main__":
    unittest.main()
