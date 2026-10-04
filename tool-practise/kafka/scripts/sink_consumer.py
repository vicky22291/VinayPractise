"""Exercise 03: where you commit the offset decides what a crash costs you.

Reads `events` as group `sink`, writes each record into a SQLite "database",
and commits the Kafka offset by hand. `--crash-at N` kills the process
(os._exit, no cleanup) on the Nth record, at the point named by `--mode`:

  commit-first   commit offset, crash, then write   -> at-most-once: record lost
  write-first    write, crash, then commit offset   -> at-least-once: duplicate row
  idempotent     like write-first, but the table has UNIQUE(event_id) and
                 the insert is INSERT OR IGNORE     -> exactly-once effect

Run:  python sink_consumer.py --mode write-first --crash-at 5
Then: python sink_consumer.py --mode write-first        (restart, no crash)
Then: python sink_consumer.py --report
"""
import argparse
import os
import sqlite3

from confluent_kafka import Consumer

DB = "/tmp/sink.db"
TABLES = ("commit_first", "write_first", "idempotent")   # one table per --mode


def db():
    conn = sqlite3.connect(DB)
    for table in TABLES:
        key = " PRIMARY KEY" if table == "idempotent" else ""
        conn.execute(f"CREATE TABLE IF NOT EXISTS {table} (event_id TEXT{key}, payload TEXT)")
    return conn


def write(conn, mode, event_id, payload):
    if mode == "idempotent":
        conn.execute("INSERT OR IGNORE INTO idempotent VALUES (?, ?)", (event_id, payload))
    else:
        conn.execute(f"INSERT INTO {mode.replace('-', '_')} VALUES (?, ?)", (event_id, payload))
    conn.commit()


def report(conn):
    for table in TABLES:
        rows, distinct = conn.execute(
            f"SELECT COUNT(*), COUNT(DISTINCT event_id) FROM {table}").fetchone()
        print(f"{table:12} rows={rows} distinct={distinct} duplicates={rows - distinct}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["commit-first", "write-first", "idempotent"])
    ap.add_argument("--crash-at", type=int, default=0)
    ap.add_argument("--report", action="store_true")
    args = ap.parse_args()

    conn = db()
    if args.report:
        return report(conn)

    consumer = Consumer({
        "bootstrap.servers": "kafka:19092",
        "group.id": f"sink-{args.mode}",
        "enable.auto.commit": False,      # we decide when the offset moves
        "auto.offset.reset": "earliest",
        "session.timeout.ms": 6000,       # how long a crashed member keeps its partitions
    })
    assigned = []
    consumer.subscribe(["events"], on_assign=lambda c, parts: assigned.extend(parts))
    seen = 0
    try:
        while True:
            msg = consumer.poll(5.0)
            if msg is None:
                if not assigned:
                    print("waiting for the group to hand us partitions...")
                    continue
                print(f"idle 5 s, processed {seen} this run, stopping")
                break
            if msg.error():
                raise SystemExit(msg.error())
            seen += 1
            event_id, payload = msg.key().decode(), msg.value().decode()
            crash = seen == args.crash_at
            print(f"p{msg.partition()} o{msg.offset()} {event_id}")

            if args.mode == "commit-first":
                consumer.commit(message=msg, asynchronous=False)
                if crash:
                    print("CRASH after commit, before write", flush=True); os._exit(1)
                write(conn, args.mode, event_id, payload)
            else:
                write(conn, args.mode, event_id, payload)
                if crash:
                    print("CRASH after write, before commit", flush=True); os._exit(1)
                consumer.commit(message=msg, asynchronous=False)
    finally:
        consumer.close()
    report(conn)


if __name__ == "__main__":
    main()
