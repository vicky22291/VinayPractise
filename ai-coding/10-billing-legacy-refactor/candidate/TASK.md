# billing: interview task

You own `billing`, which turns subscriptions into monthly invoices. It is the
oldest code in the company and it has no tests. Finance reconciles against its
output, and any invoice it has already issued must regenerate to the same cent.

The interviewer adds more parts as you finish each one. Nobody is expected to
finish every part.

## Part 1: pin today's behaviour

Product wants changes here soon. Before anyone touches the code, write
characterization tests that pin what
`billing.invoice.generate_invoice(subscription, events, as_of)` does today.
Pin current behaviour exactly, including anything that looks wrong. That
includes BILL-212 below, which you must **not** fix yet.

> **BILL-212** (from the PM): customers who change plan or seats mid-month are
> undercharged in February and overcharged in 31-day months. Finance confirmed
> it. We will fix it in a later change.

- Put your tests under `tests/`. They must pass on the current code with
  `python3 -m unittest discover -s tests -t .`
- The interviewer checks your tests by making small changes to
  `billing/invoice.py` and seeing whether your suite notices. Aim to catch at
  least 3 out of every 4.
- `fixtures/subscriptions.json` holds real-shaped subscriptions.
  `python3 cli.py fixtures/subscriptions.json 2026-02-15` prints their
  February invoices.

Do not change anything under `billing/` in this part. You have about 15 minutes.
