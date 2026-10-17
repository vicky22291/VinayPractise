"""Session: shared headers, auth, cookies and adapters across requests, plus redirect handling."""
from collections.abc import Mapping
from urllib.parse import urljoin, urlparse

from minireq.adapters import HTTPAdapter
from minireq.cookies import CookieJar, cookiejar_from_dict, extract_cookies_to_jar, merge_cookies
from minireq.exceptions import InvalidSchema, TooManyRedirects
from minireq.models import PreparedRequest, Request
from minireq.status_codes import codes
from minireq.structures import CaseInsensitiveDict
from minireq.utils import DEFAULT_PORTS, default_headers, rewind_body, to_key_val_list

DEFAULT_REDIRECT_LIMIT = 30


def merge_setting(request_setting, session_setting, dict_class=dict):
    """Merge a per-request setting over the session's. A request value of None removes the key."""
    if session_setting is None:
        return request_setting
    if request_setting is None:
        return session_setting
    if not (isinstance(session_setting, Mapping) and isinstance(request_setting, Mapping)):
        return request_setting
    merged = dict_class(to_key_val_list(session_setting))
    merged.update(to_key_val_list(request_setting))
    for key in [k for k, v in merged.items() if v is None]:
        del merged[key]
    return merged


class SessionRedirectMixin:
    def get_redirect_target(self, resp):
        """The Location of a redirect response, or None."""
        if resp.is_redirect:
            return resp.headers["location"]
        return None

    def should_strip_auth(self, old_url, new_url):
        """Decide whether the Authorization header must be removed when redirecting."""
        old_parsed = urlparse(old_url)
        new_parsed = urlparse(new_url)
        # Allow an http -> https upgrade on the standard ports. RFC 7235 does not
        # require this, but older releases allowed it and callers rely on it.
        if (
            old_parsed.scheme == "http"
            and old_parsed.port in (80, None)
            and new_parsed.scheme == "https"
            and new_parsed.port in (443, None)
        ):
            return False

        changed_port = old_parsed.port != new_parsed.port
        changed_scheme = old_parsed.scheme != new_parsed.scheme
        default_port = (DEFAULT_PORTS.get(old_parsed.scheme, None), None)
        if not changed_scheme and old_parsed.port in default_port and new_parsed.port in default_port:
            return False

        return changed_port or changed_scheme

    def resolve_redirects(self, resp, req, timeout=None, **adapter_kwargs):
        """Follow redirects starting from `resp`, the answer to `req`. Yields each new response."""
        hist = []
        url = self.get_redirect_target(resp)
        previous_fragment = urlparse(req.url).fragment
        while url:
            prepared_request = req.copy()

            hist.append(resp)
            resp.history = hist[1:]
            if len(resp.history) >= self.max_redirects:
                raise TooManyRedirects(f"Exceeded {self.max_redirects} redirects.", response=resp)
            resp.close()

            # A scheme-relative Location ("//host/path") keeps the current scheme.
            if url.startswith("//"):
                url = f"{urlparse(resp.url).scheme}:{url}"
            parsed = urlparse(url)
            if parsed.fragment == "" and previous_fragment:
                parsed = parsed._replace(fragment=previous_fragment)
            elif parsed.fragment:
                previous_fragment = parsed.fragment
            url = parsed.geturl()
            # A relative Location is resolved against the URL that answered.
            if not parsed.netloc:
                url = urljoin(resp.url, url)
            prepared_request.url = url

            self.rebuild_method(prepared_request, resp)

            # 307 and 308 resend the same request. Every other redirect drops the body.
            if resp.status_code not in (codes.temporary_redirect, codes.permanent_redirect):
                for header in ("Content-Length", "Content-Type", "Transfer-Encoding"):
                    prepared_request.headers.pop(header, None)
                prepared_request.body = None

            headers = prepared_request.headers
            headers.pop("Cookie", None)
            extract_cookies_to_jar(prepared_request._cookies, req, resp)
            merge_cookies(prepared_request._cookies, self.cookies)
            prepared_request.prepare_cookies(prepared_request._cookies)

            self.rebuild_auth(prepared_request, resp)

            # The previous send read a file-like body to its end.
            rewindable = prepared_request._body_position is not None and (
                "Content-Length" in headers or "Transfer-Encoding" in headers
            )
            if rewindable:
                rewind_body(prepared_request)

            req = prepared_request
            resp = self.get_adapter(req.url).send(req, timeout=timeout, **adapter_kwargs)
            extract_cookies_to_jar(self.cookies, prepared_request, resp)
            url = self.get_redirect_target(resp)
            yield resp

    def rebuild_auth(self, prepared_request, response):
        """Drop credentials that should not follow the request to its new location."""
        headers = prepared_request.headers
        if "Authorization" in headers and self.should_strip_auth(response.request.url, prepared_request.url):
            del headers["Authorization"]

    def rebuild_method(self, prepared_request, response):
        """Change the method where the redirect status says so (RFC 9110 section 15.4)."""
        method = prepared_request.method
        if response.status_code == codes.see_other and method != "HEAD":
            method = "GET"
        # Browsers turn 302 into GET too, whatever the spec says. Match them.
        if response.status_code == codes.found and method != "HEAD":
            method = "GET"
        # Browsers also turn a POST into a GET on a permanent redirect.
        if response.is_permanent_redirect and method == "POST":
            method = "GET"
        prepared_request.method = method


class Session(SessionRedirectMixin):
    """Keeps headers, auth, cookies and adapters across requests.

        >>> with Session() as s:
        ...     s.headers["X-Team"] = "payments"
        ...     r = s.get("http://127.0.0.1:8000/get", timeout=5)
    """

    def __init__(self):
        self.headers = default_headers()
        self.auth = None
        self.params = {}
        self.cookies = cookiejar_from_dict({})
        self.max_redirects = DEFAULT_REDIRECT_LIMIT
        self.adapters = {}
        self.mount("https://", HTTPAdapter())
        self.mount("http://", HTTPAdapter())

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def prepare_request(self, request):
        cookies = request.cookies or {}
        if not isinstance(cookies, CookieJar):
            cookies = cookiejar_from_dict(cookies)
        merged_cookies = merge_cookies(merge_cookies(CookieJar(), self.cookies), cookies)
        p = PreparedRequest()
        p.prepare(
            method=request.method.upper(),
            url=request.url,
            data=request.data,
            json=request.json,
            headers=merge_setting(request.headers, self.headers, dict_class=CaseInsensitiveDict),
            params=merge_setting(request.params, self.params),
            auth=merge_setting(request.auth, self.auth),
            cookies=merged_cookies,
        )
        return p

    def request(self, method, url, params=None, data=None, headers=None, cookies=None,
                auth=None, timeout=None, allow_redirects=True, json=None):
        req = Request(
            method=method.upper(),
            url=url,
            headers=headers,
            data=data or {},
            json=json,
            params=params or {},
            auth=auth,
            cookies=cookies,
        )
        prep = self.prepare_request(req)
        return self.send(prep, timeout=timeout, allow_redirects=allow_redirects)

    def get(self, url, **kwargs):
        kwargs.setdefault("allow_redirects", True)
        return self.request("GET", url, **kwargs)

    def options(self, url, **kwargs):
        kwargs.setdefault("allow_redirects", True)
        return self.request("OPTIONS", url, **kwargs)

    def head(self, url, **kwargs):
        kwargs.setdefault("allow_redirects", False)
        return self.request("HEAD", url, **kwargs)

    def post(self, url, data=None, json=None, **kwargs):
        return self.request("POST", url, data=data, json=json, **kwargs)

    def put(self, url, data=None, **kwargs):
        return self.request("PUT", url, data=data, **kwargs)

    def patch(self, url, data=None, **kwargs):
        return self.request("PATCH", url, data=data, **kwargs)

    def delete(self, url, **kwargs):
        return self.request("DELETE", url, **kwargs)

    def send(self, request, **kwargs):
        """Send a PreparedRequest and follow redirects unless allow_redirects=False."""
        allow_redirects = kwargs.pop("allow_redirects", True)
        if isinstance(request, Request):
            raise ValueError("You can only send PreparedRequests.")

        adapter = self.get_adapter(request.url)
        r = adapter.send(request, **kwargs)
        extract_cookies_to_jar(self.cookies, request, r)

        history = list(self.resolve_redirects(r, request, **kwargs)) if allow_redirects else []
        if history:
            history.insert(0, r)
            r = history.pop()
            r.history = history
        return r

    def get_adapter(self, url):
        for prefix, adapter in self.adapters.items():
            if url.lower().startswith(prefix.lower()):
                return adapter
        raise InvalidSchema(f"No connection adapters were found for {url!r}")

    def mount(self, prefix, adapter):
        """Register an adapter for a URL prefix. Longer prefixes win."""
        self.adapters[prefix] = adapter
        for key in [k for k in self.adapters if len(k) < len(prefix)]:
            self.adapters[key] = self.adapters.pop(key)

    def close(self):
        for adapter in self.adapters.values():
            adapter.close()


def session():
    return Session()
