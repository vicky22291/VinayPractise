## Part 3: checks across records

Fraud found the same business onboarding several times in one file, under
different record ids. Add two checks that look across records:

1. `DUPLICATE_TAX_ID` (field `tax_id`): the record has the same `country` and
   `tax_id` as an earlier record in the file. Compare tax ids
   case-insensitively. The first occurrence is not flagged. The message names
   the line of the first occurrence, for example `same tax_id as line 2`.
2. `SHARED_OWNER` (field `owner_email`): the record's `owner_email` (compared
   case-insensitively) appeared earlier in the file on a record with a
   different tax id. The message names that earlier line.

Rows with `WRONG_COLUMN_COUNT`, and empty values, take no part in these checks.

Both checks are part of `DEFAULT_RULES`, so `validate_csv(text)` reports them,
and a caller who passes `rules=[...]` decides whether they run.
