"""Blast radius of INC-2291, computed only from the dispatcher log.

    python3 incident/blast_radius.py incident/dispatcher.log
"""
import json
import re
import sys

LINE = re.compile(r"^(\S+) (\w+) (\S+)(.*)$")
FIELD = re.compile(r'(\w+)=("(?:[^"]*)"|\S+)')
SIGNATURE = "No signatures found matching"


def parse(path):
    with open(path, encoding="utf-8") as f:
        for raw in f:
            m = LINE.match(raw.rstrip("\n"))
            if m:
                ts, level, msg, rest = m.groups()
                fields = {k: v.strip('"') for k, v in FIELD.findall(rest)}
                yield ts, msg, fields


def summarize(log_path):
    sig, abandoned, timed_out, retried = {}, {}, {}, {}
    for _, msg, f in parse(log_path):
        key = (f.get("event"), f.get("endpoint"))
        if msg == "delivery.failed" and SIGNATURE in f.get("resp", ""):
            sig[key] = f["account"]
        elif msg == "delivery.gave_up":
            abandoned[key] = f["account"]
        elif msg == "delivery.timeout":
            timed_out[key] = f["account"]
        elif msg == "delivery.sent" and key in timed_out:
            retried[key] = f["account"]

    def count(d):
        return {"deliveries": len(d), "accounts": len(set(d.values()))}

    return {"signature_rejected": count(sig), "abandoned": count(abandoned),
            "retried_after_timeout": count(retried)}


if __name__ == "__main__":
    print(json.dumps(summarize(sys.argv[1] if len(sys.argv) > 1 else "incident/dispatcher.log"), indent=2))
