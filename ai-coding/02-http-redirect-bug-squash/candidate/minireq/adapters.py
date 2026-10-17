"""Transport adapters: put a PreparedRequest on a socket and read the Response back.

One connection per request. Bodies are sent as bytes, read from a file-like
object in blocks, or sent with chunked transfer encoding when the length is
unknown.
"""
import datetime
import http.client
import socket
import time
from urllib.parse import urlsplit

from minireq.cookies import extract_cookies_to_jar
from minireq.exceptions import ConnectionError, ConnectTimeout, ReadTimeout
from minireq.models import Response
from minireq.structures import CaseInsensitiveDict
from minireq.utils import get_encoding_from_headers


class BaseAdapter:
    def send(self, request, timeout=None, **kwargs):
        raise NotImplementedError

    def close(self):
        pass


class HTTPAdapter(BaseAdapter):
    """The default adapter for http:// and https:// URLs."""

    block_size = 8192

    @staticmethod
    def _timeouts(timeout):
        """`timeout` may be one number for both phases or a (connect, read) tuple."""
        if isinstance(timeout, tuple):
            connect, read = timeout
            return connect, read
        return timeout, timeout

    def get_connection(self, url, connect_timeout):
        parts = urlsplit(url)
        if parts.scheme == "https":
            return http.client.HTTPSConnection(parts.hostname, parts.port, timeout=connect_timeout)
        return http.client.HTTPConnection(parts.hostname, parts.port, timeout=connect_timeout)

    def send(self, request, timeout=None, **kwargs):
        connect_timeout, read_timeout = self._timeouts(timeout)
        conn = self.get_connection(request.url, connect_timeout)
        started = time.monotonic()
        try:
            try:
                conn.connect()
            except socket.timeout as e:
                raise ConnectTimeout(e, request=request) from None
            except OSError as e:
                raise ConnectionError(e, request=request) from None
            conn.sock.settimeout(read_timeout)
            try:
                self._send_request(conn, request)
                raw = conn.getresponse()
                content = raw.read()
            except socket.timeout as e:
                raise ReadTimeout(e, request=request) from None
            except (http.client.HTTPException, OSError) as e:
                raise ConnectionError(e, request=request) from None
        finally:
            conn.close()
        response = self.build_response(request, raw, content)
        response.elapsed = datetime.timedelta(seconds=time.monotonic() - started)
        return response

    def _send_request(self, conn, request):
        conn.putrequest(request.method, request.path_url, skip_accept_encoding=True)
        for name, value in request.headers.items():
            conn.putheader(name, value)
        conn.endheaders()

        body = request.body
        if body is None:
            return
        if isinstance(body, str):
            body = body.encode("utf-8")
        if isinstance(body, bytes):
            conn.send(body)
            return

        chunked = request.headers.get("Transfer-Encoding", "").lower() == "chunked"
        for block in self._iter_body(body):
            if not block:
                continue
            if chunked:
                conn.send(b"%x\r\n%s\r\n" % (len(block), block))
            else:
                conn.send(block)
        if chunked:
            conn.send(b"0\r\n\r\n")

    def _iter_body(self, body):
        """Yield the body in byte blocks, from a file-like object or any iterable."""
        read = getattr(body, "read", None)
        if read is not None:
            while True:
                block = read(self.block_size)
                if not block:
                    return
                yield block.encode("utf-8") if isinstance(block, str) else block
        else:
            for block in body:
                yield block.encode("utf-8") if isinstance(block, str) else block

    def build_response(self, request, raw, content):
        response = Response()
        response.status_code = raw.status
        response.reason = raw.reason
        response.headers = CaseInsensitiveDict(raw.getheaders())
        response.raw_set_cookie = raw.msg.get_all("Set-Cookie") or []
        response.encoding = get_encoding_from_headers(response.headers)
        response._content = content
        response.url = request.url
        response.request = request
        extract_cookies_to_jar(response.cookies, request, response)
        return response
