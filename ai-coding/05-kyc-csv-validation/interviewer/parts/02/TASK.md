## Part 2: new compliance rules

Compliance sent three new rules, and more will follow every quarter. Today
every check lives in one function. First make adding a rule a one-class change,
then add the three rules.

**Rule API (the hidden tests use it)**
- A rule is any object with `check(record) -> list[ValidationError]`, where
  `record` is a dict of lower-case column name to trimmed value.
- `kyc.rules.DEFAULT_RULES` is the list of rules `validate_csv` runs.
- `validate_csv(text, rules=None)`: `None` means `DEFAULT_RULES`. A list
  replaces them. `WRONG_COLUMN_COUNT` is not a rule and is always checked.
- The Part 1 checks become rules in `DEFAULT_RULES`.

**New rules**
1. `FORBIDDEN_WORD` on `business_name`: the name contains one of the words
   `bank`, `test`, `fake` as a whole word, in any letter case. `Blood Bank Cafe`
   fails. `Bankside Cafe` and `Contest Supplies` pass.
2. Per-country tax ids, still code `INVALID_TAX_ID`:
   - `US`: two digits, `-`, seven digits (`12-3456789`)
   - `GB`: exactly 8 upper-case letters or digits
   - `CA`: exactly 9 digits
   - any other country: the Part 1 rule
3. `TOO_LONG`: `business_name` over 80 characters, or `owner_name` over 60
   characters. The field is the column that is too long.
