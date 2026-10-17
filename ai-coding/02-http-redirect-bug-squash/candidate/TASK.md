# minireq: interview task

`minireq` is the HTTP client our internal services use. Its API and layout
follow `requests`. You have not seen this code before. Read it, run the tests,
and talk the interviewer through what you find. The interviewer adds tickets
as you close each one.

```
python3 -m unittest                          # whole suite, a few seconds
python3 -m unittest tests.test_redirects -v
```

## Part 1: POST bodies lost on 307 redirects

Two tests in `tests/test_redirects.py` fail:

- `test_HTTP_307_ALLOW_REDIRECT_POST_WITH_SEEKABLE`
- `test_HTTP_307_ALLOW_REDIRECT_POST_WITH_PARTIAL_SEEKABLE`

A 307 (Temporary Redirect) means: repeat the request at the new location with
the same method and the same body bytes it sent the first time.
`test_HTTP_307_ALLOW_REDIRECT_POST_DATA` sends a plain string and already
passes. The two failing tests send a file-like body. They hang after the
redirect and fail with a read timeout. The partial test reads 5 bytes of the
stream before posting, so the body that should arrive is `" world"`, leading
space included.

Rules:

- Fix the library, not the tests. All three tests must pass unchanged.
- Redirects with status 301, 302 and 303, which drop the body, keep their
  current behavior.
- Plain string bodies already work and must keep working.
