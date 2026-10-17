"""Run a batch of transfer requests on a thread pool.

The nightly payout job builds one request per connected account and runs them
here. A request is a dict with src, dst, amount and an optional idempotency_key.
"""
import logging
from concurrent.futures import ThreadPoolExecutor

from ledger.models import TransferResult

log = logging.getLogger(__name__)


def run_batch(ledger, requests, workers=8):
    """Run every request. Returns one TransferResult per request, in request order."""

    def one(request):
        try:
            return ledger.transfer(
                request["src"], request["dst"], request["amount"], request.get("idempotency_key")
            )
        except Exception as e:
            log.exception("transfer failed: %s", request)
            return TransferResult("failed", None, f"error: {e!r}")

    with ThreadPoolExecutor(max_workers=workers) as pool:
        return list(pool.map(one, requests))
