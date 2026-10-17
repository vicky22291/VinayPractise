# Stripe coding rounds on existing code: survey

As of 2026-10-17. Target: Stripe Staff (L4) onsite on 2026-10-19/20.
Purpose: evidence base for 10 practice kits (AI-allowed coding rounds on existing code).

Tag key: [prachub] PracHub question page (often a paywalled rewrite of the original). [report] first-hand candidate account (PracHub-hosted experience pages, Blind, LeetCode). [official] Stripe. [github] GitHub issue or PR. [guide] prep site, format only. [unverified] seen only in a search snippet, or the page would not open.

---

## 0. Method and source notes

- About 25 web searches (extended mode for round-specific queries) and about 35 page reads.
- Could not open (HTTP 403 or refused): 1point3acres problem list, LeetCode discuss posts 8372404 and 7595344, interviewdb AI guide, Inbyte SnakeYAML page.
- Excluded by source rules: Glassdoor (not on the allowed list), Medium, DEV Community, generic SEO blogs.
- No Stripe official page describes these rounds. Every description below is third-party. No [official] tags appear because none were found.
- PracHub shows a "listed" date and often an earlier interview date. Both are given when known.
- PracHub question pages often say the original formats "were not preserved." Treat their input formats as reconstructions.
- Coverage gap: almost nothing from 2024 surfaced. The oldest first-hand item is a Nov 2020 Blind thread.

---

## 1. Headline findings

1. **The 307 bug squash is real and current (Sep to Oct 2026).** An Oct 1, 2026 candidate report describes a Python `requests` round with three `test_HTTP_307_ALLOW_REDIRECT_POST_*` tests. A PracHub question page (Sep 24, 2026) gives the same task as a rewrite. [report][prachub]
2. **The closest real upstream bug is in urllib3, not requests.** urllib3 issue #5181 (opened Aug 26, 2026, still open) reports that a 307 or 308 redirect through `PoolManager` resends an empty body. Fix PR #5242 is open. The mechanism (body position not rewound) matches the Stripe task. [github]
3. **requests' own history.** requests #1084 (2013, closed) and #3079 (2016, closed) are the closest requests-side issues. No open requests issue found. [github]
4. **BikeMap is at least three different tasks.** (a) GeoJSON track to `staticmap` POST, save PNG (Oct 1 report). (b) tile-API fetch, plot points, nearest-landmark annotation (Inbyte prep page). (c) JSON coordinates to a "documented drawing API" (Sep 2026 report, Sep 11 PracHub page). [report][prachub][guide]
5. **The AI round has three tooling variants in 2026.** A built-in assistant in a Python environment (PracHub, Sep 24). Codex, "simulated" (Senior report, Sep 19). Opus (Oct 1 and Sep 24 reports). [prachub][report]
6. **A debugger that will not start is a reported failure.** A rejected candidate (Sep 24 report) lost about 15 minutes on a VS Code debugger that would not run. [report]
7. **Rule evaluator Part 4 is not public.** Two PracHub pages define three parts. The Aug 30 page says "more parts follow" but gives none. [prachub]

---

## 2. Q1. Bug Squash / Bug Bash

### 2.1 Reported libraries and repos

| Library or repo | What is reported | Tag | Verified? |
|---|---|---|---|
| Python `requests` (307 POST body replay) | Oct 1, 2026 report, Round 2. Sep 24 PracHub question page. Sep 24 debugger report calls it "the original Requests problem." | [report][prachub] | Report and question page agree on the task. |
| Mako (Python template engine) | 2-3 bugs. Directory path check missing. AST visitor missing for one node type. | [unverified] | Search summary of a guide and a candidate account. Not opened. |
| SnakeYAML (Java) | 60-minute "SnakeYAML Debug (Java)." Failing tests reportedly about "On" boolean parsing and CSV parsing. | [unverified] | Inbyte page refused. Linkjob account not opened. |
| Unnamed "open source library" | Nov 2020 Microsoft candidate: "fixing a bug in an open source library," backend. | [report] | Blind thread opened. |
| Unnamed "Bug-Hunt" repo | Sep 19, 2026 Senior+ report. Failing tests guided the work. Roughly 3 bugs. IDE with plugins. | [report] | Opened. Repo not named. |
| Unnamed repo, JavaScript | Blind thread titles about bug squash in JavaScript. One candidate said they were down-leveled. | [unverified] | Search snippet only. |

### 2.2 The requests 307 task

Question page, listed Sep 24, 2026, updated Oct 1. [prachub] https://prachub.com/interview-questions/fix-seekable-post-body-replay-after-a-307-redirect-in-python-requests

- Setup: "a checkout of the Python `requests` library." Starter code is the three tests plus the description. Library source is not included.
- Task: on a 307 response to a POST, resend the same method and "the same body bytes it sent the first time."
- Failing tests (names as given):
  - `test_HTTP_307_ALLOW_REDIRECT_POST_DATA` (string `'test'`). Already passes.
  - `test_HTTP_307_ALLOW_REDIRECT_POST_WITH_SEEKABLE` (`io.BytesIO(b'test')` at position 0). Hangs, then ReadTimeout.
  - `test_HTTP_307_ALLOW_REDIRECT_POST_WITH_PARTIAL_SEEKABLE` (`io.BytesIO(b'hello world')` after `read(5)`). Expected body `" world"` (leading space kept).
- Tests post to a local `httpbin` `redirect-to` endpoint with `timeout=5`. They assert final 200, a 307 in `history`, and the echoed `data`.
- Constraints quoted: "Fix the library, not the tests. All three tests must pass unchanged." 301, 302 and 303 "which drop the body, keep their current behavior." "Plain string bodies already work and must keep working."
- Time limit and AI policy: not stated.

Candidate account, Oct 1, 2026 (rejected). [report] https://prachub.com/interview-experiences/stripe-software-engineer-interview-experience-reconciliation-a-requests-307-bug-squash-bikemap-and-an-ai-exercise-no-offer
- Same three test names. Symptom: seekable stream hits ReadTimeout after redirect.
- Candidate's root cause: the first send reads the stream to the end. The resend starts from the moved cursor. The start position is never saved.
- Code named by the candidate: `prepare_body` and `copy` in `models.py`, `resolve_redirects` in `sessions.py`.
- Proposed fix: save the start position in `prepare_body`, copy it, and `seek()` back before resend.
- Time limit, AI policy, bug count: not given.

Debugger report, Sep 24, 2026 (rejected). [report] https://prachub.com/interview-experiences/stripe-software-engineer-interview-experience-ai-coding-reconciliation-and-a-debugger-that-would-not-run
- Round 3 was "the original Requests problem," practiced the day before.
- Tooling: local VS Code. Quote: "the debugger in my local VS Code just would not run properly no matter what."
- About 15 minutes lost. Root cause found from memory. A package conflict, which Gemini fixed about 5 minutes after the interview.
- Recruiter feedback: overall positive, but "debug and integration did not meet the bar."

### 2.3 Upstream history (for kit design)

| Item | Repo | Dates and state | What it says | Link |
|---|---|---|---|---|
| Issue #1084 "POST and PUT on 307 redirect will re-POST without body" | psf/requests | Opened Jan 4, 2013. Closed Mar 31, 2013. Version 1.0.4. | POST or PUT on a 307 re-sent without body. Cites RFC 2616 section 10.3.8. Closed by commit 88177ec. | [github] https://github.com/psf/requests/issues/1084 |
| Issue #3079 "requests gets stuck on post redirect where data is readable" | psf/requests | Opened Apr 7, 2016. Closed Nov 28, 2016. | File-like body (BytesIO) hangs on 307. Maintainer: requests "does not rewind the file pointer on redirect." Points to PRs #3082, #3535, #3655 as addressing it. Version not stated. | [github] https://github.com/psf/requests/issues/3079 |
| Issue #5181 "PoolManager redirect loop loses file-like body position: 307/308 resends an empty body (silent upload truncation)" | urllib3/urllib3 | Opened Aug 26, 2026. **Open.** urllib3 2.7.0, Python 3.14. | `PUT /start` with `BytesIO(b"PAYLOAD-DATA")`, 307 to `/echo`, via `urllib3.request()` with `Retry(total=3, redirect=3)`. Second hop sends `b''` and returns 200. A bare `HTTPConnectionPool` works. | [github] https://github.com/urllib3/urllib3/issues/5181 |
| PR #5242 "Rewind file-like request bodies across PoolManager redirects" | urllib3/urllib3 | **Open.** No merge date. | `PoolManager.urlopen` never passes `body_pos` to later hops. Fix records position and sets `kw["body_pos"]` only on redirect. Unrewindable 307/308 body raises `UnrewindableBodyError`. Tests named `test_307_redirect_resends_file_like_body` and similar. | [github] https://github.com/urllib3/urllib3/pull/5242 |
| PR #5161 "Drop request body framing state on 303 redirects" | urllib3/urllib3 | Linked from #5242. | 303 with file-like body fails because body position survives after body is set to None. | [github] https://github.com/urllib3/urllib3/pull/5161 |

Caveats:
- The Stripe test names and the requests `prepare_body` / `resolve_redirects` pointers do not appear on any upstream page I opened. [unverified]
- A third-party mirror (repos.supermodeltools.com) shows requests `_body_position` and `rewind_body()` in `utils.py`, called from `resolve_redirects`. Not checked against upstream. [unverified]
- Kit option: use the real requests source at a pinned tag with our own 307 tests, or use #5181 against urllib3 2.7.0. Both are real. Verify the requests tag first.

### 2.4 Format details

- Repo: unfamiliar, real open source project. Round starts from "a failing test, open issue, or broken behavior." [guide] https://prachub.com/resources/stripe-bug-squash-interview-guide-how-to-debug-an-unfamiliar-codebase (published Aug 3, 2026)
- Laptop and IDE vs HackerRank: reports show a local IDE or VS Code. The Sep 19 Senior report says the IDE and plugins were set up from a pre-interview email. No HackerRank mention for this round.
- Time: 45 to 60 minutes per guides. [guide] The Senior candidate said setup took about 30 minutes. [report]
- Bugs: "roughly three" (Sep 19 Senior report). A guide says "5-7 intentional bugs" in about 200 lines. [guide] https://www.techinterview.org/post/3233460268/stripe-interview-guide-2026-process-bug-bash-round-and-payment-systems/ (cites no sources)
- Failing tests: yes, in every detailed report. Bug-report-only format: mentioned by guides. [guide]
- AI allowed in 2026: unknown. The Aug 3 guide says "Do not assume so" and that policy "can change by team and interview format." [guide]
- Scoring (guide, no official rubric): orientation, reasoning tied to hypotheses, focused tool use, smallest root-cause fix, regression test. [guide]

### 2.5 Old item (history only)

- Nov 8, 2020 Blind thread. Bug squash was "fixing a bug in an open source library," backend. Integration was "coding and testing against part of the Stripe API." Commenter: "Not at all leetcode questions." Outcome: rejected. [report] https://www.teamblind.com/post/stripe-full-loop-what-to-expect-in-integration-and-bug-squash-rounds-havq2jl1

---

## 3. Q2. Integration round

### 3.1 BikeMap (four variants)

**A. GeoJSON track to staticmap (Oct 1, 2026 report).** [report] https://prachub.com/interview-experiences/stripe-software-engineer-interview-experience-reconciliation-a-requests-307-bug-squash-bikemap-and-an-ai-exercise-no-offer
- Input: `ride-simple.json`, GeoJSON track, 495 coordinates (494 segments).
- API: POST to a staticmap endpoint with JSON body. PNG response.
- Library: Python `requests`. `json=data` for body. `response.content` for image.
- Parts: (1) parse JSON, print first ten coordinates. (2) POST map parameters (center, width, height, zoom), save `bikemap2.png`. (3) add Start marker, Stripe marker, alternating blue and brown paths every ten segments, save `bikemap3.png`.
- Pitfalls the candidate noted: convert `[lon, lat]` to `{lat, lon}`. Do not mix `data=` with `json=`.

**B. Tile API and landmarks (Inbyte prep page, updated Jun 10, 2026).** [guide] https://www.inbyte.org/interview/stripe/bikemap-integration
- Medium. Tags: API Integration, HTTP, IO. About 60 minutes, five tasks, "most candidates finish about three."
- Starter repo with data and tasks, cloned and run locally, screen-shared.
- Tasks: (1) load track JSON, first ten coordinates, decide lat-first or lon-first, handle missing or malformed files. (2) authenticated tile-API request centered on the Stripe office, save binary image. (3) plot track points and connect them. (4) load landmark JSON, nearest track point per landmark, annotate both. (5) speed or timing, "rarely completed in time."
- Variant: server-side rendering API, JSON POST with `[longitude, latitude]`. Write binary in `'wb'` mode.
- Not stated: file formats, tile API name, libraries such as staticmap.

**C. Intern VO, Dec 2025 (published Sep 24, 2026).** [report] https://prachub.com/interview-experiences/stripe-intern-software-engineer-interview-experience-invoice-matching-screen-a-bikemap-integration-vo-and-an-sf-offer
- 45-minute programming exercise (scored 2 of 3), plus an email question (welcome emails, expiring events). Integration scored 3 of 5.
- Task: call the BikeMap API and parse responses. Docs were "long," and examples "didn't map directly onto the code they had to write."

**D. Map-drawing, Sep 2026 Senior+ report (no AI).** [report] https://prachub.com/interview-experiences/stripe-senior-software-engineer-interview-experience-bug-hunt-ai-pairing-and-map-drawing-rounds-no-system-design
- Inputs: JSON with x/y coordinates. Library: an open source drawing API "you can actually call," with a sample request body. Parts: connect points and draw the map.

**E. PracHub "Connect JSON Coordinates Through a Documented Drawing API" (Sep 11, 2026).** [prachub] https://prachub.com/interview-questions/connect-json-coordinates-through-a-documented-drawing-api
- API name, endpoint, auth, schema, coordinate system withheld. Docs and a sample body are provided in the environment.
- Parts: (1) clarifying questions. (2) JSON validation and connectivity. (3) request adapter from the contract. (4) error handling, retry and idempotency, verify the result.
- Follow-ups: disconnected paths; recovery when a response is lost after the API accepted the request.

Other map titles (listings only): "Plan bicycle routes on a city map" (Sep 6, 2025), "Generate a ride map image via POST API" (Jan 22, 2026), "Design ledger and bikemap integration" (Jul 29, 2025; Part A double-entry ledger, Part B Bikemap routing API behind an internal API). [prachub] https://prachub.com/companies/stripe?page=3 and https://prachub.com/questions/780?company=Stripe

### 3.2 Stripe API integration and starter repos

- 2020 Blind: "coding and testing against part of the Stripe API," info given by the recruiter in advance. [report]
- BikeMap intern: API docs given, no starter repo mentioned. [report]
- Inbyte: starter repo with data and tasks. [guide]
- Drawing API page: docs and sample body provided in the environment. [prachub]
- Other titles: "Implement JSON parsing and HTTP integration tasks" (Nov 26, 2025), "Propagate runtime ID across API requests" (Jan 22, 2026). [prachub] listings.
- "Prepare for Backend Parsing, API Integration, AI Coding, and Bug Fixing Rounds" (Jul 4, 2026, updated Jul 29, Onsite). Paywalled. Lists four round types in its title. Hints: "state assumptions first," "make edge cases explicit." [prachub] https://prachub.com/interview-questions/prepare-for-backend-parsing-api-integration-ai-coding-and-bug-fixing-rounds

---

## 4. Q3. AI Programming Exercise / AI pairing / AI phone screen

### 4.1 Transaction rule evaluator

Question page, listed Sep 24, 2026, updated Oct 1. [prachub] https://prachub.com/interview-questions/evaluate-ordered-accept-block-transaction-rules-with-and-or-and-parentheses
- Medium. Software Engineer, onsite. Python coding environment "with a built-in AI assistant, which the candidate is expected to use." HackerRank and Codex not named on this page.
- Signature: `evaluate(transaction: dict, rules: list[tuple[str, str]]) -> str`.
- Semantics: "Rules are applied in list order, and the first rule whose condition matches decides the result." "If no rule matches, the result is 'accept'." "Inputs are guaranteed to be well-formed."
- Example: transaction `{"merchant": "Corner Store", "country": "US"}`, rules `[('country == "FR"', "block"), ('"Corner Store" == merchant', "accept")]`, expected `"accept"`.
- Parts:
  1. String equality and rule order. Field and constant in either order. First match. Default accept.
  2. Boolean fields with AND and OR. Boundary: merchant name contains "and" or "or". Keep part 1 behavior.
  3. Parentheses and nesting. Precedence and short-circuit. Example: `(country == "US" OR country == "CA") AND merchant == "Corner Store"`.
- Edge cases listed on the page: missing field; AND/OR case; escaped quotes; bare Boolean vs `true`/`false`; AND/OR mixing without parentheses; operator words inside quoted names.
- Follow-ups listed: which rule decided (audit); precomputation at volume; NOT, inequality, numeric comparisons; validating malformed rules.

Candidate account, Oct 1, 2026, Round 4. [report] (same URL as 2.2). Tooling: "The AI built into the platform." Interviewer raised the Part 2 merchant-name edge case. No further interviewer behavior recorded.

Candidate account, Sep 24, 2026 (rule parser). [report] (same URL as 2.2 debugger report). "I used the Opus model." Found the AI's code hard to follow. Interviewer seemed "just nodding along," then said he trusted Opus to handle the requirements, and the candidate stopped writing.

Candidate account, Sep 19, 2026 (AI pairing, Senior+). [report] https://prachub.com/interview-experiences/stripe-senior-software-engineer-interview-experience-bug-hunt-ai-pairing-and-map-drawing-rounds-no-system-design
- "simulating using Codex to solve a coding problem." Inputs (recalled with uncertainty): string rules such as "a credit card name can't equal X," and transaction-record strings.
- Parts: use the agent to pass tests. Candidate also writes own tests. What the interviewer checked: not stated.

### 4.2 Later parts and related problems

- No part 4 of the rule evaluator found in any page opened.
- "Build a Transaction Rule Engine with AND/OR Chains and Nested Parentheses" (Aug 30, 2026, updated Oct 3, Technical Screen, Hard). [prachub] https://prachub.com/interview-questions/build-a-transaction-rule-engine-with-and-or-chains-and-nested-parentheses
  - Rules are ordered condition-and-action (`ACCEPT` or `DENY`). Grammar: field, `==`, `!=`, `>`, `>=`, `<`, `<=`, literal.
  - Part 1: single comparisons, separate parsing from evaluation. Part 2: AND/OR, strictly left to right, so `A OR B AND C` means `(A OR B) AND C`. Part 3: nested parentheses with a tree and clear errors.
  - "No Part 4 is defined. The prompt says more parts follow but that finishing all of them is not expected." Asks for modules so each new part is "a small, local change."
  - Open policies: first match vs any DENY, default, missing fields, malformed rules at load or eval time, uppercase AND/OR.
  - Follow-ups: NOT and IN (`country IN ("US", "CA")`), decision explanations, cross-transaction state (count per card in last hour), performance.
- "Evaluate Ordered Access-Control Rules" (Aug 13, 2026, Technical Screen, medium). [prachub] https://prachub.com/interview-questions/evaluate-ordered-access-control-rules
  - Overview: "parsing boolean access rules and enforcing first-match ACCEPT or BLOCK semantics with exact precedence and comparisons."
  - From a search summary, not fully visible: `evaluate_access_rules(rules, facts)` returns a string. Conditions are boolean identifiers or integer comparisons, joined by AND and OR, AND binds tighter. Returns NO_MATCH. Up to 10,000 rules and 10,000 facts. [unverified]

### 4.3 Tooling in 2026

- Built-in AI assistant in a Python environment: PracHub, Sep 24. [prachub]
- Opus model: Sep 24 and Oct 1 reports. [report]
- Codex agent, simulated: Sep 19 Senior+ report. [report]
- HackerRank: a guide (interviewdb, not opened) says HackerRank with about 30 minutes of coding. A Aug 2026 phone-screen candidate wondered whether the platform was HackerRank. [unverified][report]
- Cursor: not found. No Stripe-specific Codex report beyond the Sep 19 one.

### 4.4 Staff bar

- No opened report describes how the AI round is scored.
- Rule-engine page asks for modular design, each part a small local change. [prachub]
- Gap: no L4-specific feedback found.

### 4.5 Not found: July 2026 "AI pair coding round and a real GitHub bug bash"

- The title appears only as a link on the Jul 4 PracHub page. Search did not return the page. [unverified]

### 4.6 AI phone screen

- A Aug 2026 phone screen was not AI-based: a blank editor, then a CSV balances problem. [report] (see 5.4)
- The line "let the AI write all the code, your job is to review it" comes from the brief. No source found for it in this pass.

---

## 5. Q4. Reconciliation round

Three different reconciliation problems appear. Do not merge them without checking.

### 5.1 Payment to invoice, three parts (interview Sep 2025, published Aug 25, 2026)

Candidate report. [report] https://prachub.com/interview-experiences/stripe-software-engineer-interview-experience-a-three-part-payment-invoice-matching-problem
- Software Engineer, technical screen, medium. Level not stated.
- Input: invoices as strings `"invoice-id, amount, date"`. Payment as one string, e.g. `'payment-id, 300, paying for: invoice-id-1'`.
- Output: `"payment-id paid XXX amount for invoice XXX on date XXX"`.
- Part 1: match on invoice ID in the payment. Part 2: no ID, match by amount. Part 3: amount may be off by a forgiveness value. Output states how much was forgiven.
- Tie-break: earliest invoice. Tolerance: absolute or relative not stated.
- Priority (quoted): "if there's an exact invoice id, don't do amount matching;" and "if there's an exact amount match, don't bother with forgiveness."
- Candidate advice: integers over floats; substring slicing over regex. Interview focuses on object organization, not complexity.

Intern report (team screen Dec 8, 2025; published Sep 24, 2026). [report] https://prachub.com/interview-experiences/stripe-intern-software-engineer-interview-experience-invoice-matching-screen-a-bikemap-integration-vo-and-an-sf-offer
- Part 3 defines a date window: invoices dated between payment minus and plus forgiveness. Earliest wins. Author says details are secondhand, quoted from another candidate.
- Advice: "fast + accurate." Finishing all three was reportedly not required.

### 5.2 Memo ID, exact amount, tolerance (PracHub, Sep 24, 2026)

[prachub] https://prachub.com/interview-questions/match-payments-to-invoices-by-memo-id-exact-amount-then-amount-tolerance
- Payment: `"<payment_id>,<amount>,<memo>"`, e.g. `"p1,500,Paying off: INV-4"`. Invoice: `"<invoice_id>,<amount>,<due_date>"`, dates `YYYY-MM-DD`. Integer minor units.
- Tiers: (1) memo ID. (2) exact amount, earliest due date. (3) forgiveness range, earliest due date. Precedence not stated; the page asks the candidate to decide.
- Tolerance undefined: absolute or percent, inclusive, under or over payment.
- Edge cases listed: no match result, multiple IDs in memo, ID not in list, invoice matched twice, due-date ties, malformed memos, money representation.
- Strong-answer criteria: separate parsing from matching, explicit precedence, stable tie-break, defined no-match result, regression tests per part.

### 5.3 Other reconciliation titles (listings, not opened)

- "Design payment-to-invoice matcher with priorities" (Technical Screen, medium). [prachub] https://prachub.com/coding-questions/design-payment-to-invoice-matcher-with-priorities (from search result)
- "Reconcile Monthly Bank-Account Balances Across Two Datasets" (Aug 31, 2026, SQL or Python). [prachub] https://prachub.com/companies/stripe?page=2
- "Find the Latest Balance for a Bank Account" (Aug 31, 2026). [prachub] https://prachub.com/companies/stripe?page=2

### 5.4 Bank balances, blank editor (phone screen, published Sep 19, 2026)

[report] https://prachub.com/interview-experiences/stripe-software-engineer-interview-experience-a-new-coding-question-a-blank-editor-never-reached-part-3-and-didnt-pass-the-phone-screen
- Part 1: from a CSV of bank name, account name, start date, end date, balance, output the latest balance. Expected integer. Test revealed a string format not in the statement. Interviewer accepted integer.
- Part 2: second CSV. Tally by month. If an account's balance matches across both tables, "Match," else "Not Match."
- Part 3: not reached.
- Part 2 started in a blank editor. Interviewer suggested copying Part 1 and defining input freely. The copied file-path code failed immediately. A shadow (observer) was present and sometimes disagreed with the interviewer.

### 5.5 Payment and invoice, Oct 1 report

- Round 1 "Payment/Invoice Reconciliation": three parts as in 5.1. Follow-ups: "Any potential bugs?", "What if there is an exact match with forgiveness applied?", "how would we prioritize that?" [report] (same URL as 2.2)

---

## 6. Q5. Classic Stripe problems reframed as "extend this code"

Titles and dates from PracHub listings. Parts were opened only where noted.

| Problem (PracHub title) | Listed | Level | Known parts or edges | Tag |
|---|---|---|---|---|
| "Simulate sticky load balancer with shutdown" | Feb 12, 2026 | Intern, medium, OA | Not opened. Shutdown implies state change. | [prachub] p.2 |
| "Compute account balances with rejection and overdraft" | Dec 3, 2025 | SE, medium | Not opened. | [prachub] p.3 |
| "Generate Account Email Notifications" | Apr 14, 2026 | SE, medium | Not opened. | [prachub] p.2 |
| "Schedule Welcome and Expiration Emails from Subscription Records" | Dec 19, 2025 | Intern, medium | Matches the BikeMap VO email question. | [prachub] p.3 |
| "Validate transactions with risk rules and reporting" | Jan 17, 2026 | SE, medium | Not opened. Close to the rule evaluator. | [prachub] p.3 |
| "Implement Luhn-based card validation and inference" | Sep 6, 2025 | SE, medium | Not opened. | [prachub] p.3 |
| "Find linked user records by similarity" | Dec 8, 2025 | SE, medium | Not opened. | [prachub] p.3 |
| "Implement a CSV dataset join" | Jan 14, 2026 | SE, medium | Not opened. | [prachub] p.3 |
| "Parse and Format Arbitrarily Nested Tasks from CSV" | Aug 25, 2026 | SE, medium, paywalled | Not opened. | [prachub] p.1 |
| "Compute transaction fees from a CSV string" | Feb 24, 2026 | Data Engineer, hard | Not opened. | [prachub] p.1 |
| "Implement Validation and String Compression" | Mar 1, 2026 | Senior+, hard | Not opened. | [prachub] p.3 |
| "Debug Validation Error Aggregation" | May 14, 2026 | SE, hard, debugging | Not opened. | [prachub] p.1 |
| "Debug an Asynchronous SDK Race Condition with a Customer" | Jun 9, 2026 | SE, medium | Not opened. | [prachub] p.3 |
| "Assign Reviewers from Changed Files" | Apr 29, 2026 | "Software Engineer AI" label | Title only. Git-based by guess. | [prachub] p.1 |
| "Design a Feature Flag Service with Percentage Rollouts and Allow/Block Lists" | Aug 30, 2026 | Senior+, design | Design round. Repo already has a feature-flag HLD. | [prachub] p.1 |
| Validate CSV company records (missing fields, length, forbidden words, overlap) | not shown | Technical Screen, medium | Not opened. | [prachub] guide page |

Not found in any Stripe-tagged report: Accept-Language parsing, currency conversion, shipping cost, store hours, rate limiter, idempotency-key coding, log parsing.

Other:
- "Four-Part Split Tender Online Assessment" (new grad, Oct 2026). Preview only. [prachub] https://prachub.com/interview-experiences/stripe-new-grad-software-engineer-interview-experience-four-part-split-tender-online-assessment
- Stripe Senior, late Jul and late Aug 2026: "Implement a function that parses a CSV-formatted string containing business verification records" and validates each record. Fields not listed. [hellointerview] https://www.hellointerview.com/community/questions/kyc-csv-records/cmowcgza90mzo0eado496ovkw

---

## 7. Q6. Debugging, code review, and "read existing code" signals

- Debugger that would not run: Sep 24, 2026 report, VS Code, about 15 minutes lost. [report]
- Setup cost: about 30 minutes of the Sep 19 Senior+ round went to IDE setup. [report]
- Test-first advice from the Senior candidate: "you just had to look at the test cases and start from wherever the error was thrown." [report]
- Scoring method (guide): reproduce first, narrow hypotheses, smallest root-cause fix, regression test. [guide] https://prachub.com/resources/stripe-bug-squash-interview-guide-how-to-debug-an-unfamiliar-codebase
- Practice advice (guide): clone a repo with "bug"-labeled issues, reproduce, fix. [guide] (generic, not opened)
- Review of AI output: the Sep 24 candidate found the AI code hard to follow. The Sep 19 and Oct 1 AI rounds ask for review and test writing. [report]
- Debug titles (listings): "Debug Validation Error Aggregation," "Debug an Asynchronous SDK Race Condition." [prachub]

---

## 8. Q7. Ranking for Oct 2026 Staff prep (top 12)

Counts are sightings I could open, not Stripe totals. R = candidate report page. Q = PracHub question page. Lower bounds only.

| Rank | Problem family | R | Q | Why | Kit fit |
|---|---|---|---|---|---|
| 1 | Transaction rule evaluator (accept/block, AND/OR, parentheses, first match) | 3 | 3 | Most repeated Aug to Oct 2026. Three parts known. Built-in AI. | Strong. Two kits (parts and AI review). |
| 2 | Payment to invoice matching (ID, amount, forgiveness, tie-break) | 4 | 3 | Three-part structure, tie-break, priorities. Since Dec 2025. | Strong. |
| 3 | requests 307 seekable body replay (bug squash) | 2 | 1 | Dated Sep and Oct 2026. Named tests. Real urllib3 #5181 counterpart. | Strong. |
| 4 | BikeMap family (four variants) | 3 | 4 | Parsing, HTTP, image output. | Medium. Pick one variant. |
| 5 | Generic bug squash on unfamiliar OSS repo | 3 | 2 | Format stable 2020 to 2026. | Strong. Real issue with failing test. |
| 6 | CSV parse and validate (nested tasks, KYC, company records, joins) | 1 | 6 | Frequent. Edge-heavy. | Medium. |
| 7 | Bank balances and monthly reconciliation | 1 | 3 | Latest balance then two-table compare. | Medium. |
| 8 | AI-assisted coding, generic (Codex, Opus, built-in) | 2 | 3 | Interviewers reportedly trust the model. Review matters. | Strong for AI-review skill. |
| 9 | Assign reviewers from changed files | 0 | 1 | Title only. | Low evidence. |
| 10 | Classic reframes: overdraft balances, emails, sticky LB, Luhn | 0 | 6 | Classic simulations. Parts not opened. | Verify first. |
| 11 | Mako or SnakeYAML debug | 0 | 0 | Snippets and prep only. | Low confidence. |
| 12 | Design-only: ledger, feature flags, fraud, superhero dispatch | - | - | Design rounds. Not kit material. | HLD only. |

---

## 9. Sources table

| URL | Date | Level | Round | What it says | Tag |
|---|---|---|---|---|---|
| https://prachub.com/interview-questions/fix-seekable-post-body-replay-after-a-307-redirect-in-python-requests | Sep 24, 2026 (upd. Oct 1) | SE, onsite | Bug squash | Three requests tests; fix the library | prachub |
| https://prachub.com/interview-experiences/stripe-software-engineer-interview-experience-reconciliation-a-requests-307-bug-squash-bikemap-and-an-ai-exercise-no-offer | Oct 1, 2026 | SE, rejected | Reconciliation, bug squash, BikeMap, AI | Four rounds | report |
| https://prachub.com/interview-experiences/stripe-software-engineer-interview-experience-ai-coding-reconciliation-and-a-debugger-that-would-not-run | Sep 24, 2026 | SE, rejected | AI coding, integration, debug | Opus; VS Code debugger failed | report |
| https://prachub.com/interview-experiences/stripe-senior-software-engineer-interview-experience-bug-hunt-ai-pairing-and-map-drawing-rounds-no-system-design | Sep 19, 2026 | Senior+, rejected | Bug hunt, AI pairing, map | Codex simulated; IDE with plugins | report |
| https://prachub.com/interview-experiences/stripe-software-engineer-interview-experience-a-new-coding-question-a-blank-editor-never-reached-part-3-and-didnt-pass-the-phone-screen | Sep 19, 2026 (interview Aug) | SE, phone screen | Technical screen | Bank balance CSV; blank editor | report |
| https://prachub.com/interview-experiences/stripe-intern-software-engineer-interview-experience-invoice-matching-screen-a-bikemap-integration-vo-and-an-sf-offer | Sep 24, 2026 (interview Dec 2025) | Intern, offer | Team screen, VO | Invoice matching; BikeMap VO | report |
| https://prachub.com/interview-experiences/stripe-software-engineer-interview-experience-a-three-part-payment-invoice-matching-problem | Aug 25, 2026 (interview Sep 2025) | SE, screen | Technical screen | Invoice matching formats and priorities | report |
| https://prachub.com/interview-questions/evaluate-ordered-accept-block-transaction-rules-with-and-or-and-parentheses | Sep 24, 2026 (upd. Oct 1) | SE, onsite | AI programming | Rule evaluator, three parts | prachub |
| https://prachub.com/interview-questions/build-a-transaction-rule-engine-with-and-or-chains-and-nested-parentheses | Aug 30, 2026 (upd. Oct 3) | SE, screen | AI-assisted | Rule engine; no Part 4 | prachub |
| https://prachub.com/interview-questions/evaluate-ordered-access-control-rules | Aug 13, 2026 (upd. Sep 2) | SE, screen | Coding | Access rules; preview only | prachub |
| https://prachub.com/interview-questions/match-payments-to-invoices-by-memo-id-exact-amount-then-amount-tolerance | Sep 24, 2026 | SE, onsite | Fundamentals | Memo, amount, tolerance | prachub |
| https://prachub.com/interview-questions/connect-json-coordinates-through-a-documented-drawing-api | Sep 11, 2026 (upd. Sep 19) | SE, onsite | Integration | Drawing API from docs | prachub |
| https://prachub.com/questions/780?company=Stripe | Jul 29, 2025 (upd. Sep 4, 2026) | SE, onsite, hard | System design | Ledger plus Bikemap | prachub |
| https://prachub.com/interview-questions/prepare-for-backend-parsing-api-integration-ai-coding-and-bug-fixing-rounds | Jul 4, 2026 (upd. Jul 29) | SE, onsite | Multi | Four round types; paywalled | prachub |
| https://prachub.com/resources/stripe-bug-squash-interview-guide-how-to-debug-an-unfamiliar-codebase | Aug 3, 2026 | Guide | Bug squash | Scoring; no repos named | guide |
| https://prachub.com/interview-guide/stripe-software-engineer-interview-guide | Mar 17, 2026 (page upd. Oct 9) | Guide | All | 43 reports cited; round list | guide |
| https://prachub.com/companies/stripe | 2026 listing | - | - | Question list | prachub |
| https://prachub.com/companies/stripe?page=2 | 2026 listing | - | - | 20 titles and dates | prachub |
| https://prachub.com/companies/stripe?page=3 | 2026 listing | - | - | 20 titles and dates | prachub |
| https://prachub.com/interview-experiences/stripe-new-grad-software-engineer-interview-experience-four-part-split-tender-online-assessment | Oct 2026 | New grad | OA | Preview only | prachub |
| https://www.inbyte.org/interview/stripe/bikemap-integration | Upd. Jun 10, 2026 | - | Onsite coding | BikeMap tasks and variant | guide |
| https://www.techinterview.org/post/3233460268/stripe-interview-guide-2026-process-bug-bash-round-and-payment-systems/ | Apr 16, 2026 (upd. Oct 16) | - | Bug bash | "5-7 intentional bugs"; no sources | guide |
| https://www.teamblind.com/post/stripe-full-loop-what-to-expect-in-integration-and-bug-squash-rounds-havq2jl1 | Nov 8, 2020 | SWE, 6 yrs | Integration, bug squash | Old; OSS library bug | report |
| https://www.hellointerview.com/community/questions/kyc-csv-records/cmowcgza90mzo0eado496ovkw | Late Jul and Aug 2026 | Senior | Coding | CSV verification records | hellointerview |
| https://github.com/psf/requests/issues/1084 | Opened Jan 4, 2013; closed Mar 31, 2013 | requests 1.0.4 | - | POST on 307 resent without body | github |
| https://github.com/psf/requests/issues/3079 | Opened Apr 7, 2016; closed Nov 28, 2016 | Not stated | - | File body hangs on 307 | github |
| https://github.com/urllib3/urllib3/issues/5181 | Opened Aug 26, 2026; open | urllib3 2.7.0 | - | PoolManager loses body position | github |
| https://github.com/urllib3/urllib3/pull/5242 | Open | - | - | Fix for #5181 | github |
| https://github.com/urllib3/urllib3/pull/5161 | Linked from #5242 | - | - | 303 path body position | github |

---

## 10. Not found and could not open

### Could not open
- https://www.1point3acres.com/interview/problems/company/stripe (403). 234 Stripe problems. Would settle counts.
- https://leetcode.com/discuss/post/8372404/ (403). Backend engineer 2026 report.
- https://leetcode.com/discuss/post/7595344/ (403). "Stripe Onsite Interview (Hopeful pass)."
- https://www.interviewdb.io/guides/stripe-ai-programming-exercise (403). Claims HackerRank and about 30 minutes.
- https://www.inbyte.org/interview/stripe/snakeyaml-debug (refused). SnakeYAML round.
- https://www.coditioning.com/blog/804/stripe-swe-bug-squash-interview (not opened). Mako claim source.
- https://www.linkjob.ai/interview-questions/stripe-interview-questions/ (not opened). SnakeYAML claim source.
- Teamblind bug squash threads with Python and JavaScript titles (not opened; titles only).
- Glassdoor "Bug squash given this open source code base..." (excluded; not an allowed source).

### Not found
- The July 2026 "AI pair coding round and a real GitHub bug bash" PracHub page.
- Any Stripe official statement on these rounds.
- Any 2024 Stripe report on these rounds.
- An upstream requests issue with the PracHub test names, or a requests fix tied to `_body_position`.
- A verified Mako or SnakeYAML report.
- JGit in any Stripe report. The only JGit mention is a guide.
- Part 4 of the rule evaluator.
- A scoring rubric or L4 feedback for the AI round.
- A time limit for the 307 bug squash.
- Whether AI is allowed in the bug squash in 2026.
- Original input formats for invoice matching and BikeMap (PracHub says they were not preserved).

### Unverified claims
1. Mako round with directory check and AST visitor bugs. [unverified] Search summary only.
2. SnakeYAML round with "On" and CSV failing tests. [unverified] Snippet only.
3. Access-control grammar and limits. [unverified] Search summary of a paywalled page.
4. requests `_body_position` and `rewind_body()`. [unverified] Third-party mirror.
5. AI not permitted in integration round. [unverified] Guide summary.
6. Under 10% of candidates solve the Python version. [unverified] Blind snippet.
7. "Assign Reviewers from Changed Files" with JGit. [unverified] Title only.

---

## 11. Spot-check (2026-10-17, by the main session)

Pages re-opened with WebFetch. Every claim the kits rely on matched.

| Claim | Result | Source re-opened |
|---|---|---|
| 307 task: three test names, `" world"` expected body, "Fix the library, not the tests", 301/302/303 keep dropping the body | Confirmed. No time limit or AI policy on the page | prachub question page, Sep 24, 2026 |
| Fix is "record and restore the position from before the first send, not to always `seek(0)`"; files `models.py` (`prepare_body`, `copy`) and `sessions.py` (`resolve_redirects`) | Confirmed, quoted | Oct 1, 2026 report |
| BikeMap: `ride-simple.json`, first ten coordinates, `bikemap2.png`, blue then brown path every ten segments | Confirmed | Oct 1, 2026 report |
| Invoice formats `p1,500,Paying off: INV-4` and `INV-4,500,2024-04-01`, three tiers, earliest due date tie-break, precedence left to the candidate | Confirmed. Page "Last updated: Oct 1, 2026" | prachub question page |
| interviewing.io: "AI use in Stripe interviews is strictly prohibited"; bug bash is "a generic version of a real Stripe bug" | Confirmed. The page shows no date, so it may predate the 2026 AI round | interviewing.io/stripe-interview-questions |
