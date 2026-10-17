# minireq

The HTTP client our internal services use. The API and module layout follow
[requests](https://github.com/psf/requests), so most of what you know about
requests applies here.

```python
import minireq

r = minireq.post("http://127.0.0.1:8000/post", json={"amount": 1200}, timeout=5)
r.raise_for_status()
print(r.json())

with minireq.Session() as s:
    s.auth = ("svc-billing", "secret")
    s.get("http://127.0.0.1:8000/get", timeout=5)
```

## Layout

```
minireq/
  api.py           get(), post(), ...: one-shot helpers around a Session
  sessions.py      Session, redirect handling (resolve_redirects, rebuild_*)
  models.py        Request, PreparedRequest (prepare_*), Response
  adapters.py      HTTPAdapter: sends a PreparedRequest over http.client
  utils.py         super_len, header checks, encodings, body helpers
  cookies.py       CookieJar, per-host cookies
  auth.py          HTTPBasicAuth, HTTPBearerAuth
  structures.py    CaseInsensitiveDict
  status_codes.py  codes.ok, codes.temporary_redirect, ...
  exceptions.py    RequestException and subclasses
tests/
  httpbin.py       local httpbin-style server on 127.0.0.1, started per test class
  test_*.py        python3 -m unittest
```

Python 3.11+, standard library only.
