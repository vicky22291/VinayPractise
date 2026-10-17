# Brownfield coding rounds: evidence survey

Date: 2026-10-17. Target: Stripe Staff loop, 2026-10-19/20. Scope: existing-codebase rounds (fix, debug, extend, refactor, optimize, review), AI-allowed and AI-banned, across the industry.

## 0. How to read this survey

Tags on each claim:

- [official]: company engineering, careers or hiring page. Quote verified by my own fetch unless marked "excerpt".
- [report]: candidate report, news outlet quoting an internal document, or a PracHub / LeetCode / Glassdoor post.
- [guide]: prep-site guide (Hello Interview, interviewing.io, techinterview.org, Exponent, GreatFrontEnd). Used for format only.
- [github]: repository file that I read directly.
- [unverified]: I could not open the primary page, or only a search excerpt exists.

Method: 30+ searches and fetches. I used curl with a browser user agent for Hello Interview, interviewing.io and GitHub raw files. WebFetch for official pages. Several official pages (DoorDash, Coinbase, Canva's older post on LinkedIn-era policy) blocked or hid their text from my tools. Where I rely on a search excerpt, the claim says so.

Main finding: the public record is thin. Only Canva, Datadog and Anthropic have official pages on AI policy that I could read. DoorDash and Coinbase have official format posts that I could only see as search excerpts. Meta, Google, Shopify, LinkedIn and Stripe have no official grading rubric that I could open. Most task-type evidence is candidate-reported. Treat it as signal, not fact.

Plain-English point for the Stripe loop: Stripe's own public stance is "no AI" for its bug bash, per interviewing.io. Ask the recruiter before you assume AI is allowed.

## 1. Task-type taxonomy

Each type lists companies, a concrete example, a time box, and what graders reward. "Time box" is the reported or suggested length, with the source.

### 1.1 Fix failing tests in a multi-file repo

- Companies: Meta (phase 1 of the AI-enabled round, AI rules vary by interviewer) [guide]. Brex (some teams, 60-minute debugging round with failing unit tests) [guide]. Stripe debug-round variant (repo, failing test, 45 minutes) [guide].
- Meta example: "The codebase arrives with a bug. Your job is to find it and fix it." Typical bugs: "an int being cast to a double when the rest of the system expects an int", "off-by-one errors, or incorrect conditionals" [guide, https://www.hellointerview.com/blog/meta-ai-enabled-coding].
- Stripe-style example from a guide: "You clone a repo, run the test suite, and three tests come back red." [guide, https://www.techinterview.org/post/3233476091/debugging-interview-format/]
- Brex example: "a small codebase with failing unit tests and asked to identify root causes, fix the bugs, and walk through your reasoning" [guide, https://www.techprep.app/blog/brex-interview-process; 2026 guide, not verified on the page].
- Time box: Meta AI-enabled round about 60 minutes in three phases [guide]. Stripe bug bash 45 to 60 minutes [guide].
- Graders reward (Meta): "Meta cares more about your approach and reasoning than completion." Several candidates "who didn't finish phase 3 still received offers" [guide].
- Graders reward (Stripe bug bash, per guide): the interviewer watches "whether you change a single variable at a time and predict what will happen before you run anything" [guide].

### 1.2 Bug from an issue report or log, no failing test given

- Companies: Stripe (bug bash) [guide, https://interviewing.io/stripe-interview-questions]. Coinbase (official excerpt: "debugging issues") [official excerpt, https://www.coinbase.com/blog/interviewing-engineers-in-the-ai-era-lessons-from-a-year-of-rebuilding]. Amazon (PracHub listing: "Debug Watch List Movie Operations", Jun 12, 2026, "Find and fix bugs in a full-stack movie watch-list app") [report, https://prachub.com/ai-assisted]. Affirm (anonymous candidate review, Nov 2024, "debug existing code on parsing data") [report, review URL not verified].
- Stripe example, verified: "You'll be given a piece of code and will have to find the bug(s)." Stripe "usually picks a generic version of a real Stripe bug" [guide, https://interviewing.io/stripe-interview-questions]. Format: onsite, 1 hour, own IDE with screen-share or CoderPad.
- Coinbase example, from excerpt: candidates "debugging issues, reviewing code for correctness and performance, reasoning about rollback scenarios, all with AI tools available" [official excerpt].
- Time box: 45 to 60 minutes [guide].
- Graders reward (Stripe, guide): "Interviewers focus less on whether you fully fix the bug and more on how you approach the problem" (from a Stripe-guide summary on Exponent, [guide, https://www.tryexponent.com/guides/stripe-software-engineer-interview]; not verified on page).
- Graders reward (Coinbase, official excerpt): "Can they triage real issues? Can they catch subtle bugs that AI introduces? Do they understand what they're accepting when they accept an AI-generated change?" [official excerpt]

### 1.3 Extend a feature in staged parts

- Companies: DoorDash (official excerpt: 60-minute session building on a realistic project; example tasks "order dispatch", "menu composer", "support resolution" per a guide quoting the post) [official excerpt, https://careersatdoordash.com/blog/doordash-is-rebuilding-its-engineering-interviews-around-ai/]. Shopify (one problem that "starts simple and evolves") [guide, https://www.hellointerview.com/blog/shopify-ai-enabled-coding]. Rippling (build features incrementally against test cases) [guide, https://www.hellointerview.com/learn/ai-coding/overview/interview-formats]. Ramp (PracHub, May 25, 2026, "Implement and Defend an AI-Assisted Repository Change": "Add a feature to an unfamiliar repo with AI help and explain every change") [report, https://prachub.com/ai-assisted].
- DoorDash example: "replacing traditional coding rounds with a 60-minute, AI-assisted engineering working session. You join a realistic project, ramp up, and start contributing." [official excerpt]
- Shopify example: "Implement an LRU cache" or "move a robot around a grid", with follow-ups such as "now add support for multiple robots" [guide].
- Time box: DoorDash 60 minutes [official excerpt]. Shopify 75 to 90 minutes [guide].
- Graders reward (DoorDash, excerpt): five areas: "How you get oriented, how you use AI and verify outputs, how you debug, how you manage scope, and how you communicate tradeoffs." Excerpt also says "Finishing every task is less important than showing a tight loop and good judgment" [official excerpt].
- Graders reward (Shopify, guide): "Candidates who jumped straight into prompting without planning consistently received weaker signals than those who started with a requirements doc and a task breakdown" [guide].

### 1.4 Refactor for extensibility, then add a feature

- Companies: Rippling (OOD-style problems; "credit-card expense policy engine with configurable rules") [report, https://leetcode.com/discuss/post/8351482/ripplings-ai-powered-coding-round-what-i-sfms/; fetch blocked, search excerpt only]. Shopify (SOLID open/closed: "If someone says 'now add support for multiple robots,' your code should handle that without a major rewrite") [guide]. Canva (open-ended design, e.g. "a system for managing aircraft takeoffs and landings at a busy airport") [report via GreatFrontEnd, https://www.greatfrontend.com/interviews/company/canva/questions-guides].
- Rippling example (excerpt): interviewer evaluated "Extensible design, Ability to add new rules easily, Clean OOP principles, Optimal TC & SC" [report, excerpt].
- Time box: Rippling 60 minutes per one candidate; a Senior SWE candidate reported only 20 to 25 minutes [report, excerpt].
- Graders reward: extensibility of the seam, not new features. Shopify checks whether follow-ups land "without a major rewrite" [guide].

### 1.5 Performance optimization of slow existing code

- Companies: Meta (phase 3: "larger inputs that break your phase 2 solution", tiered test data files) [guide]. azizu06 practice repo (timed tests, "climb the ladder") [github]. Google code comprehension pilot ("read, debug, and optimize") [report].
- Meta example: "For the substring problem, one data file has many short words (where a trie excels) while another has fewer but much longer words (where a greedy approach is actually faster)." [guide]
- Time box: part of the Meta 60-minute round; azizu06 suggests 50 minutes for the whole session [github].
- Graders reward (azizu06 rubric, practice tool, not an employer): "Named the bottleneck in terms of N and M, asked for a list of options rather than the answer, picked one, and stated the new complexity before running the timed test." [github]
- Graders reward (Meta, guide): candidates who "recognized this and explained the tradeoff, even if they couldn't implement both solutions, scored well" [guide].

### 1.6 Concurrency or race-condition fix

- Companies: LinkedIn (follow-ups after the first solution: "concurrency, multithreading, synchronization") [guide, https://www.hellointerview.com/blog/linkedin-ai-enabled-coding]. Stripe bug bash does not name a race type; no report found for a Stripe race round. Coinbase and Canva do not name concurrency in the sources I read.
- LinkedIn example: "For cache problems, expect concurrency and multithreading follow-ups. How would you synchronize access? What race conditions could occur? How would you productionize this?" [guide]
- Time box: not reported. The concurrency piece is a follow-up after the coding part.
- Graders reward (LinkedIn, guide): "Can you reason about concurrency? Do you know what race conditions look like?" LinkedIn "reportedly uses a 4-point grading scale where a 3 is passing" [guide, unverified count].
- Evidence strength: weak. Only one guide reports a race-focused follow-up in an AI-enabled round.

### 1.7 Code review of a PR or of AI-generated code

- Companies: Coinbase (official excerpt: "catch subtle bugs that AI introduces") [official excerpt]. Shopify (reviewing AI output, "read the generated code line by line") [guide]. Meta (AI often misses edge cases; candidate reports the AI hides bugs when asked to "describe the codebase") [guide]. Coinbase PracHub task "Debug and Extend Cursor Queries" (Apr 2, 2026): "Validate and extend AI-generated query code, explaining your reasoning" [report, https://prachub.com/ai-assisted].
- Meta example, from a candidate report: "Another candidate described asking the AI to 'describe the codebase.' In his own environment, this immediately revealed all the bugs. In the interview environment, it described the code's functionality without mentioning any issues." [guide]
- Time box: not reported for pure review rounds.
- Graders reward (Coinbase excerpt): "Do they understand what they're accepting when they accept an AI-generated change?" [official excerpt]
- Graders reward (Shopify, guide): "How do you recognize and clean up imperfect output." Interviewer says AI can produce "pure garbage" [guide].

### 1.8 Write characterization tests for legacy code, then change it

- Companies: no direct report found. Closest: Shopify (interviewers ask "How would you design your unit test? What can be improved in the test file?") [guide]. Hello Interview's verification page advises agreeing test cases with the interviewer before implementation [guide, https://www.hellointerview.com/learn/ai-coding/fundamentals/verification-and-testing].
- Example: none in a public report. Practice variant: write tests that pin current output, then change code. The azizu06 "timed tests" ladder is close in spirit [github].
- Graders reward (Hello Interview guide): "Your main job shifts from verifying the implementation to verifying the tests themselves" [guide].
- Evidence strength: weak. Keep it in the kit set because Staff loops probe test strategy after the change.

### 1.9 Integrate an unfamiliar library or API into existing code

- Companies: Google code comprehension (unfamiliar codebase of about 200 to 500 lines) is closest [report]. Affirm (candidate reports of Flask/Python codebases) [guide]. Ramp (unfamiliar repo) [report].
- Example: none specific to an external API in a public report. Google's pilot is about reading, not integrating.
- Evidence strength: weak. No company was found that explicitly tests integration of a new third-party API in an AI-allowed round.

### 1.10 Production incident, log-driven debugging, rollback reasoning

- Companies: Coinbase (official excerpt: "reasoning about rollback scenarios") [official excerpt]. Coinbase candidate report: one loop had a round with "production debugging" [report, https://prachub.com/interview-experiences/coinbase-software-engineer-interview-experience-three-oas-a-block-mining-coding-round-and-two-ai-assisted-rounds; search excerpt, not verified on page]. Notion (PracHub listing, Jun 1, 2026: "Parse JSON logs, filter by time window, and rank the most frequent errors") [report, https://prachub.com/ai-assisted]. Rippling (PracHub listing, May 31, 2026: "Transform log data and support ordered text search over it") [report].
- Example: Notion-style log triage. The task is to parse, filter by time, and rank errors. This is a coding task with a log-shaped input, not a live incident.
- Time box: not reported.
- Graders reward (Coinbase excerpt): triage, then rollback reasoning. The Coinbase blog excerpt names the skill, not a rubric.
- Evidence strength: medium for Coinbase, weak for the rest. Generic production-debugging prompts (Dataford "rollback planning") are practice prompts, not reports [unverified].

### 1.11 Anything else (migration, security fix, data cleanup, idempotency)

- Companies: DoorDash (PracHub listing, Jun 5, 2026, "Implement Timeout Refund Workflow", Senior+: "Build a retry-safe, idempotent refund workflow for timed-out payments") [report, https://prachub.com/ai-assisted]. Stripe (PracHub listing, Apr 29, 2026, "Assign Reviewers from Changed Files", a Java tool that picks a PR reviewer from a Git repo's changed files) [report]. Datadog ("Implement a Snowflake Query Client", config-driven) [report].
- Example: the DoorDash refund item is a payments-flavoured idempotency task. Good for the Stripe kit set.
- Evidence strength: medium for a PracHub listing, but titles only. The page does not give the full task text.

## 2. Companies beyond the known list

Format: company, round type, AI status, evidence, tag. "Unknown" means I did not find a source I could open.

| Company | Round type seen | AI status | Evidence and tag |
|---|---|---|---|
| Datadog | Live coding bans AI unless told; AI coding interviews explicitly allowed when announced | AI allowed only when announced | Official: "You will be explicitly told in advance if you will be in an AI coding interview." [official, https://careers.datadoghq.com/candidate-experience/interviewing-at-datadog-ai-guidelines/, last updated May 13, 2026]. Debugging round not named on the page. Blind thread on AI copilot in some rounds [unverified]. |
| Anthropic | Live interview and take-home | AI banned unless told | Official: "This is all you–no AI assistance unless we indicate otherwise." Take-home: "Complete these without Claude unless we indicate otherwise." [official, https://www.anthropic.com/candidate-ai-guidance, last updated Jul 10, 2025]. Some guides say Anthropic runs an AI-collaborative round [guide, https://www.techinterview.org/post/3233474914/anthropic-interview-process-ai-collaborative-2026/, conflicts with official]. |
| Stripe | Bug bash (1 hour, find the bug) and coding (1 hour) | AI banned per interviewing.io; conflicting reports | "AI use in Stripe interviews is strictly prohibited." [guide, https://interviewing.io/stripe-interview-questions]. Conflicting: a Forward Deployed Engineer candidate said AI was explicitly allowed in its coding round [report, https://www.tryexponent.com/experiences/stripe-forward-deployed-engineer-interview-5498d0]. Stripe also appears in PracHub's AI-assisted list (Apr 29, 2026). |
| Ramp | AI-assisted development screen; practical multi-part task | Partly AI | PracHub report (July 2026): candidate screened on daily AI use and did not pass [report, https://prachub.com/interview-experiences/ramp-software-engineer-interview-ai-assisted-development-screen-9b2bf8451d]. PracHub listing: "Implement and Defend an AI-Assisted Repository Change" (May 25, 2026) [report]. |
| Brex | 60-minute debugging round for some teams | Not stated | 2026 guide: "a small codebase with failing unit tests" [guide, https://www.techprep.app/blog/brex-interview-process]. 2021 candidate review on latent errors [report, not opened]. |
| Affirm | Live coding on existing Flask/Python codebases; debugging question | Not stated | Guide: "navigating existing Flask and Python codebases" [guide, https://www.techprep.app/blog/affirm-interview-process]. Anonymous review Nov 2024 [report, not opened]. |
| Block (Square, Cash App) | Coding, system design, domain rounds | Unknown | Third-party guide: no AI tools in the loop mentioned [guide, https://www.techinterview.org/companies/block/]. Block's own statements about AI use are in coverage of Q2 2026 results [report, https://cointelegraph.com/markets/block-raises-2026-outlook-strong-quarter-says-ai-touches-nearly-all-code]. |
| Plaid | Standard loop with OA and phone screen | Unknown | No debugging round found. Guide only [guide, https://www.techprep.app/blog/plaid-interview-process]. Candidate report of reconciling two transaction feeds [report, not opened]. |
| Uber | Standard loop (CodeSignal, phone, 4 to 6 rounds) | Unknown | Named as an AI-round company in Hello Interview's intro [guide, https://www.hellointerview.com/learn/ai-coding/overview/introduction]. No dedicated page found. |
| Atlassian, Figma | No reliable policy | Unknown | Search returned no reliable source. |
| Notion | Log parsing task (PracHub, Jun 1, 2026). Generally permissive per tracker | AI generally allowed (tracker) | Tracker only [guide, https://www.techinterview.org/post/3233474911/ai-tool-policy-tracker-tech-companies-2026/, unverified]. PracHub log task [report]. |
| OpenAI | Varies by team; research AI-restricted per guide | Mixed | Guide only [guide, https://www.techinterview.org/post/3233474915/openai-interview-process-2026-team-by-team/, unverified]. |
| Shopify | Two AI rounds (screen and onsite), BYO IDE, empty repo | AI allowed | Guide [guide, https://www.hellointerview.com/blog/shopify-ai-enabled-coding]. Candidate report: 75-minute pair round [report, not opened]. |
| LinkedIn | One AI round replacing one coding round | AI optional | Guide [guide, https://www.hellointerview.com/blog/linkedin-ai-enabled-coding]. |
| Canva | Round replacing CS fundamentals (about 1 hour per a secondary guide) | AI expected | Official: "We're evaluating candidates on skills that matter more than ever" [official, https://canva.dev/blog/engineering/yes-you-can-use-ai-in-our-interviews, Jun 11, 2025]. |
| Google | Code comprehension pilot, junior and mid-level, H2 2026 | AI allowed (Gemini only) | Report quoting internal doc, plus spokesperson confirmation [report, https://www.shopifreaks.com/google-pilots-new-software-engineering-interview-process-that-lets-candidates-use-ai-assistant-gemini-during-coding-rounds/]. |
| Meta | AI-enabled round, three phases, CoderPad | AI allowed (model choice) | Guide [guide, https://www.hellointerview.com/blog/meta-ai-enabled-coding]. Rollout "in October 2025" per Hello Interview. |
| DoorDash | 60-minute AI-assisted working session | AI expected | Official excerpt [official excerpt, https://careersatdoordash.com/blog/doordash-is-rebuilding-its-engineering-interviews-around-ai/]. |
| Coinbase | Repository-based backend questions since Jan 2026 | AI tools available | Official excerpt, blog dated Jul 13, 2026 [official excerpt, https://www.coinbase.com/blog/interviewing-engineers-in-the-ai-era-lessons-from-a-year-of-rebuilding]. Report: AI-assisted Flappy Bird jump function; passed 16 of 20 tests [report, prachub]. |
| Rippling | OOD rule engine; AI allowed per recruiter quote | AI allowed | Report [report, leetcode.com discuss, search excerpt]. |

Stripe is the most important conflict. Treat its AI policy as unknown until the recruiter answers.

## 3. Official grading rubrics

Verbatim quotes with URLs. Only items I could open are quoted as fully verified. Excerpts are marked.

### 3.1 Canva [official, verified]

URL: https://www.canva.dev/blog/engineering/ai-interview-success/ (date on page: Oct 20, 2025)

- "We want to see you use AI like the productive engineer you'll be on day one."
- "We're assessing your engineering capabilities enhanced by AI collaboration, not your AI skills in isolation."
- Three core areas: "Engineering Problem-Solving: How do you approach ambiguous, realistic problems?" / "Technical Depth & Ownership: Do you understand and own the code in your solution?" / "AI Collaboration Effectiveness: Do you use AI tools to accelerate appropriate tasks while maintaining technical control?"
- Three phases: Planning, Development, Discussion.

Also: https://canva.dev/blog/engineering/yes-you-can-use-ai-in-our-interviews (Jun 11, 2025): "we expect engineers to take full ownership of any code they produce, whether they wrote it themselves or with AI assistance."

### 3.2 DoorDash [official, excerpt only]

URL: https://careersatdoordash.com/blog/doordash-is-rebuilding-its-engineering-interviews-around-ai/ (official post dated March 19, 2026 per a search summary; I could not fetch the page, HTTP 403 and JavaScript shell).

Excerpt, from search: "replacing traditional coding rounds with a 60-minute, AI-assisted engineering working session. You join a realistic project, ramp up, and start contributing." Scoring areas: "How you get oriented, how you use AI and verify outputs, how you debug, how you manage scope, and how you communicate tradeoffs." Also: "Finishing every task is less important than showing a tight loop and good judgment."

Status: [unverified verbatim]. Re-check the page in a browser before quoting it to anyone.

### 3.3 Coinbase [official, excerpt only]

URL: https://www.coinbase.com/blog/interviewing-engineers-in-the-ai-era-lessons-from-a-year-of-rebuilding (dated July 13, 2026 per search summary; WebFetch and curl both returned 403 or a Cloudflare challenge).

Excerpt: "We developed custom repository-based questions where candidates worked in a realistic codebase: debugging issues, reviewing code for correctness and performance, reasoning about rollback scenarios, all with AI tools available." Also: "Can they triage real issues? Can they catch subtle bugs that AI introduces? Do they understand what they're accepting when they accept an AI-generated change?" Also, the company moved to "repository-based backend questions in January 2026" and found "standard frontend questions were not built for AI-present settings, since the AI solved most of them directly."

Status: [unverified verbatim].

### 3.4 Datadog [official, verified]

URL: https://careers.datadoghq.com/candidate-experience/interviewing-at-datadog-ai-guidelines/ (last updated May 13, 2026)

- "In these interviews, you may be explicitly allowed (and expected) to use AI tools as part of your workflow."
- "You will be explicitly told in advance if you will be in an AI coding interview."
- "Unless explicitly stated otherwise, you should not use AI tools during live coding interviews or technical assessments."

No rubric is published for AI-assisted rounds.

### 3.5 Anthropic [official, verified]

URL: https://www.anthropic.com/candidate-ai-guidance (last updated Jul 10, 2025)

- Take-home: "Complete these without Claude unless we indicate otherwise."
- Live: "This is all you–no AI assistance unless we indicate otherwise."
- Not permitted: "Having Claude write your code when we haven't explicitly allowed it"

No rubric is published. Note: a guide says Anthropic runs an AI-collaborative round graded on "prompt clarity, verification, decomposition, and integration" [guide, https://www.techinterview.org/post/3233474914/anthropic-interview-process-ai-collaborative-2026/]. This conflicts with the official page for live rounds. Trust the official page.

### 3.6 Meta [no official rubric found]

No Meta-hosted rubric or candidate guide was found. The rubric that appears in the sources is from the practice repo below and from guides. One prep site says Meta's rubric "centers on three areas" (problem solving, code development, verification and debugging). That site cites leaked or secondhand detail, and I could not open the source [unverified].

Interviewing.io's Meta guide quotes the interviewers: "the interviewers are evaluating how well you leverage the AI to produce a great solution" and they are "watching to ensure you're not using the tool as a crutch." [guide, https://interviewing.io/blog/how-to-use-ai-in-meta-s-ai-assisted-coding-interview-with-real-prompts-and-examples; the page gives no publication date.]

Meta internal message quoted by Hello Interview: "a new type of coding interview in which candidates have access to an AI assistant. This is more representative of the developer environment that our future employees will work in, and also makes LLM-based cheating less effective." [guide, https://www.hellointerview.com/blog/meta-ai-enabled-coding]

### 3.7 Google [report, secondary]

No official Google page found. Secondary coverage of an internal document (Business Insider, not opened): "candidates are evaluated on 'AI fluency, including prompt engineering, output validation and debugging skills.'" [report, https://www.shopifreaks.com/google-pilots-new-software-engineering-interview-process-that-lets-candidates-use-ai-assistant-gemini-during-coding-rounds/]. Spokesperson confirmed Gemini as the assistant [report, search excerpt].

### 3.8 Stripe [guide, no rubric]

Stripe has no public rubric. The debug-round guidance from a guide: "whether you change a single variable at a time and predict what will happen before you run anything." [guide, https://www.techinterview.org/post/3233476091/debugging-interview-format/, updated Jul 2, 2026]

### 3.9 Shopify [guide, no official rubric]

Guide: "How do you break down a problem? How do you build context for an AI agent? How do you build and test incrementally?" [guide, https://www.hellointerview.com/blog/shopify-ai-enabled-coding]. No official Shopify page was found in my searches.

### 3.10 LinkedIn [guide, no official rubric]

Guide: "LinkedIn reportedly uses a 4-point grading scale where a 3 is passing, and scoring is relative to other candidates." [guide, https://www.hellointerview.com/blog/linkedin-ai-enabled-coding]. Mark as unverified count.

### 3.11 Practice-repo rubric (not any employer)

The azizu06 repo ships six dimensions, each scored 1 to 4: code comprehension, debugging, implementation, optimization, AI usage, communication. Example AI-usage anchor for 1: "Either ignored the assistant almost entirely, or pasted its output straight in without reading." Anchor for 4: "caught the model being confidently wrong." [github, https://github.com/azizu06/ai-coding-interview-practice/blob/main/RUBRIC.md]. This is a practice rubric. It is not Meta's, DoorDash's or any employer's.

## 4. Planted-bug design

What the sources say rounds plant or test. Public examples are thin. I did not open the answer keys in the practice repo, so the list below uses only prose descriptions.

| Bug class | Where it appears | Source |
|---|---|---|
| Type cast (int to double where int expected) | Meta phase 1 | [guide, hellointerview Meta] |
| Off-by-one | Meta phase 1 | [guide, hellointerview Meta] |
| Incorrect conditional | Meta phase 1 | [guide, hellointerview Meta] |
| Safety cap instead of a real fix (iteration cap of 10,000 throws, real fix is a visited set for infinite loops) | Meta E7 candidate | [guide, hellointerview Meta] |
| Generic version of a real production bug | Stripe bug bash | [guide, interviewing.io] |
| Two planted bugs per domain class, plus commented-out tests with `????` | azizu06 practice repo (all ten problems) | [github, README.md] |
| Substring check that counts a word as containing itself | azizu06 reference walkthrough (only example described on the page) | [github, README.md, reference walkthrough] |
| Money: float or double for currency, rounding returns 0.005 where zero is expected | Rippling (candidate report, not described as planted) | [report, Glassdoor Feb 2026, search excerpt] |
| Assistant introduces a bug while helping | azizu06 README: "The assistant will confidently introduce bugs." | [github, README.md, line about reference walkthrough] |
| AI hides bugs when asked to "describe the codebase" | Meta candidate report | [guide, hellointerview Meta] |

Bug classes the sources name but do not show in code: race conditions (LinkedIn follow-ups), rollback risk (Coinbase), idempotency for timed-out payments (DoorDash PracHub listing, title only).

Planted-bug design rules that show up in the sources:

- Bugs are "typically not algorithmic" (Meta, guide). They are small and local.
- Two bugs in one domain class is the practice-repo design. Real rounds may use one or many.
- The test suite hides the bug until the right test is uncommented (azizu06 design, `????` values).
- Real rounds may ask the candidate to explain the fix in terms of behavior, not "the test went green" (azizu06 rubric, debugging dimension).

Money-specific bug classes that match the Stripe profile (from my own knowledge, not a cited source): float rounding, currency minor units, rounding mode, double-charge on retry without an idempotency key, timezone cut-off for settlement day, and negative-balance race. Use them as practice seeds. Do not present them as a Stripe-reported list.

## 5. Practice resources with existing codebases

| Resource | Type | What it covers | Stars, last push | Tag |
|---|---|---|---|---|
| github.com/azizu06/ai-coding-interview-practice | repo | Ten problems with two planted bugs each, timed tests, interviewer prompt, six-dimension rubric | 37 stars, 3 forks, MIT, created 2026-09-15, last push 2026-09-15 (API, read 2026-10-17) | [github] |
| Hello Interview AI coding (learn section) | course | Framework: orientation, planning, driving the AI, verification, communication; problem breakdowns for 13 problems; company pages for Meta, Shopify, LinkedIn | not applicable | [guide, https://www.hellointerview.com/learn/ai-coding/overview/introduction] |
| Meta "the puzzle" | practice CoderPad | Sample problem Meta gives candidates before the round; recruiter can provide the CoderPad link with AI sidebar | not applicable | [guide, hellointerview Meta; search summary] |
| CodeSignal Agentic Interviewing | product | Candidates work with Claude Code, Codex or Cursor on a single live question | not applicable | [unverified, support page 403, search excerpt only] |
| interviewing.io | mock platform | Anonymous human mocks, AI interviewer for coding and system design | not applicable | [guide, search directory listing only] |
| PracHub AI-assisted hub | question bank | 20 AI-assisted items, updated Jun 29, 2026, some marked "AI Locked" | not applicable | [report, https://prachub.com/ai-assisted] |

Notes:

- No public GitHub repo with planted bugs was found besides azizu06. Search results for other "bug hunt" repos returned general prep repos.
- To practise Stripe's bug-bash style without AI, use the azizu06 repo with the AI turned off and the interviewer prompt as a timer.
- Do not open the repo's solutions folder before the timer ends. The README says so, and it matters for the practice to count.

## 6. Interviewer follow-ups

Collected from guides and official material. These come after the coding is done, unless noted.

| Follow-up | Where | Source |
|---|---|---|
| Add a requirement that breaks the design ("now add support for multiple robots") | Shopify | [guide, hellointerview Shopify] |
| Scale: "how it would perform if the dataset grew by orders of magnitude" | LinkedIn, data-processing problems | [guide, hellointerview LinkedIn] |
| Thread safety: "How would you synchronize access? What race conditions could occur?" | LinkedIn, cache problems | [guide, hellointerview LinkedIn] |
| Productionize: "How would you productionize this?" | LinkedIn | [guide, hellointerview LinkedIn] |
| Edge cases and malformed or missing data | LinkedIn | [guide, hellointerview LinkedIn] |
| Bigger data file that breaks phase-2 solution, then a tradeoff question | Meta phase 3 | [guide, hellointerview Meta] |
| Explain the complexity of existing code before touching it | Meta phase 1 | [guide, hellointerview Meta] |
| Testing strategy: "How would you design your unit test? What can be improved in the test file?" | Shopify | [guide, hellointerview Shopify] |
| Explain why BigDecimal over double (money) | Rippling | [report, Glassdoor, search excerpt] |
| Rollback: "reasoning about rollback scenarios" | Coinbase | [official excerpt] |
| "Describe what the AI got wrong and why you accepted it" | Coinbase, DoorDash | [official excerpt] |
| "What do you do if the AI is wrong?" | Shopify ("garbage" output) | [guide] |

Follow-ups the sources do not show (write these into the kit as likely, not as reported): 10x traffic, observability and alerting, "how would you test this in production", feature flag rollout, and migrating existing data. These are my own additions, not reported.

## 7. Task type to company to example table

| Task type | Companies (AI status) | Concrete example | Time box |
|---|---|---|---|
| Fix failing tests, multi-file | Meta (AI rules vary) [guide]; Brex [guide]; Stripe variant [guide] | Meta phase 1: int cast to double, off-by-one, bad conditional | ~60 min |
| Bug from issue or log, no test | Stripe bug bash (no AI) [guide]; Coinbase (AI) [official excerpt]; Amazon (PracHub title) [report] | Stripe: find the bug in a generic version of a real bug | 45 to 60 min |
| Extend feature in stages | DoorDash (AI expected) [official excerpt]; Shopify (AI) [guide]; Ramp [report] | DoorDash: order dispatch or menu composer task | 60 min (DoorDash) |
| Refactor for extensibility, then feature | Rippling (AI allowed) [report]; Shopify SOLID follow-up [guide] | Expense policy engine, add a new rule | 20 to 60 min |
| Performance optimization | Meta phase 3 [guide]; Google pilot (AI, Gemini) [report]; azizu06 [github] | Substring problem: trie vs greedy tradeoff on two data files | part of 60 min |
| Concurrency or race fix | LinkedIn follow-up (AI optional) [guide] | Cache: synchronize access, race conditions | follow-up, not timed |
| Code review or AI-output review | Coinbase (AI) [official excerpt]; Shopify [guide]; Coinbase PracHub "Debug and Extend Cursor Queries" [report] | Validate AI-generated query code and explain | not reported |
| Characterization tests then change | No direct report | Pin current output, then change | not reported |
| Integrate unfamiliar library or API | Google (AI, Gemini) [report]; Affirm [guide] | Unfamiliar Flask codebase; add a feature | not reported |
| Production incident and rollback | Coinbase (AI) [official excerpt]; Notion log task [report] | Parse logs, filter by time, rank errors | not reported |
| Migration, security, idempotency, data cleanup | DoorDash refund workflow (AI) [report]; Stripe reviewer tool [report] | Retry-safe refund for timed-out payments | not reported |

## 8. Sources table

| URL | Date | What it says | Tag |
|---|---|---|---|
| https://www.canva.dev/blog/engineering/ai-interview-success/ | Oct 20, 2025 (page) | Three rubric areas, three phases, "AI Collaboration Effectiveness" | [official, verified] |
| https://canva.dev/blog/engineering/yes-you-can-use-ai-in-our-interviews | Jun 11, 2025 | CS fundamentals round replaced; "full ownership of any code they produce" | [official, verified] |
| https://careers.datadoghq.com/candidate-experience/interviewing-at-datadog-ai-guidelines/ | May 13, 2026 (page) | AI allowed only when told in advance; AI banned in live coding otherwise | [official, verified] |
| https://www.anthropic.com/candidate-ai-guidance | Jul 10, 2025 (page) | "no AI assistance unless we indicate otherwise" in live interviews | [official, verified] |
| https://careersatdoordash.com/blog/doordash-is-rebuilding-its-engineering-interviews-around-ai/ | Mar 19, 2026 (search summary) | 60-minute AI working session; five scoring areas | [official, excerpt only] |
| https://www.coinbase.com/blog/interviewing-engineers-in-the-ai-era-lessons-from-a-year-of-rebuilding | Jul 13, 2026 (search summary) | Repository-based questions; triage, catch AI bugs, rollback | [official, excerpt only] |
| https://github.com/azizu06/ai-coding-interview-practice | created and pushed 2026-09-15 (API) | Ten problems, planted bugs, 50-minute timer | [github, verified] |
| https://github.com/azizu06/ai-coding-interview-practice/blob/main/RUBRIC.md | Repo state 2026-10-16 | Six dimensions 1 to 4 with anchors | [github, verified] |
| https://github.com/azizu06/ai-coding-interview-practice/blob/main/INTERVIEWER_PROMPT.md | Repo state 2026-10-16 | Interviewer prompt, timer rules | [github, verified] |
| https://www.hellointerview.com/blog/meta-ai-enabled-coding | Oct 2025 rollout (per page) | Three phases, CoderPad, "the puzzle", planted bug types | [guide, verified] |
| https://www.hellointerview.com/blog/shopify-ai-enabled-coding | page undated | Empty repo, BYO IDE, evaluation criteria | [guide, verified] |
| https://www.hellointerview.com/blog/linkedin-ai-enabled-coding | page undated | Concurrency follow-ups, 4-point scale (reported) | [guide, verified] |
| https://www.hellointerview.com/learn/ai-coding/overview/interview-formats | page undated | Three-phase arc: fix bug, add feature, optimize | [guide, verified] |
| https://www.hellointerview.com/learn/ai-coding/fundamentals/verification-and-testing | page undated | Agree test cases with interviewer, tests as verification | [guide, verified] |
| https://www.hellointerview.com/learn/ai-coding/fundamentals/codebase-orientation | page undated | Entry point, data models, tests first | [guide, verified] |
| https://www.hellointerview.com/learn/ai-coding/overview/introduction | page undated | Companies named: Meta, Shopify, LinkedIn, Canva, Uber | [guide, verified] |
| https://interviewing.io/stripe-interview-questions | page undated; footer 2026 | "AI use in Stripe interviews is strictly prohibited"; bug bash 1 hour | [guide, verified] |
| https://interviewing.io/blog/how-to-use-ai-in-meta-s-ai-assisted-coding-interview-with-real-prompts-and-examples | page undated | Meta sample prompts; "not using the tool as a crutch" | [guide, verified] |
| https://www.techinterview.org/post/3233476091/debugging-interview-format/ | updated Jul 2, 2026 | Debug round, 45 minutes, "single variable at a time" | [guide, verified] |
| https://prachub.com/ai-assisted | updated Jun 29, 2026 | 20 AI-assisted items with dates and task summaries | [prachub, verified list] |
| https://prachub.com/interview-experiences/ramp-software-engineer-interview-ai-assisted-development-screen-9b2bf8451d | Jul 2026 (per search) | Ramp AI screen, did not pass | [prachub, search excerpt] |
| https://prachub.com/interview-experiences/coinbase-software-engineer-interview-experience-three-oas-a-block-mining-coding-round-and-two-ai-assisted-rounds | undated | Coinbase OA3 Flappy Bird jump boundary, 16 of 20 tests | [prachub, search excerpt] |
| https://www.shopifreaks.com/google-pilots-new-software-engineering-interview-process-that-lets-candidates-use-ai-assistant-gemini-during-coding-rounds/ | 2026 | Google pilot: code comprehension, Gemini, "AI fluency" | [report, verified excerpt] |
| https://www.theregister.com/2025/06/11/canva_coding_assistant_job_interviews/ | Jun 11, 2025 | Canva requirement news coverage | [report, search excerpt] |
| https://careers.northeastern.edu/blog/2026/05/13/googles-ai-assisted-coding-interview-2026-guide/ | May 13, 2026 | Google guide, format detail | [guide, not opened] |
| https://leetcode.com/discuss/post/8351482/ripplings-ai-powered-coding-round-what-i-sfms/ | undated | Rippling OOD round; AI allowed per recruiter quote | [report, fetch 403, search excerpt] |
| https://leetcode.com/discuss/post/7595344/stripe-onsite-interview-hopeful-pass-sha-x8le/ | undated | Stripe debug round details | [report, fetch blocked, search excerpt only] |
| https://www.tryexponent.com/experiences/stripe-forward-deployed-engineer-interview-5498d0 | undated | FDE candidate: AI allowed in coding round | [report, search excerpt] |
| https://www.techprep.app/blog/brex-interview-process | 2026 (per page title) | Brex: 60-minute debugging round for some teams | [guide, search excerpt] |
| https://www.techprep.app/blog/affirm-interview-process | 2026 | Affirm: existing Flask codebases | [guide, search excerpt] |
| https://www.techinterview.org/post/3233474911/ai-tool-policy-tracker-tech-companies-2026/ | 2026 | Policy tracker, lists Notion, Stripe, Canva, Linear as AI-permitted in some form | [guide, unverified] |
| https://www.techinterview.org/post/3233474914/anthropic-interview-process-ai-collaborative-2026/ | 2026 | Says Anthropic has AI-collaborative round; conflicts with official | [guide, unverified] |
| https://cointelegraph.com/markets/block-raises-2026-outlook-strong-quarter-says-ai-touches-nearly-all-code | Q2 2026 | Block says AI touches nearly all code | [report, search excerpt] |

## 9. Not found / could not open

- Coinbase blog (dated July 13, 2026). WebFetch returned 403. curl returned a Cloudflare challenge page. Rubric and round details are search excerpts only. [unverified verbatim]
- DoorDash blog (dated March 19, 2026). WebFetch returned 403. curl returned a JavaScript shell. Excerpts are from a search summary. [unverified verbatim]
- CodeSignal Agentic Interviewing help article. WebFetch returned 403. [unverified]
- Business Insider original article on the Google internal document. Not found in search. Coverage quotes it secondhand. [unverified]
- Rippling LeetCode post (8351482). WebFetch returned 403. Excerpts from search only. [unverified]
- Stripe debug-round LeetCode post (7595344). The LeetCode GraphQL call returned no data and the page fetch returned a Cloudflare challenge. [unverified]
- Greatfrontend Stripe engineering-team-screen PDF. Text was compressed and unreadable. The search summary said it bans AI; I could not confirm that. Not cited. [unverified]
- Meta's own candidate guide or rubric. None found. [not found]
- Google's own careers post on the code comprehension pilot. None found. [not found]
- Shopify engineering blog post on interview changes. None found. [not found]
- Anything in the azizu06 repo's solutions folder. I did not open it on purpose. [not opened]
- Robinhood interview format. No source found. [not found]
- Atlassian and Figma AI policy. No reliable source found. [not found]
- Adyen, Chime AI-round evidence. No source found. [not found]
- Plaid debugging round. No source found beyond general guides. [not found]
- Uber AI round. No source found. The intro guide names Uber but gives no details. [not found]
- A public planted-bug answer key from a real company. None found. [not found]
- A public report of a characterization-test or library-integration round at any company. None found. [not found]
- Meta "the puzzle" text. Only guide descriptions. [not found]
- A Stripe-specific rubric. None found. [not found]
- Candidate reports on Stripe debugging round details beyond the guides. Only guides found. [unverified]

## 10. Recommendation: 10 task types to practise for a Stripe Staff loop

Ranked by payoff for a payments-company Staff loop. Each has a payments example. Run each one twice: once with AI off (Stripe's public stance) and once with AI allowed (in case the recruiter says yes, or the loop is a different team).

1. Fix failing tests, multi-file. Example: a ledger module has three red tests. One fails because the fee-proration function rounds half-up instead of half-even. Another fails because a settlement cutoff uses UTC instead of the merchant's timezone. Find both from the test output. Explain each fix in terms of the behaviour the code promises. [Meta phase 1, Stripe bug-bash shape]

2. Bug from an issue report or log, no test given. Example: a support ticket says merchants see two `payment_intent.succeeded` events after a webhook retry. The log shows the same event id twice within 40 ms. Find the dedupe bug (idempotency key scoped to the wrong account, or the check runs after the side effect). [Stripe bug bash, Coinbase triage]

3. Extend a feature in staged parts. Example: add partial refunds to an existing refund service. Stage 1: refund up to the captured amount. Stage 2: several partial refunds that must sum correctly. Stage 3: refunds across currencies with different minor-unit exponents. Tests grow between stages. [DoorDash, Shopify follow-up pattern]

4. Refactor for extensibility, then add a feature. Example: a fee engine hard-codes three card-network rules in one function. Refactor to a rule interface. Then add a new rule for a country's digital-services tax without touching the existing rules. [Rippling OOD, Shopify open/closed follow-up]

5. Performance optimization of slow existing code. Example: a settlement report loops per merchant and issues one query each. Optimize to a single grouped query. Then the interviewer adds a dataset with 10 million rows where the grouped query spills memory. Name the bottleneck in N and M, and offer options, not one answer. [Meta phase 3, azizu06 optimization ladder]

6. Concurrency or race-condition fix. Example: two capture requests for the same payment intent both read status `requires_capture`, both call the processor, and the merchant is charged twice. Fix with a conditional update or row lock, and explain the failure window. Then answer: what if the processor call succeeds but the database write fails? [LinkedIn cache follow-up pattern, Stripe-style idempotency]

7. Code review of AI-generated change. Example: an AI-written retry wrapper retries every POST to the processor on timeout. Review finds that a retried charge with no idempotency key creates a second charge. Say what you accept, what you reject, and the test that would have caught it. [Coinbase review excerpt, Shopify AI-output check]

8. Characterization tests, then change. Example: a legacy payout batcher rounds each line item, then the total. You want to change it to round the total only. Before changing it, write tests that pin the current output for twenty real-shaped batches, including a case with 0.005 remainders. Then change the rounding and show the diff in outputs. [Hello Interview verification guidance; no direct report, so weak evidence]

9. Integrate an unfamiliar API or file format into existing code. Example: add parsing for a bank's ACH return file that you have not seen before, with a sample file and a spec of fifteen lines. Build the parser behind the existing interface, handle a malformed row, and say what you would verify with the bank before go-live. [Google comprehension pattern, Affirm existing-codebase pattern; weak evidence]

10. Production incident and rollback reasoning. Example: after a deploy, p99 authorization latency rises from 120 ms to 900 ms. Logs show a cache key change in the risk-scoring path and a spike in cache misses. Decide: roll back the deploy, flip a feature flag, or ship a forward fix. Name the blast radius and the metric that pages at 3am. [Coinbase rollback excerpt, DoorDash timeout-refund pattern]

Why this set: task types 1, 2 and 7 are the most reported across companies. Types 6 and 10 are the Staff-level follow-ups that the guides name. Type 8 is the one with least public evidence; keep it because Staff loops probe test strategy before changes.

Recommendation for the kit build: start with types 1, 2, 5 and 7 because they are the best reported and easiest to plant bugs in. Add 6 and 10 as follow-ups to each kit, not as separate kits.

## 11. Spot-check list for you

These are the claims most worth checking in a browser before you rely on them:

1. The DoorDash five scoring areas (search excerpt only).
2. The Coinbase "rollback scenarios" wording (search excerpt only).
3. The Stripe "strictly prohibited" line on interviewing.io (fetched, but the page is undated).
4. The Meta "the puzzle" name (guide only).
5. The LinkedIn "4-point scale where a 3 is passing" (guide, marked "reportedly").
6. The Google internal-document quote (secondhand).

---

## 12. Spot-check (2026-10-17, by the main session)

| Claim | Result |
|---|---|
| Hello Interview, Meta phase 1 bugs: int cast to double, off-by-one, incorrect conditionals, a 10,000-iteration cap hiding the real fix (a visited set) | Confirmed, quoted on the page. Effective main working time "roughly 30 minutes" |
| Canva rubric: Engineering Problem-Solving, Technical Depth & Ownership, AI Collaboration Effectiveness; phases Planning, Development, Discussion; dated Oct 20, 2025 | Confirmed |
| interviewing.io: "AI use in Stripe interviews is strictly prohibited" | Confirmed, but the page is undated. 2026 candidate reports describe an AI round with a built-in assistant, so treat the policy as round-specific |
