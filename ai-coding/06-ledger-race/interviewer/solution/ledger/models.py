"""Results returned to callers. Business outcomes are results, not exceptions."""
from dataclasses import dataclass


@dataclass(frozen=True)
class TransferResult:
    status: str               # succeeded | rejected (| failed, from run_batch only)
    transfer_id: str | None   # set only when succeeded
    reason: str | None        # insufficient_funds | unknown_account | invalid_amount | same_account


@dataclass(frozen=True)
class PayoutResult:
    status: str               # paid | pending | declined | rejected
    reference: str | None     # the bank's reference when paid
