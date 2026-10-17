import io
import unittest

import minireq
from fakebin import TIMEOUT, HttpbinTestCase


class PipeLike:
    """A stream like a pipe: readable and iterable, but tell() and seek() fail."""

    def __init__(self, data):
        self._buf = io.BytesIO(data)

    def read(self, n=-1):
        return self._buf.read(n)

    def __iter__(self):
        return iter(self._buf)

    def tell(self):
        raise OSError("illegal seek")

    def seek(self, *args):
        raise OSError("illegal seek")


class SeekFails(io.BytesIO):
    """tell() works but seek() fails, like a buffered socket."""

    def seek(self, *args):
        raise io.UnsupportedOperation("seek")


class Part4Unrewindable(HttpbinTestCase):
    def send(self, data, status=307, url="post"):
        return minireq.post(self.httpbin("redirect-to"), data=data,
                            params={"url": url, "status_code": status}, timeout=TIMEOUT)

    def paths(self):
        return [entry["path"] for entry in self.bin.log]

    def test_error_class_exists_and_is_request_exception(self):
        from minireq.exceptions import RequestException, UnrewindableBodyError
        self.assertTrue(issubclass(UnrewindableBodyError, RequestException))

    def test_generator_on_307_raises_and_sends_nothing_more(self):
        from minireq.exceptions import UnrewindableBodyError
        with self.assertRaises(UnrewindableBodyError):
            self.send((b for b in [b"chunk-1", b"chunk-2"]))
        self.assertEqual(self.paths(), ["/redirect-to"])

    def test_generator_on_308_raises(self):
        from minireq.exceptions import UnrewindableBodyError
        with self.assertRaises(UnrewindableBodyError):
            self.send((b for b in [b"x"]), status=308, url="anything")

    def test_iterator_on_307_raises(self):
        from minireq.exceptions import UnrewindableBodyError
        with self.assertRaises(UnrewindableBodyError):
            self.send(iter([b"a", b"b"]))

    def test_pipe_like_on_307_raises(self):
        from minireq.exceptions import UnrewindableBodyError
        with self.assertRaises(UnrewindableBodyError):
            self.send(PipeLike(b"abc"))
        self.assertEqual(self.paths(), ["/redirect-to"])

    def test_seek_failure_on_307_raises_our_error(self):
        from minireq.exceptions import UnrewindableBodyError
        with self.assertRaises(UnrewindableBodyError):
            self.send(SeekFails(b"abc"))

    def test_generator_on_302_does_not_raise(self):
        r = self.send((b for b in [b"x"]), status=302, url="anything")
        self.assertEqual((r.json()["method"], r.json()["data"]), ("GET", ""))

    def test_generator_without_redirect_still_works(self):
        r = minireq.post(self.httpbin("post"), data=(b for b in [b"ab", b"cd"]), timeout=TIMEOUT)
        self.assertEqual(r.json()["data"], "abcd")

    def test_rewindable_bodies_still_work(self):
        self.assertEqual(self.send("text").json()["data"], "text")
        self.assertEqual(self.send(b"bytes").json()["data"], "bytes")
        self.assertEqual(self.send(io.BytesIO(b"seekable")).json()["data"], "seekable")
        r = minireq.post(self.httpbin("redirect-to"), data={"k": "v"},
                         params={"url": "post", "status_code": 307}, timeout=TIMEOUT)
        self.assertEqual(r.json()["form"], {"k": "v"})


if __name__ == "__main__":
    unittest.main()
