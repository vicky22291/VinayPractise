"""Finance's nightly check: balances must agree with the journal."""
from dataclasses import dataclass

from ledger.journal import EXTERNAL


@dataclass(frozen=True)
class Report:
    ok: bool
    problems: list


def reconcile(ledger):
    problems = []
    if not ledger.journal.is_balanced():
        problems.append("journal rows do not sum to zero")
    for account_id in ledger.accounts.ids():
        balance, net = ledger.balance(account_id), ledger.journal.net(account_id)
        if balance != net:
            problems.append(f"{account_id}: balance {balance} but journal says {net}")
        if balance < 0:
            problems.append(f"{account_id}: negative balance {balance}")
    deposited = -ledger.journal.net(EXTERNAL)
    if ledger.total() != deposited:
        problems.append(f"total balance {ledger.total()} but {deposited} was deposited")
    return Report(not problems, problems)
