"""Module-level helpers. Each call opens a fresh Session and closes it afterwards."""
from minireq import sessions


def request(method, url, **kwargs):
    """Send a request. Takes the same keyword arguments as Session.request.

        >>> minireq.request("GET", "http://127.0.0.1:8000/get", timeout=5)
        <Response [200]>
    """
    with sessions.Session() as session:
        return session.request(method=method, url=url, **kwargs)


def get(url, params=None, **kwargs):
    return request("get", url, params=params, **kwargs)


def options(url, **kwargs):
    return request("options", url, **kwargs)


def head(url, **kwargs):
    kwargs.setdefault("allow_redirects", False)
    return request("head", url, **kwargs)


def post(url, data=None, json=None, **kwargs):
    return request("post", url, data=data, json=json, **kwargs)


def put(url, data=None, **kwargs):
    return request("put", url, data=data, **kwargs)


def patch(url, data=None, **kwargs):
    return request("patch", url, data=data, **kwargs)


def delete(url, **kwargs):
    return request("delete", url, **kwargs)
