"""Client for the payment processor's charges API."""
import logging
from dataclasses import dataclass

from invoicing.errors import CardDeclined, ProcessorError

log = logging.getLogger(__name__)

MAX_ATTEMPTS = 3


@dataclass(frozen=True)
class ChargeResult:
    id: str
    amount: int
    currency: str


class ProcessorClient:
    def __init__(self, transport):
        self.transport = transport

    def charge(self, amount, currency, card, invoice_id):
        """Create one charge. Retries timeouts so a slow processor does not fail the billing run."""
        body = {
            "amount": amount,
            "currency": currency,
            "card_number": card.number,
            "exp_month": card.exp_month,
            "exp_year": card.exp_year,
            "metadata": {"invoice_id": invoice_id},
        }
        log.info("charging card %s for %s %s (invoice %s)", card.number, amount, currency, invoice_id)
        last_error = None
        for attempt in range(1, MAX_ATTEMPTS + 1):
            try:
                return self._parse(self.transport.post("/v1/charges", body))
            except Exception as e:  # timeouts are transient, try again
                last_error = e
                log.warning("charge attempt %d of %d failed: %s", attempt, MAX_ATTEMPTS, e)
        raise ProcessorError(f"charge failed after {MAX_ATTEMPTS} attempts") from last_error

    @staticmethod
    def _parse(resp):
        if resp["status"] == 402:
            raise CardDeclined(resp["error"]["code"])
        if resp["status"] != 200:
            raise ProcessorError(f"processor returned {resp['status']}")
        return ChargeResult(resp["id"], resp["amount"], resp["currency"])
