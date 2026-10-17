## Part 4: incident note

1. Add `incident/blast_radius.py` with `summarize(log_path) -> dict`. Compute
   everything from the log alone:

   ```
   {"signature_rejected":    {"deliveries": int, "accounts": int},
    "abandoned":             {"deliveries": int, "accounts": int},
    "retried_after_timeout": {"deliveries": int, "accounts": int}}
   ```

   A delivery is one (event, endpoint) pair.
   - `signature_rejected`: deliveries with at least one `delivery.failed` line
     whose response says no signature matched.
   - `abandoned`: deliveries with a `delivery.gave_up` line.
   - `retried_after_timeout`: deliveries with a `delivery.timeout` line followed
     later by a `delivery.sent` line. The merchant may have processed these
     more than once.

2. Write `INCIDENT.md` (one page): a timeline from the log, the blast radius,
   the metric that should have paged someone and at what threshold, and your
   rollback decision for 1.4.0 with the reason.
