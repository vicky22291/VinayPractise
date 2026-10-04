"""Exercise 07: Kafka transactions, seen from a consumer.

  python txn_producer.py commit  ledger-1   # 3 records, then commit
  python txn_producer.py abort   ledger-2   # 3 records, then abort
  python txn_producer.py hang    ledger-3   # 3 records, then exit without
                                            # commit or abort (a "hanging"
                                            # transaction: blocks read_committed)

The second argument is a prefix for the record values so you can tell the
runs apart in the consumer output. The transactional.id stays the same
across runs, so each new run fences the previous producer (epoch + 1).
"""
import os
import sys

from confluent_kafka import Producer


def main():
    action, prefix = sys.argv[1], sys.argv[2]
    p = Producer({
        "bootstrap.servers": "kafka:19092",
        "transactional.id": "ledger-relay",   # stable id = zombie fencing
        "transaction.timeout.ms": 60000,       # a hang blocks readers this long
    })
    p.init_transactions()   # bumps the epoch, aborts whatever the last owner left open
    p.begin_transaction()
    for i in range(3):
        p.produce("ledger", key=f"acct-{i}", value=f"{prefix}-{i}")
    p.flush()               # records are in the log now, but not committed
    print(f"{action}: 3 records written to the log, transaction still open", flush=True)

    if action == "commit":
        p.commit_transaction()
        print("committed")
    elif action == "abort":
        p.abort_transaction()
        print("aborted")
    elif action == "hang":
        print("exiting without commit or abort", flush=True)
        os._exit(0)         # no cleanup, like a crashed relay


if __name__ == "__main__":
    main()
