"""Result types for the KYC validator."""
from dataclasses import dataclass, field


@dataclass(frozen=True)
class ValidationError:
    code: str      # e.g. MISSING_FIELD, see README.md for the full list
    field: str     # column name, or "*" for the whole row
    message: str


@dataclass
class RecordResult:
    line: int        # 1-based line in the file; the header is line 1
    record_id: str   # "" when the row could not be read
    errors: list = field(default_factory=list)

    @property
    def valid(self):
        return not self.errors
