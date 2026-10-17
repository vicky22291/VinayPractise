# kyc

Validates the business verification CSV that onboarding receives from partner
banks. Each row is one business. Ops reads the report and contacts the business
about every error.

```
kyc/csv_reader.py   read_rows(text) -> (header, rows)
kyc/validators.py   validate_record(record) -> [ValidationError]
kyc/errors.py       ErrorCollector
kyc/pipeline.py     validate_csv(text) -> [RecordResult]
kyc/report.py       format_report(results) -> str
cli.py              python3 cli.py data/merchants.csv
tests/              python3 -m unittest
```

## File format

Columns (any order): `record_id, business_name, tax_id, country,
incorporation_date, owner_name, owner_email`.

## Error codes

| Code | Field | Meaning |
|---|---|---|
| `MISSING_FIELD` | the column | Required value is empty |
| `WRONG_COLUMN_COUNT` | `*` | Row has a different number of fields than the header |
| `INVALID_TAX_ID` | `tax_id` | 5 to 20 letters, digits or `-` |
| `INVALID_COUNTRY` | `country` | Not a country we onboard (`kyc/schema.py`) |
| `INVALID_DATE` | `incorporation_date` | Not a real date in `YYYY-MM-DD` form |
| `INVALID_EMAIL` | `owner_email` | Not `name@domain.tld` |

Python 3.11+, standard library only.
