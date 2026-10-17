"""Client for the payment processor's charges API."""
import logging
import uuid
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
        """Create one charge. Timeouts are retried under one Idempotency-Key, so a retry never charges twice."""
        body = {
            "amount": amount,
            "currency": currency,
            "card_number": card.number,
            "exp_month": card.exp_month,
            "exp_year": card.exp_year,
            "metadata": {"invoice_id": invoice_id},
        }
        headers = {"Idempotency-Key": f"charge-{invoice_id}-{uuid.uuid4().hex}"}
        log.info("charging card ending %s for %s %s (invoice %s)", card.last4, amount, currency, invoice_id)
        for attempt in range(1, MAX_ATTEMPTS + 1):
            try:
                resp = self.transport.post("/v1/charges", body, headers)
            except TimeoutError as e:
                log.warning("charge attempt %d of %d timed out (invoice %s)", attempt, MAX_ATTEMPTS, invoice_id)
                if attempt == MAX_ATTEMPTS:
                    raise ProcessorError(f"charge timed out {MAX_ATTEMPTS} times") from e
                continue
            return self._parse(resp)

    @staticmethod
    def _parse(resp):
        if resp["status"] == 402:
            raise CardDeclined(resp["error"]["code"])
        if resp["status"] != 200:
            raise ProcessorError(f"processor returned {resp['status']}")
        return ChargeResult(resp["id"], resp["amount"], resp["currency"])
