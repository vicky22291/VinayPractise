"""The objects that move through minireq: Request -> PreparedRequest -> Response."""
import datetime
import io
import json as complexjson
from collections.abc import Mapping
from urllib.parse import urlencode, urlsplit, urlunsplit

from minireq.auth import HTTPBasicAuth
from minireq.cookies import CookieJar, cookiejar_from_dict, get_cookie_header
from minireq.exceptions import HTTPError, InvalidJSONError, InvalidURL, JSONDecodeError, MissingSchema
from minireq.status_codes import REDIRECT_STATI, codes
from minireq.structures import CaseInsensitiveDict
from minireq.utils import (
    check_header_validity,
    get_auth_from_url,
    get_encoding_from_headers,
    super_len,
    to_key_val_list,
)


class RequestEncodingMixin:
    @property
    def path_url(self):
        """The path and query string that go on the request line."""
        parts = urlsplit(self.url)
        path = parts.path or "/"
        return f"{path}?{parts.query}" if parts.query else path

    @staticmethod
    def _encode_params(data):
        """Form-encode a dict or list of pairs. Strings, bytes and files pass through."""
        if isinstance(data, (str, bytes)) or hasattr(data, "read"):
            return data
        if hasattr(data, "__iter__"):
            result = []
            for key, values in to_key_val_list(data):
                if isinstance(values, (str, bytes)) or not hasattr(values, "__iter__"):
                    values = [values]
                for value in values:
                    if value is not None:
                        result.append((key, value))
            return urlencode(result, doseq=True)
        return data


class Request:
    """A request as the caller described it. `prepare()` turns it into what is sent."""

    def __init__(self, method=None, url=None, headers=None, data=None, params=None,
                 auth=None, cookies=None, json=None):
        self.method = method
        self.url = url
        self.headers = {} if headers is None else headers
        self.data = [] if data is None else data
        self.json = json
        self.params = {} if params is None else params
        self.auth = auth
        self.cookies = cookies

    def __repr__(self):
        return f"<Request [{self.method}]>"

    def prepare(self):
        p = PreparedRequest()
        p.prepare(method=self.method, url=self.url, headers=self.headers, data=self.data,
                  json=self.json, params=self.params, auth=self.auth, cookies=self.cookies)
        return p


class PreparedRequest(RequestEncodingMixin):
    """Exactly what goes on the wire: method, URL, headers and body.

    Sessions send these. When a redirect is followed, the session works on a
    copy() of the previous PreparedRequest.
    """

    def __init__(self):
        self.method = None
        self.url = None
        self.headers = None
        self._cookies = None
        self.body = None
        self._body_position = None

    def prepare(self, method=None, url=None, headers=None, data=None, params=None,
                auth=None, cookies=None, json=None):
        self.prepare_method(method)
        self.prepare_url(url, params)
        self.prepare_headers(headers)
        self.prepare_cookies(cookies)
        self.prepare_body(data, json)
        self.prepare_auth(auth)

    def __repr__(self):
        return f"<PreparedRequest [{self.method}]>"

    def copy(self):
        p = PreparedRequest()
        p.method = self.method
        p.url = self.url
        p.headers = self.headers.copy() if self.headers is not None else None
        p._cookies = self._cookies.copy() if self._cookies is not None else None
        p.body = self.body
        p._body_position = self._body_position
        return p

    def prepare_method(self, method):
        self.method = method.upper() if method is not None else None

    def prepare_url(self, url, params):
        url = str(url).strip()
        parts = urlsplit(url)
        if not parts.scheme:
            raise MissingSchema(f"Invalid URL {url!r}: no scheme supplied. Perhaps you meant https://{url}?")
        if not parts.hostname:
            raise InvalidURL(f"Invalid URL {url!r}: no host supplied")
        query = parts.query
        encoded = self._encode_params(params) if params else ""
        if isinstance(encoded, bytes):
            encoded = encoded.decode("utf-8")
        if encoded:
            query = f"{query}&{encoded}" if query else encoded
        self.url = urlunsplit((parts.scheme, parts.netloc, parts.path or "/", query, parts.fragment))

    def prepare_headers(self, headers):
        self.headers = CaseInsensitiveDict()
        if headers:
            for header in headers.items():
                check_header_validity(header)
                name, value = header
                self.headers[name] = value

    def prepare_body(self, data, json=None):
        body = None
        content_type = None

        if not data and json is not None:
            content_type = "application/json"
            try:
                body = complexjson.dumps(json, allow_nan=False).encode("utf-8")
            except ValueError as e:
                raise InvalidJSONError(e, request=self)

        is_stream = hasattr(data, "__iter__") and not isinstance(data, (str, bytes, list, tuple, Mapping))

        if is_stream:
            try:
                length = super_len(data)
            except (TypeError, AttributeError, io.UnsupportedOperation):
                length = None
            body = data
            if getattr(body, "tell", None) is not None:
                # Record the current file position before reading, so the
                # body can be sent again if a redirect needs it.
                try:
                    self._body_position = body.tell()
                except OSError:
                    # Distinct from None: there is a position, we just could not read it.
                    self._body_position = object()
            if length:
                self.headers["Content-Length"] = str(length)
            else:
                self.headers["Transfer-Encoding"] = "chunked"
        else:
            if data:
                body = self._encode_params(data)
                if not isinstance(data, (str, bytes)):
                    content_type = "application/x-www-form-urlencoded"
            if isinstance(body, str):
                body = body.encode("utf-8")
            self.prepare_content_length(body)
            if content_type and "content-type" not in self.headers:
                self.headers["Content-Type"] = content_type

        self.body = body

    def prepare_content_length(self, body):
        if body is not None:
            length = super_len(body)
            if length:
                self.headers["Content-Length"] = str(length)
        elif self.method not in ("GET", "HEAD") and self.headers.get("Content-Length") is None:
            self.headers["Content-Length"] = "0"

    def prepare_auth(self, auth):
        if auth is None:
            url_auth = get_auth_from_url(self.url)
            auth = url_auth if any(url_auth) else None
        if auth:
            if isinstance(auth, tuple) and len(auth) == 2:
                auth = HTTPBasicAuth(*auth)
            r = auth(self)
            self.__dict__.update(r.__dict__)

    def prepare_cookies(self, cookies):
        """Set the Cookie header. Does nothing if one is already there."""
        if isinstance(cookies, CookieJar):
            self._cookies = cookies
        else:
            self._cookies = cookiejar_from_dict(cookies)
        if "Cookie" in self.headers:
            return
        cookie_header = get_cookie_header(self._cookies, self.url)
        if cookie_header is not None:
            self.headers["Cookie"] = cookie_header


class Response:
    """The server's answer. `history` lists the redirect responses that led here, oldest first."""

    def __init__(self):
        self._content = b""
        self.status_code = None
        self.headers = CaseInsensitiveDict()
        self.raw_set_cookie = []
        self.url = None
        self.encoding = None
        self.history = []
        self.reason = None
        self.cookies = CookieJar()
        self.elapsed = datetime.timedelta(0)
        self.request = None

    def __repr__(self):
        return f"<Response [{self.status_code}]>"

    def __bool__(self):
        return self.ok

    @property
    def ok(self):
        try:
            self.raise_for_status()
        except HTTPError:
            return False
        return True

    @property
    def is_redirect(self):
        return "location" in self.headers and self.status_code in REDIRECT_STATI

    @property
    def is_permanent_redirect(self):
        return "location" in self.headers and self.status_code in (
            codes.moved_permanently,
            codes.permanent_redirect,
        )

    @property
    def content(self):
        return self._content

    @property
    def text(self):
        encoding = self.encoding or "utf-8"
        try:
            return str(self._content, encoding, errors="replace")
        except LookupError:
            return str(self._content, "utf-8", errors="replace")

    def json(self, **kwargs):
        try:
            return complexjson.loads(self.text, **kwargs)
        except complexjson.JSONDecodeError as e:
            raise JSONDecodeError(e.msg, e.doc, e.pos, response=self)

    def raise_for_status(self):
        if 400 <= self.status_code < 500:
            raise HTTPError(f"{self.status_code} Client Error: {self.reason} for url: {self.url}", response=self)
        if 500 <= self.status_code < 600:
            raise HTTPError(f"{self.status_code} Server Error: {self.reason} for url: {self.url}", response=self)

    def close(self):
        """The body is read eagerly, so there is nothing to release. Kept for API parity."""
