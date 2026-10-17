## Part 4: the 2 GB nightly file

Ops will now validate one 2 GB file every night. `validate_csv` takes the
whole text in memory.

Before you code, tell the interviewer what happens to memory for the Part 3
checks on 50 million records, and what you would do about it.

1. Add `kyc.validate_stream(lines, rules=None)`. `lines` is any iterable of
   lines, as you get from iterating an open file (each line keeps its `\n` or
   `\r\n`). It returns an iterator of `RecordResult` in file order, produced
   while reading: never more than a few lines ahead of the result it returns.
   Line numbers stay correct.
2. Memory may grow with the number of distinct tax ids and owner emails, but
   not otherwise with the size of the file.
3. Add `kyc.summarize(results, top=5)`. It consumes any iterable of
   `RecordResult` without keeping them, and returns an object with `total`,
   `valid`, `invalid` and `top_codes`: a list of `(code, count)` tuples for the
   most frequent error codes, by count descending then code ascending, at most
   `top` entries.
4. `validate_csv` keeps working.
