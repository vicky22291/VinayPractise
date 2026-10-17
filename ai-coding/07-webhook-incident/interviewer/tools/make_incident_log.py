"""Regenerate candidate/incident/dispatcher.log by running the STARTER code against fake merchants.

    python3 ai-coding/07-webhook-incident/interviewer/tools/make_incident_log.py

The log is produced by the buggy starter itself, so every line matches the code.
Prints the facts the ticket, the answer key and test_p4 depend on.
"""
import json
import os
import random
import sys

KIT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(KIT, "candidate"))

from hooks.clock import FakeClock  # noqa: E402
from hooks.dispatcher import Dispatcher  # noqa: E402
from hooks.log import Logger  # noqa: E402
from hooks.models import Endpoint  # noqa: E402
from hooks.transport import Response, TransportTimeout  # noqa: E402
from sdk.webhooks import SignatureVerificationError, verify_signature  # noqa: E402

T0 = 1_791_968_400          # 2026-10-14T09:00:00Z
LAST_EVENT = T0 + 3 * 3600 + 30 * 60   # 12:30
END = T0 + 4 * 3600 + 30 * 60          # 13:30
NORTHWIND_DOWN = (T0 + 65 * 60, T0 + 185 * 60)   # 10:05 to 12:05
LUMEN_SLOW = (T0 + 100 * 60, T0 + 118 * 60)      # 10:40 to 10:58

MERCHANTS = [
    # account, name, endpoint, descriptor, mean minutes between events
    ("acct_1Lumen", "Lumen Books", "we_lumen01", "LUMEN BOOKS", 6),
    ("acct_1CafeOle", "Café Olé", "we_cafeole1", "CAFÉ OLÉ", 9),
    ("acct_1Muller", "Müller Fahrräder", "we_muller01", "MÜLLER FAHRRÄDER", 11),
    ("acct_1Northwind", "Northwind Supplies", "we_northw01", "NORTHWIND", 5),
    ("acct_1Acme", "Acme Tools", "we_acme0001", "ACME TOOLS", 7),
    ("acct_1Bluebird", "Bluebird Coffee", "we_bluebd01", "BLUEBIRD COFFEE", 8),
    ("acct_1Kestrel", "Kestrel Labs", "we_kestrl01", "KESTREL LABS", 10),
]
CUSTOMERS = ["Ana Silva", "Ben Okafor", "Chloe Martin", "Dev Patel", "Emma Brown",
             "Femi Adeyemi", "Grace Lee", "Hugo Laurent", "Ivy Chen", "Jack Wilson"]


def main():
    rng = random.Random(14)
    clock = FakeClock(T0)
    lines = []
    sink = lines

    class Transport:
        def __init__(self):
            self.handlers = {}

        def post(self, url, body, headers, timeout=30):
            return self.handlers[url](body, headers)

    transport = Transport()
    d = Dispatcher(transport, clock, log=Logger(clock, sink=sink))
    lumen_seen, lumen_shipped = set(), []

    def verifying(handler):
        def wrapped(body, headers):
            try:
                verify_signature(body, headers["Hooks-Signature"], "whsec_" + url_secret[headers["X-Url"]], clock.now())
            except SignatureVerificationError as e:
                return Response(400, str(e))
            return handler(body, headers)
        return wrapped

    url_secret = {}

    def ok(body, headers):
        return Response(200, "ok")

    def lumen(body, headers):
        payload = json.loads(body)
        if payload["id"] in lumen_seen:
            return Response(200, "duplicate")
        lumen_seen.add(payload["id"])
        if payload["type"] == "charge.succeeded":
            lumen_shipped.append((payload["data"]["object"]["id"], payload["id"]))
        if LUMEN_SLOW[0] <= clock.now() < LUMEN_SLOW[1]:
            clock.advance(30)
            raise TransportTimeout()
        return Response(200, "ok")

    def northwind(body, headers):
        if NORTHWIND_DOWN[0] <= clock.now() < NORTHWIND_DOWN[1]:
            return Response(503, "Service Unavailable")
        return Response(200, "ok")

    def kestrel(body, headers):
        return Response(500, "upstream error") if rng.random() < 0.05 else Response(200, "ok")

    behaviour = {"we_lumen01": lumen, "we_northw01": northwind, "we_kestrl01": kestrel}
    for account, name, ep_id, _, _ in MERCHANTS:
        url = f"https://hooks.{name.split()[0].lower().replace('é', 'e').replace('ü', 'u')}.example/stripe"
        url_secret[url] = ep_id
        d.endpoints.add(Endpoint(ep_id, account, url, "whsec_" + ep_id))
        inner = verifying(behaviour.get(ep_id, ok))
        transport.handlers[url] = (lambda inner, url: lambda body, headers: inner(body, {**headers, "X-Url": url}))(inner, url)

    schedule = []
    seq = {"ch": 0, "pi": 0, "po": 0, "re": 0}

    def nid(prefix):
        seq[prefix] += 1
        return f"{prefix}_3Q{seq[prefix]:05d}"

    for account, name, ep_id, descriptor, mean in MERCHANTS:
        t = T0 + rng.randint(0, 120)
        while t < LAST_EVENT:
            r = rng.random()
            customer = rng.choice(CUSTOMERS)
            if r < 0.6:
                data = {"id": nid("ch"), "amount": rng.randint(5, 400) * 100, "currency": "eur" if account in ("acct_1CafeOle", "acct_1Muller") else "usd",
                        "statement_descriptor": descriptor, "billing_details": {"name": customer}}
                typ = "charge.succeeded"
            elif r < 0.8:
                data = {"id": nid("pi"), "amount": rng.randint(5, 400) * 100, "status": "succeeded"}
                typ = "payment_intent.succeeded"
            elif r < 0.9:
                data = {"id": nid("po"), "amount": rng.randint(50, 900) * 100, "arrival_date": T0 + 86400}
                typ = "payout.paid"
            else:
                data = {"id": nid("re"), "charge": f"ch_3Q{rng.randint(1, 99):05d}", "amount": rng.randint(5, 50) * 100}
                typ = "charge.refunded"
            schedule.append((t, account, typ, data))
            t += max(30, int(rng.expovariate(1 / (mean * 60))))
    # One Bluebird customer with a non-ASCII name: the ticket does not mention this account.
    schedule.append((T0 + 132 * 60 + 17, "acct_1Bluebird", "charge.succeeded",
                     {"id": "ch_3Q09001", "amount": 1450, "currency": "usd", "statement_descriptor": "BLUEBIRD COFFEE",
                      "billing_details": {"name": "Zoë Adams"}}))
    schedule.sort(key=lambda s: (s[0], s[1]))

    lines.append("2026-10-14T09:00:00Z INFO worker.started service=hooks-dispatcher version=1.4.0 sha=8c1e2f0 region=us-west-2")
    for t, account, typ, data in schedule:
        d.run_until(t)
        clock.set(max(t, clock.now()))
        d.publish(account, typ, data)
        d.run_due()
    d.run_until(END)
    lines.append("2026-10-14T13:30:00Z INFO worker.stopped reason=log_export")

    with open(os.path.join(KIT, "candidate", "incident", "dispatcher.log"), "w") as f:
        f.write("\n".join(lines) + "\n")

    dup = {}
    for ch, wid in lumen_shipped:
        dup.setdefault(ch, []).append(wid)
    print("lines", len(lines), "events", len(schedule))
    print("lumen double-shipped:", {k: v for k, v in dup.items() if len(v) > 1})
    statuses = {}
    for dl in d.deliveries:
        statuses[dl.status] = statuses.get(dl.status, 0) + 1
    print("delivery statuses", statuses)


if __name__ == "__main__":
    main()
