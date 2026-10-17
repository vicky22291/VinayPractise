## Part 5: production scale and safe reruns

The nightly job now sees about 100,000 open invoices and 1,000,000 payments, in
several batch files a night. The bank sometimes resends a file, and our
scheduler sometimes retries a batch that already finished.

Add `recon.matcher.Reconciler`:

```python
r = Reconciler(invoices, tolerance=0)     # invoice lines, as before
lines = r.run(batch_id, payments)         # payment lines, as before
```

1. State carries across runs. An invoice closed in one batch stays closed for
   later batches.
2. Running the same `batch_id` again returns exactly the same lines as the
   first time and changes nothing. The same `batch_id` with a different payment
   list raises `ValueError`.
3. A payment ID that was already applied, in this batch or any earlier one, is
   not applied again. Its line repeats the line it got the first time.
4. `reconcile(payments, invoices, tolerance)` returns the same lines as one
   `run` on a fresh `Reconciler`.
5. It must be fast: 100,000 invoices against 1,000,000 payments in well under a
   minute on a laptop.

Before you code it, tell the interviewer where the time goes today.
