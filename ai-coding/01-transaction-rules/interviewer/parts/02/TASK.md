## Part 2: booleans, AND, OR

Rules can now combine comparisons:

```
merchant_name == "Evil Corp" OR card_country == "NG"
is_3ds == false AND card_country == "BR"
```

- Boolean fields are compared with the bare words `true` and `false`.
  `is_3ds == "true"` compares against the string `"true"`, so it never matches a
  boolean field.
- `AND` and `OR` are keywords in any letter case (`and`, `Or`). Inside quotes
  they are plain text: `merchant_name == "Bread and Butter"` is one
  comparison.
- There is no precedence yet. Evaluate strictly left to right:
  `a OR b AND c` means `(a OR b) AND c`.

Keep every earlier test passing.
