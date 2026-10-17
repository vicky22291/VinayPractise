## Part 2: credentials sent to another host

Security ticket **SEC-212**, no test attached:

> Our billing client calls `https://api.internal.example/v1/export` with an
> `Authorization: Bearer ...` header. The endpoint now answers 302 with a
> pre-signed download URL on `https://files.partner-cdn.example/...`. The
> partner's access logs show our bearer token.

`minireq` must not send the `Authorization` header to a different host when it
follows a redirect. A redirect within the same host keeps it. So does an
`http` to `https` upgrade on the same host with default ports.

1. Write a test that reproduces the leak. The test server listens on
   `127.0.0.1`, so `localhost` on the same port is a different host name for
   the same server.
2. Fix it. The decision lives in `Session.should_strip_auth(old_url, new_url)`,
   which returns `True` when the header must be removed.
