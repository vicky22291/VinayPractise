"""Errors raised by the ledger."""


class LedgerError(Exception):
    """Base class for ledger errors."""


class UnknownAccount(LedgerError):
    pass


class InsufficientFunds(LedgerError):
    pass


class InvalidTransfer(LedgerError):
    """Bad amount, or the transfer makes no sense."""
