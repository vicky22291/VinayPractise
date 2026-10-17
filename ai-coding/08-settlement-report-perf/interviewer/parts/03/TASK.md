## Part 3: incremental runs

Late rows keep arriving after midnight, and finance reruns the report every 10
minutes until 06:00. `payouts/store.py` was updated again: `Store` now gives
every row a sequence number when it is written, and
`Store.iter_transactions_since(day, after_seq)` streams `(seq, txn)` pairs with
`seq > after_seq`, in sequence order.

Add `payouts.report.run_incremental(store, day, checkpoint)`, returning
`(report, new_checkpoint)`:

- `checkpoint` is `None` on the first run, otherwise what the previous run
  returned. It must survive `json.dumps` then `json.loads`. Never mutate the one
  you are given.
- `report` equals `build_report(store, day)` for the store as it is now.
- A run reads only rows written since the checkpoint, in at most 10 round trips.
- A rerun with no new rows returns the same report and an equal checkpoint.
- A checkpoint from another day raises `ValueError`.
