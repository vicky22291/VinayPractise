"""A small cookie jar.

Cookies set by a response are stored under the host that set them (or the
Domain attribute) and are sent back only to that host and its subdomains.
Cookies the caller adds without a host are sent with every request that uses
the jar.
"""
from http.cookies import CookieError, SimpleCookie
from urllib.parse import urlparse


class CookieJar:
    def __init__(self):
        self._cookies = {}  # (host, name) -> value

    def set(self, name, value, host=""):
        if value is None:
            self._cookies.pop((host, name), None)
        else:
            self._cookies[(host, name)] = value

    def get(self, name, default=None, host=None):
        for (h, n), v in self._cookies.items():
            if n == name and (host is None or h == host):
                return v
        return default

    def get_dict(self, host=None):
        return {n: v for (h, n), v in self._cookies.items() if host is None or h == host}

    def for_url(self, url):
        """The cookies that should be sent to `url`, as a dict."""
        hostname = (urlparse(url).hostname or "").lower()
        out = {}
        for (h, n), v in self._cookies.items():
            if not h or hostname == h or hostname.endswith("." + h):
                out[n] = v
        return out

    def update(self, other):
        if isinstance(other, CookieJar):
            self._cookies.update(other._cookies)
        else:
            for name, value in other.items():
                self.set(name, value)

    def copy(self):
        new = CookieJar()
        new._cookies = dict(self._cookies)
        return new

    def clear(self):
        self._cookies.clear()

    def __getitem__(self, name):
        value = self.get(name)
        if value is None:
            raise KeyError(name)
        return value

    def __setitem__(self, name, value):
        self.set(name, value)

    def __contains__(self, name):
        return any(n == name for (_, n) in self._cookies)

    def __iter__(self):
        return iter([n for (_, n) in self._cookies])

    def __len__(self):
        return len(self._cookies)

    def __repr__(self):
        return f"<CookieJar {self.get_dict()}>"


def cookiejar_from_dict(cookie_dict, jar=None):
    jar = CookieJar() if jar is None else jar
    for name, value in (cookie_dict or {}).items():
        jar.set(name, value)
    return jar


def merge_cookies(jar, cookies):
    """Add `cookies` (a CookieJar or a dict) into `jar` and return `jar`."""
    if cookies is not None:
        jar.update(cookies)
    return jar


def extract_cookies_to_jar(jar, request, response):
    """Store the Set-Cookie headers of `response` (an answer to `request`) in `jar`."""
    host = (urlparse(request.url).hostname or "").lower()
    for header in getattr(response, "raw_set_cookie", []):
        parsed = SimpleCookie()
        try:
            parsed.load(header)
        except CookieError:
            continue
        for name, morsel in parsed.items():
            domain = morsel["domain"].lstrip(".").lower() or host
            if morsel["max-age"] == "0":
                jar.set(name, None, host=domain)
            else:
                jar.set(name, morsel.value, host=domain)


def get_cookie_header(jar, url):
    cookies = jar.for_url(url)
    if not cookies:
        return None
    return "; ".join(f"{name}={value}" for name, value in cookies.items())
