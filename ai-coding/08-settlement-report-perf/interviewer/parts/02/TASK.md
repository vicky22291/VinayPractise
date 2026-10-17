## Part 2: days that do not fit in memory

Black Friday days have 10 times the rows. `payouts/store.py` was just updated.
It is still the database, so still do not change it:

- `Store.list_transactions(day)` now refuses days over 100,000 rows
  (`ResultTooLarge`).
- `Store.iter_transactions(day)` streams one day through a server-side cursor
  in one round trip.
- `ArchiveStore` is the replica used for the biggest days. It has the merchant
  and FX tables and `iter_transactions(day)`, once per day. No random access.

`build_report(store, day)` must work on both stores, produce the same bytes as
before, read each transaction once, and keep memory flat as the day grows: a
300,000-row day must stay under 16 MiB of peak Python allocations.
