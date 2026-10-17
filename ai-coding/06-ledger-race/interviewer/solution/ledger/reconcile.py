"""Finance's nightly check: balances must agree with the journal."""
from dataclasses import dataclass

from ledger.journal import BANK, EXTERNAL, PENDING


@dataclass(frozen=True)
class Report:
    ok: bool
    problems: list


def reconcile(ledger):
    problems = []
    if not ledger.journal.is_balanced():
        problems.append("journal rows do not sum to zero")
    for account_id in ledger.accounts.ids():
        account = ledger.accounts.get(account_id)
        balance, net = account.balance, ledger.journal.net(account_id)
        if balance != net:
            problems.append(f"{account_id}: balance {balance} but journal says {net}")
        if balance < -account.overdraft_limit:
            problems.append(f"{account_id}: balance {balance} is past its overdraft limit")
    deposited = -ledger.journal.net(EXTERNAL)
    left = ledger.journal.net(PENDING) + ledger.journal.net(BANK)
    if ledger.total() + left != deposited:
        problems.append(f"total balance {ledger.total()} plus {left} paid out but {deposited} was deposited")
    return Report(not problems, problems)
