# Two-factor authenticator app (Google Authenticator)

> One-line answer: codes are computed on the phone from a shared secret and the clock (TOTP, RFC 6238), so the code path has no server and zero QPS. The website verifies over steps T-1, T, T+1, accepts each step once (compare-and-set on `last_step`), charges each attempt before evaluating it, and forces a password reset after 5 consecutive failures (NIST allows at most 100). The backend exists to keep the secrets when the phone is lost: a ~4 KB per-user vault encrypted end to end under a vault key wrapped per device (Secure Enclave / StrongBox) and once for recovery. Recovery without any device goes through HSM clusters that release the recovery key only for the right PIN and destroy it after 10 wrong guesses, behind a 24-hour cooling-off with alerts. At 100 M users the backend is ~1k sync reads/s and ~400 GB. The red node is the recovery path and its HSM escrow clusters.

Tier 4 breadth problem in [`hld/README.md`](../README.md). Reusable blocks: [`../../concepts/crdt.md`](../../concepts/crdt.md) (the vault merge is an LWW-element set), [`../../concepts/rate-limiting-and-load-shedding.md`](../../concepts/rate-limiting-and-load-shedding.md) (per-factor backoff), [`../../concepts/replication-and-quorums.md`](../../concepts/replication-and-quorums.md) (home-region factor rows, majority HSM counters), [`../../concepts/exactly-once.md`](../../concepts/exactly-once.md) (one-time codes as a conditional write), [`../../concepts/realtime-client-server-communication.md`](../../concepts/realtime-client-server-communication.md) (push as a hint, pull on open), [`../../concepts/signed-url.md`](../../concepts/signed-url.md) (HMAC as a capability, the same primitive as TOTP).

## Problem statement (as given)

"I want the design of a 2FA app like Google Authenticator App."

No verbatim interview prompt for Google Authenticator was found in candidate reports (see [`research/interview-framing-survey.md`](research/interview-framing-survey.md) and its corrections). In the wild the prompt arrives as "design an OTP service" or "design 2FA", e.g. "OTP with Cache (Uber Interview Question) (this is 2FA -- you have 2 devices involved ...)" in a curated Blind list (2023). Public guides cover the Google Authenticator framing: [ByteByteGo](https://bytebytego.com/guides/how-does-google-authenticator-or-other-types-of-2-factor-authenticators-work/) (setup and verification stages) and [SystemDesignHandbook](https://www.systemdesignhandbook.com/guides/how-google-authenticator-works-system-design/) (offline generation, multiple accounts, validation under 100 ms).

## What the web research changed

Sources checked on 2026-10-03. Notes and spot-check corrections in [`research/`](research/).

| Change | Requirement | Evidence |
|---|---|---|
| ADD | **Backup and restore are core, and the server must not be able to read the secrets.** Google's 2023 sync is described only as encrypted "in transit and at rest". Retool lost 27 customer accounts when an attacker took over an employee's Google account and got the synced codes | [Google help](https://support.google.com/accounts/answer/1066447), [Retool](https://retool.com/blog/mfa-isnt-mfa) |
| ADD | **Recovery after losing every device**, with a hardware guess limit on a low-entropy PIN (10 attempts, then destroyed) | [Apple iCloud Keychain escrow](https://support.apple.com/guide/security/escrow-security-for-icloud-keychain-sec3e341e75d/web), [Google Titan-backed backups](https://security.googleblog.com/2018/10/google-and-android-have-your-back-by.html) |
| ADD | **Accept each code once, cap consecutive failures at 100.** NIST SP 800-63B-4 §3.1.4 and §3.2.2 | [NIST](https://pages.nist.gov/800-63-4/sp800-63b.html) |
| ADD | **Sync fabric rules:** keys stored only encrypted, "SHOULD be encrypted using a method that employs a user-controlled secret", AAL2-equivalent MFA to reach them | NIST SP 800-63B-4 Appendix B |
| UPDATE | Clock handling: Google removed its in-app time correction in 7.0 and uses the OS clock. We keep ±1 step, learn drift per factor on the server, and warn on skew in the app | RFC 6238 §5.2 and §6, Google help |
| KEEP | Codes work offline, 6 digits, 30 s, SHA-1, `otpauth://` QR enrollment | RFC 6238, [Key URI format](https://github.com/google/google-authenticator/wiki/Key-Uri-Format) |
| BELOW THE LINE | Push approval (Microsoft Authenticator, Duo) and passkeys. Push is §5.6 as a mutation. Neither TOTP nor push is phishing-resistant (NIST §3.1.4) | [Microsoft number matching](https://learn.microsoft.com/en-us/entra/identity/authentication/how-to-mfa-number-match) |

## Final requirements

Functional:
1. Enroll: scan a QR from a website, store the secret, confirm with the first code.
2. Show every account's 6-digit code offline, refreshed every 30 s.
3. Verify at the website: accept a correct code once, within a small clock window, and stop guessing.
4. Back up and sync secrets across the user's devices, with adds, renames and deletes propagating.
5. Restore on a new phone, with the old phone or after losing every device.

Non-functional: 100 M users with sync, 30 M DAU, ~8 accounts each. Codes: 0 server calls, < 100 ms, airplane mode. Verify p99 < 50 ms in the home region. 5 consecutive failures force a password reset (NIST cap 100 as backstop), each step accepted once. No server, insider or account-takeover attacker can read a secret. Recovery: ≤ 10 PIN guesses per record in hardware, 24 h cooling-off. Availability: codes 100% (offline), verifier 99.99%, sync and recovery 99.9%. Consistency: strong per factor at the verifier, linearizable per user in the vault, eventual (seconds) across devices.

## What interviewers probe

Ranked by how often the sources raise them:
1. How does the phone's code match the server's with no network?
2. The phone clock is off. Window size, and what it costs.
3. Replay of a code within its window, and brute force of 10^6 codes.
4. The user loses the phone. Backup, restore, and backup codes.
5. Can the provider, or someone who phishes the account, read the secrets?
6. SMS vs TOTP vs push vs passkeys. Is any of it phishing-resistant?
7. Push approval and MFA fatigue, number matching.
8. How does the website store a secret it cannot hash?
9. Two devices edit offline. Sign-ins land in two regions at once.

## Files

| File | What it is |
|---|---|
| [`solution.md`](solution.md) | Full HLD in flow-first form: §4 builds Google's 2023 design one requirement at a time, §5 breaks it into an end-to-end encrypted design, then nitty-gritty |
| [`diagrams.md`](diagrams.md) | The D1 to D12 diagram set |
| [`edge-cases.md`](edge-cases.md) | Every "what if" with a 60-second answer and a confidence box |
| [`deep-dives/totp-algorithm-and-clock-drift.md`](deep-dives/totp-algorithm-and-clock-drift.md) | HOTP / TOTP internals, test vectors, URI parsing, windows, drift learning, runnable Python |
| [`deep-dives/vault-encryption-and-key-hierarchy.md`](deep-dives/vault-encryption-and-key-hierarchy.md) | Vault key, device slots, AEAD with associated data, device join by QR, revocation and rotation |
| [`deep-dives/recovery-and-hsm-escrow.md`](deep-dives/recovery-and-hsm-escrow.md) | The red node: PIN escrow in HSM clusters, 10-try counters, cooling-off, capacity, cluster failure |
| [`deep-dives/multi-device-sync-and-conflicts.md`](deep-dives/multi-device-sync-and-conflicts.md) | Delta sync, per-item merge, tombstones, regression re-upload, runnable merge simulation |
| [`deep-dives/server-side-verification.md`](deep-dives/server-side-verification.md) | The RP verifier: replay guard, backoff and the 100 cap, home region, secrets at rest, backup codes, runnable verifier |
| [`deep-dives/push-approval-and-phishing.md`](deep-dives/push-approval-and-phishing.md) | Push approval, number matching, MFA fatigue, why none of it stops a relay, passkeys |
| [`research/`](research/) | Three web surveys (interview framing, mechanisms, real-world architectures), each with a spot-check corrections table |
| `two-factor-authenticator.excalidraw` | My drawing. Missing until I draw it |
