## Part 3: fix BILL-212 for new invoices only

Proration must use the real number of days in the month. A segment of `d` paid
days in a month of `n` days costs `seat price x seats x d / n`, rounded half
up to the cent, and its line reads `"<plan name> x <seats> (<d> of <n> days)"`.

The fix applies to billing periods that start on or after **2026-11-01**.
Every earlier period keeps the 30-day calculation exactly, so regenerating an
invoice that was already issued reproduces it to the cent. `generate_invoice`
keeps its signature: the switch is the period's start date.

Before you code it: how do you roll this out safely, and what do you tell
finance?
