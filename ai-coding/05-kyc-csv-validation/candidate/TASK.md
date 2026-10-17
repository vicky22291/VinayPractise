# kyc: interview task

You just joined the onboarding team. `kyc` validates the business verification
CSV that partner banks send us. Ops says the nightly run is red and the report
is wrong. Read the code and run the tests before you change anything. The
interviewer adds more parts as you finish each one.

## Part 1: make the tests pass

`python3 -m unittest` has failing tests. Make them pass by fixing the library,
not the tests. Then make sure the file format below is fully supported, and
add tests for whatever you fix.

**API (keep it):** `kyc.validate_csv(text: str) -> list[RecordResult]`, one
result per data row, in file order. `RecordResult` has `line`, `record_id`,
`errors` and `valid`. Each error is a `ValidationError(code, field, message)`.
Error codes are listed in `README.md`.

**File format**
- UTF-8 text. It may start with a byte order mark.
- Lines end in `\n` or `\r\n`. A trailing newline is not a record. Blank lines
  are skipped.
- The first line is the header. Header names are case-insensitive, may have
  spaces around them, and can come in any order. Extra columns are ignored. A
  missing required column raises `HeaderError`.
- Standard CSV quoting: a field in double quotes may contain commas, and `""`
  inside quotes is a literal `"`. Fields never contain line breaks.
- Values are trimmed of surrounding spaces.
- `line` is the line number in the file, counting the header as line 1 and
  counting skipped blank lines too.
- Every error on a record is reported, not just the first of each kind.
- Dates are real calendar dates written exactly as `YYYY-MM-DD`.
