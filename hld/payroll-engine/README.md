# Payroll run for ~1M small businesses

> One-line answer: a payroll run is a **deadline-driven batch** whose deadline is the bank's ACH (automated clearing house) cut-off, not the pay date. Approving a run freezes an immutable **pay run snapshot** (inputs, tax table version, engine version), and a deterministic gross-to-net calculation turns it into paychecks, so a crashed worker just recomputes the same numbers. Every money movement (employer debit, each employee's net pay, each tax deposit) becomes a row in a **payment instruction ledger** with an id derived from (pay run, payee, purpose) before any file is built. At each ACH window a **file builder** claims eligible instructions under a lease, writes a NACHA file, records it in a **file registry** (hash, entry count, total) and uploads it. An upload with an unknown outcome is resolved by asking the bank, never by re-sending blindly, because a duplicate payroll file is the most expensive bug in the system. The employer's debit can be returned up to 2 banking days after it settles, which is after employees are paid, so per-company payroll limits and funding checks are part of the design, and NACHA reversals are the last-resort repair, not the plan.

Tier 3, problem #29 in [`hld/README.md`](../README.md). Two framings in one folder: the user's Intuit Principal / Staff practice list (2026-10, "payroll run for ~1M small businesses", the batch and money movement) and Rippling's "multi-tenant payroll engine" (exact money math, pay run as a saga, tenant isolation, audit trail). Related: [`../payments-ledger/`](../payments-ledger/), [`../expense-rules-engine/`](../expense-rules-engine/) (reimbursements paid through payroll), [`../employee-ops-bundle/`](../employee-ops-bundle/). Sources: [`research/`](research/).

## Problem statement (as asked)

Payroll run for ~1M small businesses. Crux: deadline-driven batch with exactly-once money movement and safe retries.

Follow-ups that always come: the employer's debit comes back NSF (non-sufficient funds) after employees were paid; the file upload timed out; an approval at 4:59:59 PM; a calc worker dies halfway through a 500-employee company; a wrong paycheck that has to be pulled back; a tax engine change that must not break 10 M paychecks.

## Functional requirements

Core:
- **Schedule and approve.** Each company has pay schedules (weekly, biweekly, semimonthly, monthly) and a holiday calendar. The admin approves the run (or auto-payroll does) before the cut-off for the chosen speed (2-day, next-day, same-day direct deposit, or 4-day "debit first" for new companies; the riskiest tier funds by wire before the run).
- **Calculate.** Gross to net per employee: earnings, pre-tax deductions, federal, state and local taxes, garnishments, employer taxes. Deterministic and versioned.
- **Move money exactly once.** Debit the employer, credit each employee by direct deposit, and deposit tax liabilities with the agencies on their schedule. Each instruction leaves the building once.
- **Retry and repair safely.** Any step can be retried. Returns (R01, R02, R03 and others) and mistakes are handled by reversals, re-issues and adjustments that keep the books balanced.

Below the line: tax form filing (941, W-2) except as the deposit schedule that drives deadlines, time tracking, benefits administration, paper checks, international payroll, building the tax engine's rule content.

## Non-functional requirements

| Dimension | Target |
|---|---|
| Scale | ~1 M companies, ~10 employees on average, ~10 M employees. ~33 M pay runs/year, ~330 M paychecks/year [estimate]. Weekly peak: ~3 M paychecks approved inside the last 2 hours before the 2-day cut-off on Wednesday afternoon, more around the 15th and month end. Design peak ~6 M paychecks at one cut-off (a month-end Friday pay date) |
| Deadline | A run approved before its cut-off is in the right ACH file, every time. Miss rate 0 for approved runs. Calc for the peak batch done in under 30 min |
| Exactly-once | No instruction sent twice. No NACHA file uploaded twice. Retries are always safe |
| Correctness | Every paycheck reproducible from its snapshot to the cent. Ledger balances: employer debit = net pay + taxes + fees, per run |
| Availability | Approval and calc 99.95% in the 4 hours before each cut-off. Late is worse than slow |
| Risk | Credit exposure (debits that can still return) capped per company. New companies have lower limits or prefunding |
| Audit | Every run, snapshot, file and instruction kept 7 years |

## What interviewers probe (the ladder)

1. The employer's ACH debit comes back R01 after employees were paid (the window closes about one banking day after Friday's credits). Who eats it, and how do you stop it happening at scale?
2. The NACHA file upload to the bank timed out. Did the bank get it? What do you do in the next 10 minutes?
3. A customer approves at 4:59:59 PM PT and your cut-off is 5 PM. Which file is it in? What about a federal holiday on Monday?
4. A calc worker dies after computing 300 of 500 employees. What happens on retry?
5. One employee was paid $10,000 instead of $1,000. What can you do and by when?
6. A state changes its withholding table mid-quarter. Which runs use which table, and can you prove it?
7. How do you test a tax engine change before it computes 10 M paychecks?
8. One tenant has 50k employees. Does anything change?

## Files

| File | What it is |
|---|---|
| [`solution.md`](solution.md) | Full HLD in flow-first form: one incremental diagram, one walkthrough per FR, deep dives that mutate the design, then nitty-gritty |
| [`diagrams.md`](diagrams.md) | The D1 to D12 diagram set |
| [`edge-cases.md`](edge-cases.md) | Every "what if" with a 60-second answer and a confidence box |
| [`deep-dives/deadlines-and-ach-windows.md`](deep-dives/deadlines-and-ach-windows.md) | Cut-offs, ACH windows, banking-day calendars, the batch plan, what happens when we are late |
| [`deep-dives/exactly-once-money-movement.md`](deep-dives/exactly-once-money-movement.md) | Instruction ids, the instruction ledger, the file builder lease, the file registry, unknown upload outcomes |
| [`deep-dives/gross-to-net-calc-and-tax-tables.md`](deep-dives/gross-to-net-calc-and-tax-tables.md) | Deterministic calc, versioned tax tables, exact money math, testing an engine change against history |
| [`deep-dives/funding-risk-and-returns.md`](deep-dives/funding-risk-and-returns.md) | Employer debit risk, return codes and windows, payroll limits, reversals and re-issues |
| [`deep-dives/multi-tenant-batch-and-retries.md`](deep-dives/multi-tenant-batch-and-retries.md) | Partitioning the batch, the pay run saga, retries, big tenants, tenant isolation |
| [`research/`](research/) | Raw web research notes with source links. Input to the files above, not study material |
| `payroll-engine.excalidraw` | My drawing. Missing until I draw it |
