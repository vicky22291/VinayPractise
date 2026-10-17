## Part 4: metered usage

The catalog now has a metered plan, `api` ("API Pro"): a seat price plus a
price per API call. `fixtures/catalog.json` has been updated.

1. `Plan` gets `usage_unit_amount: int = 0`, in cents per unit.
2. New event kind `"usage"`, with `quantity` = units used on that date.
3. Usage inside the billing period is priced at the `usage_unit_amount` of the
   plan in force on the event's date. Add one line per plan that has a usage
   price: `"<plan name> usage (<units> units)"`, amount = units x
   `usage_unit_amount`. Usage lines come after the seat lines and before the
   coupon line, in the order of each plan's first usage event.
4. Usage is not billed before the subscription starts, during the trial, or
   after a cancel. A plan without a usage price gets no usage line.
5. Usage events never split seat segments. A full month with usage still has
   a full-price seat line.
6. Coupons and tax apply to the subtotal including usage.

Keep Parts 1 to 3 green.
