"""Run a batch of transfer requests on a thread pool.

The nightly payout job builds one request per connected account and runs them
here. A request is a dict with src, dst, amount and an optional idempotency_key.
"""
import logging
from concurrent.futures import ThreadPoolExecutor

log = logging.getLogger(__name__)


def run_batch(ledger, requests, workers=8):
    """Run every request. Returns the transfer ids in request order (None if it failed)."""

    def one(request):
        try:
            return ledger.transfer(
                request["src"], request["dst"], request["amount"], request.get("idempotency_key")
            )
        except Exception as e:
            log.warning("transfer failed: %s: %r", request, e)
            return None

    with ThreadPoolExecutor(max_workers=workers) as pool:
        return list(pool.map(one, requests))
