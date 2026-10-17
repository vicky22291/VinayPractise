import os
import tempfile
import unittest

from incident.blast_radius import summarize

EXPECTED = {
    "signature_rejected": {"deliveries": 20, "accounts": 3},
    "abandoned": {"deliveries": 30, "accounts": 4},
    "retried_after_timeout": {"deliveries": 5, "accounts": 1},
}

SMALL = """\
2026-10-14T09:00:00Z INFO worker.started service=hooks-dispatcher version=1.4.0
2026-10-14T09:00:01Z WARN delivery.failed event=evt_1 delivery=whd_1 endpoint=we_a account=acct_a type=x attempt=1 http=400 resp="No signatures found matching the expected signature for payload"
2026-10-14T09:02:01Z WARN delivery.failed event=evt_1 delivery=whd_2 endpoint=we_a account=acct_a type=x attempt=2 http=400 resp="No signatures found matching the expected signature for payload"
2026-10-14T09:03:00Z WARN delivery.failed event=evt_2 delivery=whd_3 endpoint=we_b account=acct_b type=x attempt=1 http=503 resp="Service Unavailable"
2026-10-14T09:04:00Z WARN delivery.timeout event=evt_3 delivery=whd_4 endpoint=we_c account=acct_c type=x attempt=1 timeout_ms=30000
2026-10-14T09:06:00Z INFO delivery.sent event=evt_3 delivery=whd_5 endpoint=we_c account=acct_c type=x attempt=2 http=200 bytes=10
2026-10-14T09:07:00Z WARN delivery.timeout event=evt_4 delivery=whd_6 endpoint=we_c account=acct_c type=x attempt=1 timeout_ms=30000
2026-10-14T09:08:00Z INFO delivery.sent event=evt_5 delivery=whd_7 endpoint=we_c account=acct_c type=x attempt=1 http=200 bytes=10
2026-10-14T10:00:00Z ERROR delivery.gave_up event=evt_2 endpoint=we_b account=acct_b attempts=6 age_s=3720
2026-10-14T10:01:00Z ERROR delivery.gave_up event=evt_1 endpoint=we_a account=acct_a attempts=6 age_s=3720
"""


class Part4(unittest.TestCase):
    def test_incident_log(self):
        self.assertEqual(summarize(os.path.join("incident", "dispatcher.log")), EXPECTED)

    def test_small_log(self):
        with tempfile.NamedTemporaryFile("w", suffix=".log", delete=False, encoding="utf-8") as f:
            f.write(SMALL)
        try:
            self.assertEqual(summarize(f.name), {
                "signature_rejected": {"deliveries": 1, "accounts": 1},
                "abandoned": {"deliveries": 2, "accounts": 2},
                "retried_after_timeout": {"deliveries": 1, "accounts": 1},
            })
        finally:
            os.unlink(f.name)


if __name__ == "__main__":
    unittest.main()
