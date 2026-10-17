## Part 4: silent upload truncation

Some callers stream bodies from a generator or a pipe. Those cannot be
rewound. Today, when such a request gets a 307 or 308, `minireq` resends an
empty or partial body, and the server often accepts it: the upload is silently
truncated. urllib3 has an open issue for the same failure (#5181, Aug 2026).

**Before you code,** tell the interviewer who could break when this starts
raising an error, and how you would roll the change out.

Then:

- Add `UnrewindableBodyError` to `minireq/exceptions.py`, a subclass of
  `RequestException`.
- On a 307 or 308, if the body is a stream that cannot be put back where it
  started (a generator or iterator, a file object whose `tell()` failed, or
  one whose `seek()` fails), raise `UnrewindableBodyError` and send nothing to
  the new location.
- Bytes, strings, form data and JSON bodies are unaffected. 301, 302 and 303
  drop the body, so they never raise.
