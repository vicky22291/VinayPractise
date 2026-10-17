# payouts: interview task

`payouts` builds the daily settlement report that finance uses to pay
merchants. Read the code, run the tests, then run
`python3 -m payouts.cli --merchants 2000 --transactions 200000 > /dev/null`
to see what one day costs. The interviewer adds more parts as you go.

## Part 1: make it fast

A 200,000-transaction day makes about 1.26 million database round trips. At
about 1.5 ms each that is over 30 minutes in production, and the payout batch
waits for it.

Make `payouts.report.build_report(store, day)` fast:

- The output must stay **byte-for-byte identical**, for every input. Finance
  diffs it against the ledger.
- The number of round trips (`store.total_calls()`) must not grow with the
  number of transactions or merchants.
- `payouts/store.py` stands for the database. Do not change it. Its bulk
  methods are fair game.

Before you change anything, tell the interviewer how you will prove the output
did not change.
