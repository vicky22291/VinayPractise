import io
import unittest

from minireq.models import PreparedRequest
from minireq.structures import CaseInsensitiveDict
from minireq.utils import get_encoding_from_headers, super_len, to_key_val_list


class CaseInsensitiveDictTests(unittest.TestCase):
    def test_lookup_ignores_case(self):
        d = CaseInsensitiveDict({"Content-Type": "text/plain"})
        self.assertEqual(d["content-type"], "text/plain")
        self.assertIn("CONTENT-TYPE", d)

    def test_keeps_original_case(self):
        d = CaseInsensitiveDict()
        d["X-Trace-Id"] = "1"
        self.assertEqual(list(d), ["X-Trace-Id"])

    def test_copy_is_independent(self):
        d = CaseInsensitiveDict({"A": "1"})
        e = d.copy()
        e["a"] = "2"
        self.assertEqual(d["A"], "1")


class UtilsTests(unittest.TestCase):
    def test_super_len(self):
        self.assertEqual(super_len(b"abcd"), 4)
        self.assertEqual(super_len("héllo"), 6)
        stream = io.BytesIO(b"hello world")
        stream.read(5)
        self.assertEqual(super_len(stream), 6)
        self.assertEqual(stream.tell(), 5)

    def test_to_key_val_list(self):
        self.assertEqual(to_key_val_list({"a": 1}), [("a", 1)])
        with self.assertRaises(ValueError):
            to_key_val_list("ab")

    def test_encoding_from_headers(self):
        self.assertEqual(get_encoding_from_headers({"content-type": "text/html; charset=UTF-8"}), "UTF-8")
        self.assertEqual(get_encoding_from_headers({"content-type": "application/json"}), "utf-8")


class PreparedRequestTests(unittest.TestCase):
    def test_copy_keeps_method_url_headers_body(self):
        p = PreparedRequest()
        p.prepare(method="post", url="http://example.com/x", headers={"X-A": "1"}, data=b"body")
        q = p.copy()
        self.assertEqual((q.method, q.url, q.headers["X-A"], q.body), ("POST", "http://example.com/x", "1", b"body"))
        q.headers["X-A"] = "2"
        self.assertEqual(p.headers["X-A"], "1")


if __name__ == "__main__":
    unittest.main()
