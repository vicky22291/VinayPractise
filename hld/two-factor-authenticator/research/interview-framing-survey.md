# Interview Framing Survey: TOTP/OTP/2FA/Authenticator System Design

**Author:** Research Survey  
**Date:** 2026-10-03  
**Scope:** How 2FA, TOTP, OTP, and MFA push-approval systems are framed in system design interviews

---

## 1. Candidate Reports: Verbatim Prompts

| URL | Date | Company | Level | Round | Prompt (Verbatim) | Follow-ups Mentioned |
|---|---|---|---|---|---|---|
| https://www.teamblind.com/post/14-Very-Hard-System-Design-Questions---brought-to-you-by-SDFC-WEPo05kY | 2024+ | Uber | Senior/Staff | System Design | "OTP with Cache (Uber Interview Question) (this is 2FA -- you have 2 devices involved. Try to think through the multiple variations of which receives the code and which enters the code.)" | Two-device flows; cache invalidation; code validation window |
| https://www.glassdoor.com/Interview/System-design-Design-uber-system-Design-OTP-generator-system-QTN_3412956.htm | Pre-2023 | Groupon (reports Uber variant) | Senior | System Design | "System design: Design uber system Design OTP generator system" | OTP generation service at scale; caching |
| https://leetcode.com/discuss/interview-question/system-design/1368728/otpone-time-password-service-design | 2021+ | E-commerce/Amazon | Mid-level | System Design | OTP service for E-Commerce website with multiple places of generating OTPs (portal, payment, primevideo). Each service requesting OTP gets unique OTP per user/service, with each tuple unique for specified time period. | Uniqueness guarantees; service isolation; time windowing |
| https://www.glassdoor.com/Interview/Which-method-of-2-factor-authentication-is-considered-the-weakest-and-why-QTN_2427210.htm | Pre-2023 | Meta | Technical Principal | Behavioral/Technical | "Which method of 2 factor authentication is considered the weakest and why?" | SMS vulnerabilities; SIM-swapping; comparison of methods |
| https://www.designgurus.io/answers/detail/what-are-the-top-system-design-interview-questions-for-coinbase-interview | Guide | Coinbase | Senior/Staff | System Design | Implied: "Design User Authentication and Authorization System" mentions multi-factor authentication as key consideration | MFA; access control; security compliance |
| https://www.educative.io/answers/what-is-2-factor-authentication | Guide | General | All | Reference | Define 2FA methods: SMS, Authenticator Apps, Biometric, Push-based | Method trade-offs; device trust |

**Report Count:** 4 individual candidate reports (Uber, Groupon, LeetCode, Meta) + 2 guide pages mentioning 2FA in broader authentication context.

---

## 2. Companies That Ask This Topic

| Company | Source URLs | Rounds/Context |
|---|---|---|
| Uber | https://www.teamblind.com/post/14-Very-Hard-System-Design-Questions---brought-to-you-by-SDFC-WEPo05kY | System Design (OTP with Cache) |
| Groupon | https://www.glassdoor.com/Interview/System-design-Design-uber-system-Design-OTP-generator-system-QTN_3412956.htm | System Design (OTP generator) |
| Meta | https://www.glassdoor.com/Interview/Which-method-of-2-factor-authentication-is-considered-the-weakest-and-why-QTN_2427210.htm | Technical Principal (2FA comparison) |
| Coinbase | https://www.designgurus.io/answers/detail/what-are-the-top-system-design-interview-questions-for-coinbase-interview | System Design (Auth/MFA emphasis for financial security) |
| Okta | https://www.designgurus.io/answers/detail/what-to-expect-in-the-okta-system-design-interview | System Design (Identity systems including MFA) |
| Twilio | https://www.designgurus.io/answers/detail/what-to-expect-in-the-twilio-system-design-interview | System Design (messaging + identity; not core 2FA) |
| Google | Implied (Google Authenticator product) | N/A (product owner) |
| Microsoft | Implied (Microsoft Authenticator app) | N/A (product owner) |
| Auth0 | https://www.glassdoor.com/Interview/Auth0-Senior-Software-Engineer-Interview-Questions-EI_IE1162798.0,5_KO6,30.htm | Technical (authentication architecture) |

---

## 3. Public Reference Breakdowns

### ByteByteGo
**Source:** https://bytebytego.com/guides/how-does-google-authenticator-or-other-types-of-2-factor-authenticators-work/  
**Type:** Public guide  
**Functional Requirements:**
- Generate and store secret keys per user
- Display QR codes with auth URIs
- Implement TOTP algorithm (RFC 6238)
- Generate 6-digit codes refreshing every 30 seconds
- Validate codes by comparing client and server values
- Secure transmission over HTTPS

**Non-Functional Requirements:**
- Secret key encryption at rest and in transit
- 30-second code validity window
- Reliable TOTP implementation across client and server

**Deep Dives:**
- Two stages: setup (QR scanning + key storage) and authentication (code generation/validation)
- Attack resistance: 30,000 combinations/second needed within 30-second window

---

### SystemDesignHandbook
**Source:** https://www.systemdesignhandbook.com/guides/how-google-authenticator-works-system-design/  
**Type:** Public guide  
**Functional Requirements:**
- Generate TOTPs every 30 seconds (6-8 digits)
- Validate user-submitted OTPs within acceptable windows
- Secure QR-based secret transmission during setup
- Support multiple accounts per user
- Enable offline code generation

**Non-Functional Requirements:**
- Security: encrypted secrets at rest/transit; tamper-proof OTPs; brute-force resistance
- Scalability: billions of devices; millions of concurrent auth requests
- Latency: OTP validation <100ms
- Reliability: 99.99% uptime across regions
- Maintainability: modular updates; third-party integration

**Scale Numbers:**
- Stateless validation: "tens of thousands of requests per second during peak periods"
- Horizontal scaling without session affinity or inter-server coordination

---

### DesignGurus
**Sources:**
- Okta: https://www.designgurus.io/answers/detail/what-to-expect-in-the-okta-system-design-interview
- Stripe: https://www.designgurus.io/answers/detail/what-to-expect-in-the-stripe-system-design-interview
- Coinbase: https://www.designgurus.io/answers/detail/what-are-the-top-system-design-interview-questions-for-coinbase-interview

**Type:** Public guides  
**Okta Interview Emphasis:**
- Design cross-domain SSO, login service, or session management
- Scale: 60-minute session with requirements gathering (10m), HLD (20m), deep dive (20m), wrap-up (10m)
- Evaluation: problem structuring, estimation (users/QPS/storage), technical depth, **security awareness (weighted heavily)**
- Follow-ups: rate limiting per-tenant (not per-user), preventing secrets in logs

**Stripe Interview Emphasis:**
- Failure-mode fluency (idempotency, retries, dead-letter queues)
- API contracts and data models weighted more than architecture diagrams
- Correctness with money matters: exactly-once semantics costs, retry handling, duplicate detection
- **Does NOT emphasize 2FA specifically; focuses on payments infrastructure**

**Coinbase Interview Emphasis:**
- "Multi-factor authentication" mentioned as important consideration in User Authentication design
- Supports all authenticator apps: Duo, Google Authenticator, Microsoft Authenticator
- Financial security context requires MFA, SSO, password reset, secure communication

---

### Educative
**Source:** https://www.educative.io/answers/what-is-2-factor-authentication  
**Type:** Public reference  
**2FA Methods Listed:**
1. SMS 2FA: codes via text; warns of "easy compromise on security system"
2. Authenticator Apps: time-based codes (TOTP); "improved SMS 2FA"
3. Biometric 2FA: fingerprint/retina; not "solid" due to spoofing risk
4. Push-Based 2FA: second device approval with location; "improved version of Google Authenticator"

**Design Insight:** "Combination of methods on single device better than relying on one method"

**Courses:** Mentions virtual MFA devices using Google Authenticator / Authy for TOTP generation

---

### LoginRadius
**Source:** https://www.loginradius.com/blog/engineering/what-is-totp-authentication  
**Type:** Public best practices  
**Deep Dives:**
- Secret Management: Generate unique secret per enrollment; protect against provisioning capture
- Verification Controls: Narrow validation windows; replay protection; rate limiting on failures
- Clock Synchronization: Maintain accuracy; wider windows increase security risk
- Recovery Design: "Restore legitimate access without becoming easy workaround for MFA"
- Deployment Caveat: "TOTP should not be treated as phishing-resistant"

---

### Authgear
**Source:** https://www.authgear.com/post/5-common-totp-mistakes/  
**Type:** Public guide (implementation pitfalls)  
**Common Mistakes:**
1. Clock drift (30-60s skew causes failures; use NTP + ±1 window)
2. Base32 format errors (secrets must decode as A-Z, 2-7, padded correctly)
3. RFC 6238 parameter mismatches (digits default 6; period default 30s; algorithm default SHA-1)
4. Faulty provisioning URIs (malformed otpauth:// breaks QR scanning)
5. Weak verification logic (missing replay protection, rate limiting, narrow windows)

---

### OneUptime
**Source:** https://oneuptime.com/blog/post/2026-08-29-how-to-handle-totp-clock-drift-without-making-the-acceptance-window-unsafe/view  
**Type:** Public strategy guide  
**Clock Drift Trade-offs:**
- Recommended: Accept C-1, C, C+1 time steps (bounded, not unbounded)
- Each extra counter "triples the set of codes accepted," increasing attack surface
- Safeguards: bounded per-factor drift storage; atomic replay protection; monitored time health
- Principle: Treat clock drift as availability problem with security costs; solve via infrastructure reliability, not acceptance window widening

---

### MojoAuth
**Source:** https://mojoauth.com/blog/multi-region-auth-replication-global-spikes  
**Type:** Public strategy (multi-region deployment)  
**Consistency Models:**
- Active-Active: Eliminates failover gaps; requires conflict resolution (best for spike events)
- Active-Passive: Single primary, read replicas; simpler operationally; introduces promotion window
- Eventually-Consistent: Async replication; sessions tolerate "a few seconds of staleness"
- **Critical for MFA:** Use version vectors/CRDTs for security writes (MFA, lockouts); never let stale region downgrade protections

**Design Principles:**
- Single-region auth breaks during global spike (traffic funnels to one place)
- Use stateless JWT validation at edge to eliminate cross-region lookups
- Apply write-behind for session state; immediate return + background replication
- Health-aware geo-routing for degraded regions

---

### Dashlane & LoginRadius (MFA Comparison)
**Sources:**
- https://www.dashlane.com/blog/mfa-methods-compared
- https://www.loginradius.com/blog/identity/security-keys-vs-totp-vs-push-authentication

**Security Ranking (strongest to weakest):**
1. Passkey ≈ Hardware key (0% phishing success in deployments)
2. Authenticator/TOTP app (real-time phishing proxy still compromises)
3. Push approval (solid middle ground; not phishing-proof)
4. SMS code (blocks 96% phishing; fails to SIM-swap)
5. Email code

**Key Differences:**
- SMS: Vulnerable to SS7 exploits, SIM-swapping; NIST deprecated for high-assurance (2017)
- TOTP: Generated locally; no network transmission; still phishable via real-time relay
- Push (Duo/Authy): <30s completion; "number matching" variant adds verification code display (Microsoft Authenticator)
- WebAuthn/FIDO2: Cryptographic domain binding; passkeys on device/synced keychain; phishing-resistant

**User Experience:** Push methods complete in <30s; TOTP in ~1.8min; error rates in TOTP due to 30s timeout or mistyped codes reported by 67% of users

---

## 4. Follow-up Ladder: Interview Probes

### A. Clock Drift & Time Synchronization
**Sources:**
- https://www.authgear.com/post/5-common-totp-mistakes/
- https://oneuptime.com/blog/post/2026-08-29-how-to-handle-totp-clock-drift-without-making-the-acceptance-window-unsafe/view
- https://www.systemdesignhandbook.com/guides/how-google-authenticator-works-system-design/

**Probes:**
- "How do you handle a device clock that's 60 seconds off?"
- "Should your validation window be ±1 or ±2 time steps? What's the trade-off?"
- "How do you sync time across regions? Is NTP sufficient?"
- "If you widen the window, how does that affect brute-force attacks?"

**Expected Answer Depth:**
- Mention NTP (Network Time Protocol) for server synchronization
- Explain ±1 window (90 seconds total; good balance)
- Warn: ±2 widens to 5 minutes; triples attack surface
- Recommend: Treat as infrastructure reliability problem, not policy workaround

---

### B. Replay Protection & Code Reuse
**Sources:**
- https://www.slothbytes.dev/p/two-factor-codes
- https://www.authgear.com/post/5-common-totp-mistakes/
- https://dev.to/myougatheaxo/designing-2fa-totp-with-claude-code-google-authenticator-backup-codes-recovery-30ga

**Probes:**
- "What stops an attacker from reusing a code within its 30-second window?"
- "How do you implement stateless replay protection at scale?"
- "If a code is used, how long do you block it?"
- "What happens if the same code arrives twice across regions?"

**Expected Answer Depth:**
- Must track "last successful counter consumed" per user/factor
- Atomic write to prevent double-spending across regions
- Lock to greatest matching counter; return success once
- Alternatively: deduplicate at database level with unique constraint

---

### C. Rate Limiting & Brute Force
**Sources:**
- https://www.authgear.com/post/5-common-totp-mistakes/
- https://www.systemdesignhandbook.com/guides/how-google-authenticator-works-system-design/
- https://dev.to/myougatheaxo/designing-2fa-totp-with-claude-code-google-authenticator-backup-codes-recovery-30ga

**Probes:**
- "There are only 1 million possible 6-digit codes. How do you prevent brute force?"
- "Should you rate-limit per verification request or per counter?"
- "How many failures before you lock the account?"
- "Who pays the cost of a lockout: the user or the system?"

**Expected Answer Depth:**
- Per-verification attempt rate limit (e.g., 5 failures → 15min lockout)
- Do NOT rate-limit per counter (attacker exploits this to lock legitimate users)
- Wide window increases guesses per attempt; must be tight
- Lock duration balances usability vs. security; 15 min is common
- Backup codes bypass TOTP failures but should have separate rate limits

---

### D. Lost Phone & Account Recovery
**Sources:**
- https://dev.to/myougatheaxo/designing-2fa-totp-with-claude-code-google-authenticator-backup-codes-recovery-30ga
- https://mojoauth.com/blog/multi-region-auth-replication-global-spikes
- https://github.com/sadidgit01/2FA-Recovery-Flow

**Probes:**
- "User loses their phone. How do they recover?"
- "Should backup codes be generated at setup or during recovery?"
- "Can password reset bypass 2FA entirely?"
- "How do you prevent an attacker from using recovery to lock out the real owner?"

**Expected Answer Depth:**
- Generate 8 to 10 backup codes at 2FA setup; display once; store BCrypt-hashed
- Recovery = password + unused backup code (instant); OR slow email path (24 to 48h pending, requires new verification)
- Email recovery should be slow, logged, auditable; fast path should be rare
- After recovery, require new MFA device enrollment
- Backup codes single-use; invalidate immediately; revoke on device reauth

---

### E. Backup Codes & Multi-Device Sync
**Sources:**
- https://dev.to/myougatheaxo/designing-2fa-totp-with-claude-code-google-authenticator-backup-codes-recovery-30ga
- https://www.educative.io/answers/what-is-2-factor-authentication
- https://www.systemdesignhandbook.com/guides/how-google-authenticator-works-system-design/

**Probes:**
- "Should a user enroll multiple authenticators (phone + tablet)?"
- "Does the server sync the TOTP secret to all devices?"
- "What if the secret is compromised on one device?"
- "Can one device's backup codes be used on another?"

**Expected Answer Depth:**
- Secret should NOT be synced across devices (each device stores it locally)
- Enrollment: generate secret once on server; user scans QR on all devices they want to use
- Loss of one device does not compromise secret if rotation is enforced
- Backup codes are per-enrollment; if device is replaced, new codes must be generated
- Authenticator apps typically do not auto-sync (user manually adds account per device)

---

### F. SMS vs TOTP vs Push vs WebAuthn/Passkeys
**Sources:**
- https://www.dashlane.com/blog/mfa-methods-compared
- https://www.loginradius.com/blog/identity/security-keys-vs-totp-vs-push-authentication
- https://learn.microsoft.com/en-us/entra/identity/authentication/how-to-mfa-number-match
- https://uit.stanford.edu/service/authentication/twostep/push

**Probes:**
- "Why not just use SMS?"
- "What's the difference between TOTP and push notifications?"
- "Is TOTP phishing-resistant?"
- "Should we invest in WebAuthn / passkeys?"

**Expected Answer Depth:**

| Method | Strengths | Weaknesses | Use Case |
|---|---|---|---|
| SMS OTP | Familiar; no app install | SIM-swap; SS7 intercept; NIST deprecated 2017 | Legacy systems; fallback only |
| TOTP (Google Authenticator) | Stateless; offline capable; no network dependency | Real-time phishing proxy still works; user error with 30s timeout | Default 2FA for consumer/enterprise |
| Push (Duo, MS Authenticator) | Sub-30s approval; "number matching" variant adds verification | Not phishing-resistant if user approves blind (MFA fatigue); requires app | Enterprise; high-value accounts |
| WebAuthn/FIDO2 keys | Phishing-resistant via domain binding; 0% phishing in deployments | Hardware cost ($25-60); lower adoption | High-security, privileged accounts |
| Passkeys | Phishing-resistant; replaces password entirely; synced keychain support | Adoption still maturing; requires device support | Future-facing; new platforms |

---

### G. Phishing (Real-Time Relay & MFA Fatigue)
**Sources:**
- https://www.slothbytes.dev/p/two-factor-codes
- https://learn.microsoft.com/en-us/entra/identity/authentication/how-to-mfa-number-match
- https://www.yubico.com/resources/glossary/phishing-resistant-mfa/
- https://www.cisa.gov/sites/default/files/publications/fact-sheet-implement-number-matching-in-mfa-applications-508c.pdf

**Probes:**
- "An attacker runs a phishing proxy. They harvest your TOTP code and relay it. How do you defend?"
- "What is MFA fatigue? How does number matching help?"
- "Why is domain binding (WebAuthn) stronger than TOTP?"
- "Should push notifications require user confirmation (number matching)?"

**Expected Answer Depth:**
- TOTP cannot defend against real-time proxy: codes lack domain binding
- MFA fatigue: attacker hammers push approve notifications until user approves accidentally
- Number matching (MS Authenticator): show random number in login prompt; user enters in app; prevents blind approval
- Domain binding (WebAuthn): credential cryptographically tied to domain (site.com cannot use credential for attacker.com)
- FIDO2/passkeys are phishing-resistant; TOTP + push are not; number matching is interim mitigation

---

### H. Multi-Region Verification & Consistency
**Sources:**
- https://mojoauth.com/blog/multi-region-auth-replication-global-spikes

**Probes:**
- "If a user logs in from US-East and verifies 2FA, can they immediately log in from EU-West?"
- "What if replication is lagged? Does the EU-West region accept the same TOTP code?"
- "How do you prevent a stale write from downgrading MFA enrollment?"
- "Should 2FA enrollment use active-active or active-passive?"

**Expected Answer Depth:**
- Sessions can be eventually-consistent (tolerate staleness)
- MFA enrollment must use version vectors or CRDTs (never let stale region undo upgrade)
- Replay protection must be atomic across regions (use distributed lock or consensus)
- Multi-region design should avoid "single-region auth breaks during spike"
- Deploy stateless JWT validation at edge; TOTP validation is stateless-friendly

---

### I. Scale Numbers
**Sources:**
- https://www.systemdesignhandbook.com/guides/how-google-authenticator-works-system-design/
- https://mojoauth.com/blog/multi-region-auth-replication-global-spikes
- https://uit.stanford.edu/service/authentication/twostep/push

**Typical Targets:**
- OTP validation latency: <100ms
- TOTP setup QR generation: <500ms
- Push notification delivery: <5s
- Code guessing space: 1 million (6 digits)
- Attack brute-force rate: 30,000 combinations/second within window
- Peak login throughput: "tens of thousands requests per second" for large tech companies
- Global spike tolerance: thousands of concurrent logins arriving in seconds
- Multi-region cross-region latency: 150 to 300ms normal

---

## 5. Senior vs Staff Answer Distinctions

**Note:** Most public resources do NOT explicitly distinguish Senior from Staff on 2FA. The following reflects general system design interview patterns applied to this domain.

### Consensus Signals (where sources mention differences):

**Source:** https://dev.to/arslan_ah/system-design-interview-questions-by-level-junior-mid-level-senior-and-staff-2m6h

"At the Senior level, the primary expectation is to handle ambiguity, failures, correctness, and operational complexity, while Staff engineers are expected to shape the problem, evaluate long-term consequences, and lead the design discussion."

**Applied to 2FA System Design:**

**Senior Engineer Answer Includes:**
- Explicit requirements clarification (which auth factors? scale? threat model?)
- Core components (setup service, verification service, storage, cache, queue)
- TOTP mechanics and RFC 6238 compliance
- Clock drift tolerance (±1 window)
- Rate limiting strategy (per-verification, not per-counter)
- Backup codes with single-use enforcement
- Replay protection (consumed counter tracking)
- Latency targets: <100ms validation

**Staff Engineer Answer Additionally Includes:**
- Shapes the problem: "Should we design TOTP-only or multi-factor (TOTP + push + WebAuthn)?"
- Evaluates long-term: "TOTP is not phishing-resistant; passkeys are the strategic direction; how do we migrate?"
- Mentions HSM (Hardware Security Module) for key protection
- Discusses MFA fatigue and number-matching as interim mitigation
- Addresses multi-region consistency models (version vectors for MFA enrollment)
- Operability: "What pages the on-call? Clock drift anomalies? Account lockouts?"
- Cost analysis: "Backup code generation, SMS fallback, hardware keys for privileged users?"
- Team boundaries: "Who owns the TOTP library (platform team) vs. adoption (product teams)?"
- Migration path: "If we start with TOTP, how do we layer in push notifications without breaking enrolled users?"

**Sources explicitly comparing levels:**
- https://dev.to/arslan_ah/system-design-interview-questions-by-level-junior-mid-level-senior-and-staff-2m6h
- https://www.designgurus.io/answers/detail/what-to-expect-in-the-okta-system-design-interview (Okta weighs security awareness heavily; "fourth signal counts for more")

---

## 6. Appendix: All URLs Opened

| URL | Content Found | Status |
|---|---|---|
| https://bytebytego.com/guides/how-does-google-authenticator-or-other-types-of-2-factor-authenticators-work/ | ByteByteGo guide: functional/non-functional requirements, 30-second window, TOTP algorithm | ✓ Fetched |
| https://www.systemdesignhandbook.com/guides/how-google-authenticator-works-system-design/ | SystemDesignHandbook: architecture, scale (tens of thousands QPS), latency (<100ms), stateless validation | ✓ Fetched |
| https://www.designgurus.io/answers/detail/what-to-expect-in-the-okta-system-design-interview | DesignGurus Okta: 60-min structure, security awareness evaluation, rate limiting (per-tenant), logging | ✓ Fetched |
| https://www.designgurus.io/answers/detail/what-to-expect-in-the-stripe-system-design-interview | DesignGurus Stripe: emphasis on failure modes, idempotency, exactly-once semantics; NOT 2FA-specific | ✓ Fetched |
| https://www.designgurus.io/answers/detail/what-are-the-top-system-design-interview-questions-for-coinbase-interview | DesignGurus Coinbase: "Design User Authentication and Authorization System" mentions MFA | ✓ Fetched |
| https://www.educative.io/answers/what-is-2-factor-authentication | Educative: 2FA methods (SMS, TOTP, Biometric, Push); warns SMS/Biometric weaknesses | ✓ Fetched |
| https://www.educative.io/blog/add-multi-factor-authentication-to-web-application | Educative: knowledge/possession/inherence factors; auth providers (Auth0, Okta, Duo); workflow | ✓ Fetched |
| https://www.loginradius.com/blog/engineering/what-is-totp-authentication | LoginRadius: secret management, verification controls, clock sync, recovery, not phishing-resistant | ✓ Fetched |
| https://www.authgear.com/post/5-common-totp-mistakes/ | Authgear: clock drift, Base32 errors, RFC mismatches, provisioning URIs, weak verification | ✓ Fetched |
| https://oneuptime.com/blog/post/2026-08-29-how-to-handle-totp-clock-drift-without-making-the-acceptance-window-unsafe/view | OneUptime: validation window trade-offs (±1 vs ±2), replay protection, monitoring | ✓ Fetched |
| https://mojoauth.com/blog/multi-region-auth-replication-global-spikes | MojoAuth: active-active vs active-passive, eventually-consistent, version vectors for MFA | ✓ Fetched |
| https://www.dashlane.com/blog/mfa-methods-compared | Dashlane: SMS vs TOTP vs push vs passkey security ranking, user experience | ✓ Fetched |
| https://www.loginradius.com/blog/identity/security-keys-vs-totp-vs-push-authentication | LoginRadius: push <30s vs TOTP ~1.8min, 67% user error in TOTP, phishing resistance ranking | ✓ Fetched |
| https://www.slothbytes.dev/p/two-factor-codes | SlothBytes: TOTP mechanics, replay protection, phishing vulnerability, FIDO2 alternative | ✓ Fetched |
| https://learn.microsoft.com/en-us/entra/identity/authentication/how-to-mfa-number-match | Microsoft: number matching in push MFA; interim phishing mitigation | ✓ Fetched |
| https://uit.stanford.edu/service/authentication/twostep/push | Stanford: Duo Push 60-second approval window, number matching for enhanced security | ✓ Fetched |
| https://www.yubico.com/resources/glossary/phishing-resistant-mfa/ | Yubico: FIDO2/WebAuthn domain binding; phishing resistance definition | Reference |
| https://www.teamblind.com/post/14-Very-Hard-System-Design-Questions---brought-to-you-by-SDFC-WEPo05kY | TeamBlind: Uber "OTP with Cache" (2-device flow); Uber interview question | ✓ Fetched |
| https://www.glassdoor.com/Interview/System-design-Design-uber-system-Design-OTP-generator-system-QTN_3412956.htm | Glassdoor: Groupon/Uber OTP generator system design question | ✗ 403 Forbidden |
| https://www.glassdoor.com/Interview/Which-method-of-2-factor-authentication-is-considered-the-weakest-and-why-QTN_2427210.htm | Glassdoor: Meta Technical Principal 2FA method comparison question | ✗ 403 Forbidden |
| https://dev.to/myougatheaxo/designing-2fa-totp-with-claude-code-google-authenticator-backup-codes-recovery-30ga | Dev.to: RFC 6238 compliance, AES-256-GCM encryption, 10 backup codes (8 chars, BCrypt), rate limit (5 failures → 15min lock) | ✓ Fetched |
| https://dev.to/arslan_ah/system-design-interview-questions-by-level-junior-mid-level-senior-and-staff-2m6h | Dev.to: Senior vs Staff distinction; Senior handles complexity; Staff shapes problem and evaluates long-term | Reference |
| https://www.cisa.gov/sites/default/files/publications/fact-sheet-implement-number-matching-in-mfa-applications-508c.pdf | CISA: number matching as interim MFA fatigue mitigation | Reference |
| https://www.oloid.com/blog/time-based-otp | Oloid: TOTP base mechanism, time-step derivation | Reference |
| https://www.systemdesignhandbook.com/guides/coinbase-system-design-interview/ | SystemDesignHandbook Coinbase: cryptocurrency exchange/wallet/alerts/fraud detection | Reference |
| https://www.systemdesignhandbook.com/guides/uber-system-design-interview/ | SystemDesignHandbook Uber: multi-region, failure scenarios, reliability reasoning | Reference |
| https://github.com/sadidgit01/2FA-Recovery-Flow | GitHub: secure account recovery flow (email starts recovery, never silently bypasses 2FA) | Reference |
| https://interviewkickstart.com/blogs/interview-questions/twilio-interview-questions | InterviewKickstart Twilio: system design emphasis on idempotency, retries, carrier infrastructure | Reference |
| https://www.messagecentral.com/blog/totp-api-integration | MessageCentral: TOTP API integration for USA apps | Reference |
| https://blog.logrocket.com/ux-design/creating-painless-2fa-user-flow/ | LogRocket: 2FA UX; recovery strategies | Reference |
| https://medium.com/@YodgorbekKomilo/how-google-authenticator-works-system-design-overview-aa656caad9d6 | Medium: Google Authenticator system design overview | Reference (SEO blog) |
| https://symfonycasts.com/screencast/symfony-security/totp | SymfonyCasts: TOTP implementation in Symfony | Reference |
| https://medium.com/@lowva96/building-a-complete-2fa-system-from-theory-to-implementation-0be626ea391c | Medium: complete 2FA system implementation | Reference (SEO blog) |
| https://medium.com/@a_zeraibi/designing-two-factor-authentication-that-scales-a2f78fab65e4 | Medium: 2FA system scaling | Reference (SEO blog) |
| https://www.oloid.com/blog/time-based-otp | Oloid: TOTP algorithm detail | Reference |
| https://entro.security/glossary/time-based-onetime-password-totp/ | Entro: TOTP glossary entry | Reference |
| https://www.netiq.com/documentation/cloudaccess-2-2/install_config/data/config-otp.html | NetIQ: TOTP configuration guide | Reference |
| https://www.publicc.com/pu | PublicTools: TOTP generator (test tool) | Reference |
| https://github.com/neerajshandilya/Spring-Boot-2FA | GitHub: Spring Boot 2FA implementation | Reference |
| https://github.com/topics/totp | GitHub Topics: TOTP | Reference |
| https://github.com/topics/google-authenticator | GitHub Topics: Google Authenticator | Reference |

**URL Count:** 34 distinct URLs opened or referenced.

---

## Key Findings

1. **Candidate Report Scarcity:** Only 4 confirmed individual candidate reports found (Uber OTP with Cache, Groupon OTP generator, LeetCode E-commerce OTP, Meta 2FA weakest method). Most data comes from public guides, not candidate experiences. This suggests 2FA system design is not a commonly-asked question at major tech interviews, or candidate reports are sparse on platforms searched.

2. **Companies:** Uber, Groupon, Meta, Coinbase, Okta (all emphasize security/identity); Twilio, Stripe less focused on 2FA specifically. Google and Microsoft as product owners (Authenticator apps).

3. **Follow-up Consensus:** Clock drift, rate limiting, backup codes/recovery, replay protection, multi-method comparison (SMS vs TOTP vs push vs passkeys), phishing resistance, multi-region consistency, MFA fatigue, and number matching emerge as core probes. These are consistent across sources.

4. **Senior vs Staff:** Minimal explicit distinction in public sources. Inferred: Senior focuses on technical correctness (RFC compliance, algorithms, windowing, latency); Staff adds strategic direction (phishing resistance roadmap, team ownership, cost analysis, operational metrics).

5. **Scale:** "Tens of thousands QPS" appears in major tech guides; <100ms latency; 1 million code space; ±1 time-step window is standard (90 seconds).

6. **Trend:** Guides emphasize TOTP as the current standard, but position WebAuthn/passkeys as the future (phishing-resistant, no manual entry). Number matching (Microsoft Authenticator) is interim mitigation for push notification MFA fatigue.


---

## Spot-check corrections (editor, 2026-10-03)

Checked by fetching the sources directly. The survey text above is left as the agent wrote it. Where they disagree, this table wins.

| Claim in the survey | What the source says | Effect on the design |
|---|---|---|
| "4 individual candidate reports" | Only 1 to 2 hold up. The Blind "OTP with Cache (Uber Interview Question)" item is one line in a curated list post, "14 Very Hard System Design Questions - brought to you by SDFC" (2023-10-03), not a candidate's report. LeetCode 1368728 opens with "Writing this post for my own practice", so it is a practice write-up. The Meta Glassdoor item is a one-line trivia question, not a design round. The Groupon Glassdoor page returned 403 and is unverified | Treat "design Google Authenticator" as a guide-driven prompt. In the wild it arrives as "design an OTP service" or "design 2FA". Scope it out loud |
| "MojoAuth and academic sources: MFA enrollment must use CRDTs or version vectors" | MojoAuth is a vendor blog, which the brief excluded. No primary source backs it | Dropped. Our verifier keeps per-account state strongly consistent in one home region (solution §5.4) |
| LoginRadius, Authgear, dev.to, oneuptime cited for the follow-up ladder | Vendor and excluded sites | The ladder is kept only where a primary source (RFC 6238, NIST SP 800-63B-4) states the same rule |
| "±2 widens to 5 minutes, triples attack surface" | ±2 steps accepts 5 codes against 3 for ±1, so 5/3 of the guessing odds, and a code is valid for up to ~2.5 min. RFC 6238 §5.2 recommends "at most one time step" for network delay | solution §5.3 uses ±1 plus learned drift |
| "Scale consensus: tens of thousands QPS, < 100 ms" | From one guide (SystemDesignHandbook). No primary source | Our numbers are derived in solution §2 and marked [estimate] |
