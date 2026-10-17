"""Errors raised by the invoicing service."""


class ProcessorError(Exception):
    """The processor rejected or failed a request."""


class CardDeclined(ProcessorError):
    """The card was declined. Not retryable: the same card will decline again."""
