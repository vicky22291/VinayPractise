"""Columns and reference data for the business verification file."""

COLUMNS = [
    "record_id",
    "business_name",
    "tax_id",
    "country",
    "incorporation_date",
    "owner_name",
    "owner_email",
]

# Countries we can onboard today.
COUNTRIES = {"US", "GB", "CA", "IE", "DE", "FR", "NL", "SG", "AU", "JP"}

# What ops sees next to each code in the dashboard. Keep in sync with README.md.
ERROR_CODES = {
    "MISSING_FIELD": "A required value is empty.",
    "WRONG_COLUMN_COUNT": "The row has a different number of fields than the header.",
    "INVALID_TAX_ID": "The tax id is not in the expected format.",
    "INVALID_COUNTRY": "We cannot onboard businesses from this country yet.",
    "INVALID_DATE": "The incorporation date is not a real YYYY-MM-DD date.",
    "INVALID_EMAIL": "The owner email is not a valid address.",
}

# How urgent each code is for the ops queue. Unknown codes sort last.
SEVERITY = {
    "WRONG_COLUMN_COUNT": 0,
    "MISSING_FIELD": 1,
    "INVALID_TAX_ID": 1,
    "INVALID_COUNTRY": 2,
    "INVALID_DATE": 2,
    "INVALID_EMAIL": 3,
}
