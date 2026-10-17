"""When to try a failed delivery again.

Merchants are promised retries for up to three days, with exponential backoff.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class RetryPolicy:
    base: int = 60              # seconds; doubled on every failed attempt
    cap: int = 6 * 60 * 60      # never wait more than 6 hours between attempts
    max_age: int = 3 * 24 * 60  # give up three days after the event was created

    def next_attempt_at(self, created_at, attempts, now):
        """When to try again after `attempts` failed attempts, or None to give up."""
        delay = min(self.base * 2 ** attempts, self.cap)
        at = now + delay
        if at - created_at > self.max_age:
            return None
        return at
