# ledger: interview task

`ledger` holds merchant balances for the payout system. Read the code and run
the tests before you change anything. The interviewer adds more parts as you
finish each one.

## Part 1: money appears and disappears

**PAY-311.** After last night's busy payout run, finance's reconciliation
failed: the sum of balances did not match the money deposited, and one merchant
ended below zero, which the ledger must never allow. Ops also had to restart
the payout job twice last week because it froze. `tests/test_stress.py` fails,
but not the same way every time.

Find the causes and fix them. Keep the public API: `Ledger.open_account`,
`deposit`, `transfer`, `balance`, `total`, the `journal` attribute, and
`workers.run_batch`.

These must hold under any amount of concurrency:

- Money is conserved: the sum of balances equals the money deposited.
- The journal balances: all rows sum to zero, and each account's rows sum to
  its balance.
- No balance goes below zero. A transfer that would do that raises
  `InsufficientFunds` and moves nothing.
- A transfer from an account to itself is invalid: it raises `InvalidTransfer`
  and moves nothing.
- The ledger never freezes, whatever order transfers arrive in.
- Transfers between unrelated accounts should not wait on each other.

Explain your fix for the freeze to the interviewer: why can it no longer
happen?
