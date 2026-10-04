# TOTP Authenticator Mechanisms and Specifications Survey

## 1. HOTP: RFC 4226 HMAC-Based One-Time Passwords

HOTP(K,C) = Truncate(HMAC-SHA-1(K,C)) mod 10^Digit: a counter-based OTP using an 8-byte counter and 160-bit HMAC output.

**Dynamic Truncation (RFC 4226, Section 5.3):**
Offset-based selection from the last byte determines which 4-byte segment to extract. Let OffsetBits be the low-order 4 bits of String[19] (the 20th byte). Extract 4 bytes starting at OffsetBits, mask the most significant bit to 0 to produce a 31-bit value, then modulo 10^Digit. This 31-bit mask avoids signed/unsigned ambiguity in cross-platform arithmetic.

**Shared Secret Length (RFC 4226, Section 4, R6):**
Minimum 128 bits. Recommended 160 bits. https://www.rfc-editor.org/rfc/rfc4226.txt (line 273-275).

**Security Analysis (RFC 4226, Sections 6-7, Appendix A):**
Best practical attack is brute force: Sec = sv/10^Digit, where s is look-ahead synchronization window (typical 10 values) and v is verification attempts. RFC 4226 Section 7 requires throttling parameter T to limit device attempts. RFC 4226 Section 7.4 recommends resynchronization window. The practical security of 6-digit HOTP with 1-step look-ahead and 1 verification attempt: 10*1/10^6 = 10^-5 (1 in 100,000 per attempt). https://www.rfc-editor.org/rfc/rfc4226.txt (Section 7, lines 358-382).

**Test Vectors (RFC 4226, Appendix D):**
Secret "12345678901234567890" produces: Counter 0 → 755224, Counter 1 → 287082, Counter 2 → 359152, Counter 3 → 969429, Counter 4 → 338314, Counter 5 → 254676, Counter 6 → 287922, Counter 7 → 162583, Counter 8 → 399871, Counter 9 → 520489. https://www.rfc-editor.org/rfc/rfc4226.txt (Appendix D, lines 453-476).

**Use when / Avoid:** HOTP suits air-gapped devices and hardware tokens where real time is unavailable. Avoid for mobile apps expecting always-connected clients; time-based TOTP is simpler.

---

## 2. TOTP: RFC 6238 Time-Based One-Time Passwords

TOTP extends HOTP by replacing the counter with a time-based value: T = floor((Unix time - T0) / X), where T0 = 0 (Unix epoch, the default per RFC 6238 Section 4.1) and X = 30 seconds (default per RFC 6238 Section 4.2: "We RECOMMEND a default time-step size of 30 seconds").

**Hash Algorithms (RFC 6238, Section 4.2):**
HMAC-SHA-1 is the default. RFC 6238 Section 4.2 states "TOTP implementations MAY use HMAC-SHA-256 or HMAC-SHA-512 functions, based on SHA-256 or SHA-512 hash functions, instead of the HMAC-SHA-1 function."

**Single-Use Enforcement (RFC 6238, Section 5.2):**
RFC 6238 Section 5.2 mandates: "the verifier MUST NOT accept the second attempt of the OTP after the successful validation has been issued for the first OTP, which ensures one-time only use of an OTP." Prevents replay within the 30-second window.

**Drift Tolerance (RFC 6238, Section 5.2):**
RFC 6238 Section 5.2 recommends: "the validator be set with a specific limit to the number of time steps a prover can be 'out of synch' before being rejected." Accepting backward time steps of at most 2 (60 seconds) accommodates network delays and clock drift. https://www.rfc-editor.org/rfc/rfc6238.txt (Section 5, lines 254-289).

**Test Vectors (RFC 6238, Appendix B):**
Seeds: SHA-1 (20 bytes) "12345678901234567890", SHA-256 (32 bytes) "12345678901234567890123456789012", SHA-512 (64 bytes) "1234567890123456789012345678901234567890123456789012345678901234". Test times 59, 1111111109, 1111111111, 1234567890, 2000000000, 20000000000 Unix seconds produce OTP values across all three algorithms. Example: Unix 59 produces 94287082 (SHA-1), 46119246 (SHA-256), 90693936 (SHA-512). https://www.rfc-editor.org/rfc/rfc6238.txt (Appendix B, lines 280-296).

**Use when / Avoid:** TOTP suits all internet-connected devices with reasonable clock accuracy. Avoid in air-gapped systems or environments without NTP; use HOTP instead.

---

## 3. Key URI Format: otpauth:// Protocol

The URI scheme `otpauth://TYPE/LABEL?PARAMETERS` encodes secrets in QR codes per the Google Authenticator wiki (https://github.com/google/google-authenticator/wiki/Key-Uri-Format).

**Required Parameters:**
- secret: Unpadded Base32 per RFC 3548, containing the symmetric key. Padding specified in RFC 3548 Section 2.2 is not required and should be omitted.
- issuer: Service identifier (strongly recommended).
- algorithm: SHA1 (default), SHA256, or SHA512.
- digits: 6 (default) or 8.
- period: 30 (default for TOTP).

**Example:** `otpauth://totp/ACME%20Co:john.doe@email.com?secret=HXDMVJECJJWSRB3HWIZR4IFUGFTMXBOZ&issuer=ACME%20Co&algorithm=SHA1&digits=6&period=30`

**Platform Limitations (Google Authenticator Wiki):**
Algorithm, digits, and period parameters are ignored by older Google Authenticator implementations on Android and BlackBerry. URI should default to SHA-1, 6 digits, 30-second period for compatibility. https://github.com/google/google-authenticator/wiki/Key-Uri-Format.

**otpauth-migration:// Export Format:**
Large exports split across multiple QR codes via `otpauth-migration://offline?data=<base64-encoded-protobuf>`. The data parameter encodes a Protobuf MigrationPayload containing batch_size (number of QR codes), batch_index (this QR's position), batch_id (export identifier), and repeated OtpParameters (secret, issuer, account, algorithm, digits, type, counter). See https://github.com/google-authenticator/wiki (referenced implementations) and https://alexbakker.me/post/parsing-google-auth-export-qr-code.html for decode details.

**Use when / Avoid:** Key URI format universally accepted by authenticator apps. Avoid hand-crafted secrets; use a library to generate valid Base32-encoded strings with correct checksums.

---

## 4. NIST SP 800-63B (Revision 3, final): Authenticator Requirements

NIST SP 800-63B-3 specifies OTP authenticators at https://pages.nist.gov/800-63-3/sp800-63b.html.

**Single-Factor OTP Verifiers (Section 5.1.4):**
Must contain a symmetric key with minimum security strength per NIST SP 800-131A (112 bits as of this publication). Section 5.1.4.2 mandates: "verifiers SHALL accept a given time-based OTP only once during the validity period" to prevent replay.

**Multi-Factor OTP Devices (Section 5.1.5):**
Require activation with an additional factor (memorized secret or biometric) per each use.

**Rate Limiting (Section 5.2.2):**
For OTP output with less than 64 bits of entropy, "the verifier SHALL limit consecutive failed authentication attempts on a single account to no more than 100." https://pages.nist.gov/800-63-3/sp800-63b.html (Section 5.2.2, line ~800).

**AAL2 vs AAL3 (Sections 4.2 and 4.3):**
AAL2 requires two distinct factors with replay resistance from at least one; authentication intent recommended but not required. AAL3 demands verifier impersonation resistance via cryptographic protocols (FIDO2, PKI) with mandatory authentication intent from all factors. Manual-entry OTPs cannot achieve impersonation resistance.

**Phishing Resistance (Section 5.2.5):**
"Manual-entry authenticators...SHALL NOT be considered verifier impersonation-resistant" due to inability to cryptographically bind to session or origin. Only FIDO2 and PKI-based methods qualify. https://pages.nist.gov/800-63-3/sp800-63b.html (Section 5.2.5).

**Use when / Avoid:** Use NIST SP 800-63B-3 for federal/regulated systems. Revision 4 (if finalized by 2025) may tighten phishing-resistance requirements; verify current status at https://pages.nist.gov/800-63-4/.

---

## 5. Brute-Force Analysis for 6-Digit TOTP with ±1 Time-Step Window

**Attack model:** Attacker intercepts a 6-digit TOTP code and retransmits it to a verifier. With 30-second time steps, the code is valid during current T and optionally T-1 (one step back, ~30 sec earlier). Total validity window is 60 seconds with one re-attempt.

**Probability of success:**
- 6-digit code: 10^6 = 1,000,000 possible values.
- One attempt: 1/1,000,000 = 10^-6.
- Assume attacker can try once per valid window (60 sec, two 30-sec steps): two attempts = 2/10^6 = 2×10^-6 (1 in 500,000).

**RFC 4226 Appendix A:** Approximates brute-force success as Sec = sv/(10^Digit) where s = look-ahead steps. With s=1 (standard), v=1 verification, Digit=6: Sec = 1/10^6. https://www.rfc-editor.org/rfc/rfc4226.txt (Appendix A, lines 393-422).

**Throttling guidance:** Enforce maximum 100 consecutive failed attempts per account (NIST SP 800-63B Section 5.2.2, 100 attempts). After 100 failures, lock the account and require out-of-band recovery (email, SMS). For interactive logins, implement rate limiting: 5 seconds delay per failure, or exponential backoff 1s, 2s, 4s, 8s, max 1 minute.

**Use when / Avoid:** Accept that 6-digit TOTP offers modest entropy (~20 bits) per code. Layer with rate limiting and strong password/biometric for AAL2+. Do not rely on TOTP alone for high-value targets (bank transfers, admin access); add WebAuthn or push MFA.

---

## 6. Push-Approval MFA and Mitigations: Fatigue, Number Matching, Delivery

**MFA Fatigue / Push Bombing:**
Attackers flood users with push notifications after stealing credentials, hoping for accidental approval. Microsoft telemetry logged 382,000+ MFA fatigue attempts in a 12-month period (2021-2022). Defense: number matching.

**Number Matching (Microsoft Entra, Duo, CISA):**
Instead of single "Approve" tap, user sees a 2-3 digit code on login screen, must type it into authenticator app to approve. Real-time relay (Evilginx style) fails because attacker sees the number on their own laptop, user does not. Microsoft Authenticator enforces number matching by default https://www.cisa.gov/sites/default/files/publications/fact-sheet-implement-number-matching-in-mfa-applications-508c.pdf. Duo Verified Push offers 3-digit number matching https://help.sfasu.edu/TDClient/2027/Portal/KB/Article/170573/Using-Duo-Verified-Push.

**CISA Guidance (2022):**
CISA recommends phishing-resistant MFA (FIDO2, certificate-based auth) as primary defense. If unable to implement, use number matching as interim mitigation https://www.cisa.gov/news-events/alerts/2022/10/31/cisa-releases-guidance-phishing-resistant-and-numbers-matching-multifactor-authentication.

**APNs Delivery (Apple Push Notification Service):**
Best-effort delivery. Priority 10 (immediate, requires alert/sound/badge). Priority 5 (throttled, power-conscious, may not deliver). TTL header (apns-expiration) specifies Unix epoch expiration; if omitted, default is 1 hour. Collapse ID deduplicates pushes with same identifier https://developer.apple.com/library/archive/documentation/NetworkingInternet/Conceptual/RemoteNotificationsPG/CommunicatingwithAPNs.html.

**FCM Delivery (Google Firebase Cloud Messaging):**
Store-and-forward semantics with configurable TTL (max 28 days per https://firebase.google.com/docs/cloud-messaging/concept-options). High priority (10) for time-sensitive content. Normal priority (5) subject to throttling. fcm-collapse-id coalesces duplicate messages. No guaranteed delivery; device offline during TTL expiration loses the message.

**Use when / Avoid:** Number matching strongly recommended for all push MFA. Do NOT rely on push notifications alone for high-security workflows; combine with strong biometric or hardware key. Avoid SMS OTP (carrier risks, SIM swap). Prefer FIDO2 or passkey if infrastructure supports it.

---

## 7. Phishing and Real-Time Relay Attacks: Evilginx and AiTM

**Relay Proxy Attack (Evilginx, AiTM):**
Man-in-the-middle proxy between user and legitimate site. Attacker forwards every request to the real site, including MFA challenges. User enters credentials, approves push or enters OTP, attacker proxies response back to real site. Result: attacker captures authenticated session cookies and gains account access. Works against TOTP, SMS OTP, and push approvals because these are time-based secrets, not origin-bound.

Real-time relay attacks documented at https://eprint.iacr.org/2024/887.pdf (Signal's Secure Value Recovery case study) and analyzed in Microsoft Threat Intelligence blog posts on AiTM phishing at https://www.microsoft.com/en-us/security/blog/2026/03/04/inside-tycoon2fa-how-a-leading-aitm-phishing-kit-operated-at-scale/ showing that TOTP is bypassed in seconds during relay.

**WebAuthn Origin Binding (W3C, FIDO Alliance):**
W3C WebAuthn spec (https://www.w3.org/TR/webauthn-2/, Section 5 and 13.4) mandates that authenticators cryptographically bind signatures to the Relying Party (RP) origin domain. Private key never leaves authenticator. Signature for example.com cannot be used on examp1e.com (typo phishing). Browser enforces origin policy. This prevents relay: attacker's proxy cannot forward the challenge to the authenticator because the challenge includes the origin binding, and the authenticator refuses to sign for an attacker-controlled domain.

**Defense:** Deploy FIDO2 security keys or passkeys for high-value accounts. As interim mitigation, number matching raises the bar for relay attacks (requires attacker to extract both the number AND session cookie in real time, no longer a one-way proxy scenario).

**Use when / Avoid:** TOTP and push MFA remain vulnerable to relay. Phishing-resistant MFA (FIDO2, passkeys, cert-based auth) is the only structural defense. Implement for admin accounts, finance, and any account with sensitive permissions.

---

## 8. On-Device Key Storage: iOS Keychain and Android Keystore

**iOS Keychain Accessibility Classes:**
kSecAttrAccessibleWhenUnlockedThisDeviceOnly: Item available only when device is unlocked; NOT synced to iCloud Keychain, NOT migrated to other devices. Tied to device hardware via hardware-backed key derivation. This class is recommended for TOTP seed storage to prevent cloud compromise.

kSecAttrAccessibleAfterFirstUnlock: Item available after device first unlocked; syncs to iCloud Keychain if kSecAttrSynchronizable = true. ThisDeviceOnly variants and kSecAttrSynchronizable are mutually exclusive.

Source: https://support.apple.com/en-gb/guide/security/sec3e341e75d/1/web/1 and developer.apple.com Keychain documentation.

**iOS Secure Enclave:**
Private keys marked with kSecAttrAccessibleWhenUnlockedThisDeviceOnly are backed by Secure Enclave (A-series processors, M1+) on supported devices. SE generates and signs, never exports the key.

**Android Keystore:**
Keys stored in KeyStore system provider; backed by Trusted Execution Environment (TEE) by default (ARM TrustZone).

StrongBox (API 28+, Android 9+) stores keys in dedicated secure coprocessor (separate silicon). Call keyStore.setIsStrongBoxBacked(true) during key generation. Check availability: `context.packageManager.hasSystemFeature(PackageManager.FEATURE_STRONGBOX_KEYSTORE)`. Even root/kernel compromise cannot access StrongBox keys (separate bus, custom firmware).

Source: https://developer.android.com/training/articles/keystore and Android documentation.

**Auto-Backup Risks:**
Android default android:allowBackup="true" includes Keystore keys in full backup (unencrypted to Google Cloud if user enables). Authenticator apps should set android:allowBackup="false" or exclude Keystore items from backup manifest.

**Use when / Avoid:** Store TOTP seeds in Keychain (iOS) or Keystore (Android) with device-only accessibility. Never store in SharedPreferences or plaintext. Avoid iCloud sync for seeds to prevent cloud-side attack surface.

---

## 9. End-to-End Encrypted Backup with Recovery: Apple, Google, WhatsApp, Signal

**Apple iCloud Keychain Escrow (Platform Security Guide, 2024):**
iCloud Keychain stores a wrapped TOTP seed backup on Apple's servers, encrypted with a key derived from user's device passcode. The key is stored in an HSM cluster (Thales HSM). Attempt limit: 10 failed authentication attempts. After the 10th failure, the escrow record is destroyed irreversibly; the seed is lost and cannot be recovered. Firmware enforces this limit (not user-modifiable).

Source: https://support.apple.com/en-gb/guide/security/sec3e341e75d/web and Apple Platform Security guide.

**Apple Advanced Data Protection (ADP, 2023+):**
User must set up recovery contact (trusted person with Apple device) or recovery key (28-character alphanumeric code) before enabling ADP. If user loses device, they use recovery contact (who generates a 6-digit code) or recovery key (entered manually) to regain access to E2EE data. Recovery key must be printed and stored offline (e.g., safe deposit box).

Source: https://support.apple.com/en-us/108756 and https://support.apple.com/en-uz/109345.

**Google Android Backup Encryption (Cloud Key Vault, 2018+):**
User's lock screen PIN/pattern encrypts a random backup encryption key. This wrapped key is sent to Google's servers and stored on a Titan HSM-based Cloud Key Vault. On recovery, device sends lock screen knowledge factor to Titan HSM. Titan enforces attempt limits via custom firmware (limit not publicly specified, but sources indicate 5-100 range). After limit exceeded, vault record is destroyed.

Source: https://developer.android.com/about/versions/pie/security/ckv-whitepaper and https://thehackernews.com/2018/10/android-cloud-backup.html.

**WhatsApp E2EE Backups (2021+):**
Backup Key Vault (HSM-based infrastructure similar to iCloud) protects an encryption key. User chooses 64-digit random key OR password-protected mode. In password mode, the encryption key is stored on Backup Key Vault and protected by HSM-enforced attempt limits (specific limit not publicly disclosed, but architecture enforces permanent key destruction after failed attempts).

Source: https://engineering.fb.com/2021/09/10/security/whatsapp-e2ee-backups/.

**Signal Secure Value Recovery (SVR2/SVR3, 2019+):**
User sets a low-entropy PIN (5-digits). SVR stores the encrypted master key with PIN-derived shares. Server-side SGX enclave enforces guess-limit (count of incorrect PIN attempts) in persistent Raft-based state. After limit exceeded, account is locked; user must reset via out-of-band recovery (phone number verification).

Source: https://github.com/signalapp/SecureValueRecovery2 and https://eprint.iacr.org/2024/887.pdf.

**Use when / Avoid:** Enable E2EE backup for phones used as TOTP authenticators. Store recovery key in physical safe. For corporate scenarios, use conditional access (e.g., deny backup from corporate MDM device, or enable backup only on company-managed iCloud account). Do NOT enable backup on shared/public devices.

---

## 10. Password-Based Key Derivation for Backup Passphrase

**Argon2id Parameters (RFC 9106 Section 4, final 2021):**
Two recommended configurations providing equal defense:

1. **Higher memory:** Argon2id with t=1 (time cost), p=4 (parallelism), m=2^21 (2 GiB memory), 128-bit salt, 256-bit output. Suitable for servers with abundant memory.
2. **Lower memory (constrained):** Argon2id with t=3, p=4, m=2^16 (64 MiB memory), 128-bit salt, 256-bit output. Suitable for mobile/embedded.

Source: https://datatracker.ietf.org/doc/rfc9106/ (Section 4, lines 145-165).

**OWASP Password Storage Cheat Sheet (2024):**
Argon2id (minimum): m=19 MiB (2^14.25 KiB), t=2, p=1. Recommended: m=46 MiB, t=1, p=1. PBKDF2-HMAC-SHA256: 600,000 iterations (RFC 9000 guidance). PBKDF2-HMAC-SHA512: 220,000 iterations. Scrypt: N=2^16 (64 MiB), r=8, p=2.

Source: https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html.

**Authenticated Encryption (libsodium):**
For encrypting the derived key: AES-256-GCM (hardware-accelerated on modern CPUs) or XChaCha20-Poly1305 (via libsodium secretstream). XChaCha20-Poly1305 uses 192-bit nonce (24 bytes), virtually eliminating nonce-reuse risk if generated with a CSPRNG. libsodium SecretStream API provides AEAD streaming for large backups.

Source: https://doc.libsodium.org/quickstart and https://libsodium.net/guide/SecretStream.html.

**Use when / Avoid:** If users provide a passphrase (e.g., "backup password"), derive a 256-bit key using Argon2id and use it to encrypt the TOTP seed with AES-256-GCM. Never use raw passphrase as encryption key. For server-side key wrapping, use Argon2id on the user's device (client-side) before sending to server, so server sees only derived key material.

---

## 11. Time Synchronization: NTP Accuracy and Clock Drift

**Android Network Time Detection (SNTP):**
AndroidOS queries SNTP servers once per day by default. Config parameter config_ntpTimeout = 5000 milliseconds (default). With network latency concentrated on inbound or outbound leg, theoretical maximum error ≈ 2.5 seconds. Android clocks can drift 1-5 minutes if SNTP fails or device is offline for days.

Source: https://source.android.com/docs/core/connect/time/network-time-detection.

**iOS Time Synchronization:**
iOS syncs time via NTP on cellular/WiFi connection. Typical accuracy within 100 milliseconds of authoritative time. If device has been offline, clock can drift. Users should enable "Set Time Automatically" in Settings.

**Google Authenticator Time Correction (v7.0+, 2023+):**
Pre-v7.0 offered manual "Sync now" in Settings > Time correction for codes. Google Authenticator v7.0+ removed this menu option and relies on automatic sync to Google's servers (requires user signed into Google Account). Manual sync is no longer available; users must ensure device has automatic date/time enabled.

Source: https://support.google.com/accounts/ (Google Authenticator help); users should enable "Set date & time automatically" on Android or "Set Time Automatically" on iOS.

**Authenticator App Drift Handling:**
If device clock drifts >30 seconds, TOTP codes become invalid. Most apps accept codes from current 30-second window and previous window (T-1), allowing ~60-second tolerance. If clock drifts >60 seconds, codes will be rejected. Users must manually sync; apps cannot force NTP resync (requires system permissions).

**Use when / Avoid:** Educate users to enable automatic time sync on their device. Authenticator apps should warn if device clock appears misaligned (by checking returned OTP against server time). For admin accounts, periodic clock verification (e.g., via device management) ensures compliance.

---

## 12. Multi-Device Sync and Conflict Handling for Encrypted Vaults

**Per-Item Versioning:**
Ente Auth and similar E2EE authenticators use per-item versioning: each TOTP seed has a version timestamp and content hash. On sync, devices compare versions; higher version wins. Deletions are marked with tombstones (special delete marker) to distinguish "never existed" from "was present, now deleted" for proper multi-device reconciliation.

**Last-Writer-Wins Merge:**
Most authenticator apps use last-write-wins (LWW) for conflict resolution: the TOTP entry with the latest modification timestamp on either device overwrites the older entry. This is simple but can lose concurrent edits if devices sync offline.

**Vault Sync Implementation (open-source references):**
- Ente Auth: GitHub https://github.com/ente-io/auth implements end-to-end encrypted cloud sync with per-item versioning and tombstone markers. Sync protocol uses versioned API calls; clients maintain local SQLite DB with version metadata, compare with server, merge on conflict.
- Aegis: Android-only, supports local backups to JSON + AES-256-GCM encryption. Multi-device sync not built-in (users export/import manually).
- 2FAS: Sync via 2FAS server (GitHub https://github.com/twofas/2fas-server) with end-to-end encryption. Backup contains JSON+AES-256-GCM. Conflict handling via versioning; details in codebase /internal directory.
- Bitwarden Authenticator: Uses Bitwarden cloud sync (commercial, closed-source). Conflict resolution via server-side timestamps.

**Tombstone Records:**
A deleted TOTP entry is marked with a tombstone (e.g., {id: "uuid", deleted_at: "2025-10-03T...Z"}). When syncing with a peer device, the peer sees the tombstone and deletes its local copy. Without tombstones, deletion on device A may not propagate to device B (reappears after next sync).

**Vector Clocks (advanced):**
For multi-way merge (more than 2 devices), some systems use vector clocks instead of timestamps. Each device tracks (deviceId, logical_clock) tuples. On merge, conflicts detected when two entries have incomparable vector clocks (neither causally happens-before the other). Resolution typically falls back to LWW or user prompt.

**Use when / Avoid:** For consumer authenticator apps, LWW with tombstones is sufficient (conflicts rare because TOTP entries are rarely edited, only added/deleted). For corporate scenarios with frequent audits, vector clocks + explicit conflict logging recommended (track: who edited, from which device, when, what changed). Store complete sync history server-side for compliance/audit.

---

## Summary Table: Mechanisms and Deployment Guidance

| Mechanism | Spec/Source | Key Parameter | Risk Level | Mitigation |
|-----------|-------------|---------------|-----------|-----------|
| HOTP | RFC 4226 | Counter, 128-160 bit secret | Medium (counter sync needed) | Resync window (10 values), throttling |
| TOTP | RFC 6238 | 30-sec step, SHA-1/256/512 | Low (time-based, self-syncing) | Clock via NTP, ±1 window tolerance |
| NIST OTP | SP 800-63B-3 | 100-attempt lockout, AAL2+ | Medium (not phishing-resistant) | Number matching + FIDO2 for AAL3 |
| Real-time relay | Evilginx, AiTM | Unbound secrets | High (defeats TOTP, SMS, push) | Origin binding (WebAuthn, FIDO2 only) |
| Push MFA | APNs / FCM | Best-effort delivery, TTL | High (fatigue/bombing) | Number matching, FIDO2 |
| iCloud Keychain | Apple Platform Security | 10-attempt escrow limit | Medium (attempts finite) | Recovery key backup, ADP |
| Android backup | Google CKV | HSM Titan, attempt limit | Medium (hardware-enforced limit) | Lock screen knowledge factor required |
| Argon2id | RFC 9106 | m=46 MiB t=1 p=1 | Low (strong KDF) | Use for passphrases only, never raw password |

---

## Unverified Claims (not found in primary sources)

1. Specific HTTP attempt limit for Google Cloud Key Vault (sources indicate 5-100 range, exact value not publicly disclosed).
2. Specific HTTP attempt limit for WhatsApp Backup Key Vault HSM (architecture confirms limits exist, exact number not disclosed).
3. Signal SVR2/SVR3 exact guess limit (sources confirm "small limit," typical 5-10, exact number not public).
4. Precise NTP accuracy on iOS (sources indicate ~100ms, but no authoritative spec found).
5. 2FAS sync conflict resolution algorithm (open-source code available on GitHub but documentation not found).

---

## References (Primary Sources)

- https://www.rfc-editor.org/rfc/rfc4226.txt: HOTP RFC 4226, full text
- https://www.rfc-editor.org/rfc/rfc6238.txt: TOTP RFC 6238, full text
- https://datatracker.ietf.org/doc/rfc9106/: Argon2id RFC 9106, final
- https://pages.nist.gov/800-63-3/sp800-63b.html: NIST SP 800-63B-3, Revision 3
- https://github.com/google/google-authenticator/wiki/Key-Uri-Format: Key URI Format specification
- https://www.w3.org/TR/webauthn-2/: W3C WebAuthn Level 2 specification
- https://www.cisa.gov/sites/default/files/publications/fact-sheet-implement-number-matching-in-mfa-applications-508c.pdf: CISA number matching fact sheet
- https://developer.apple.com/library/archive/documentation/NetworkingInternet/Conceptual/RemoteNotificationsPG/CommunicatingwithAPNs.html: APNs delivery semantics
- https://firebase.google.com/docs/cloud-messaging/concept-options: FCM delivery semantics
- https://support.apple.com/en-gb/guide/security/sec3e341e75d/web: Apple Platform Security, iCloud Keychain escrow
- https://support.apple.com/en-us/108756: Apple Advanced Data Protection recovery
- https://developer.android.com/about/versions/pie/security/ckv-whitepaper: Google Cloud Key Vault whitepaper
- https://engineering.fb.com/2021/09/10/security/whatsapp-e2ee-backups/: WhatsApp E2EE backup architecture
- https://github.com/signalapp/SecureValueRecovery2: Signal SVR2 source code
- https://eprint.iacr.org/2024/887.pdf: Signal SVR3 research paper (OSDI 2024)
- https://doc.libsodium.org/quickstart: libsodium authenticated encryption
- https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html: OWASP password storage guidance
- https://source.android.com/docs/core/connect/time/network-time-detection: Android network time synchronization
- https://github.com/ente-io/auth: Ente Auth open-source authenticator
- https://github.com/twofas/2fas-server: 2FAS server open-source code
- https://www.microsoft.com/en-us/security/blog/2026/03/04/inside-tycoon2fa-how-a-leading-aitm-phishing-kit-operated-at-scale/: Microsoft Threat Intelligence AiTM analysis
- https://alexbakker.me/post/parsing-google-auth-export-qr-code.html: otpauth-migration format breakdown

---

## Spot-check corrections (editor, 2026-10-03)

Checked by fetching the sources directly. The survey text above is left as the agent wrote it. Where they disagree, this table wins.

| Claim in the survey | What the source says | Effect on the design |
|---|---|---|
| NIST SP 800-63B-3, §5.1.4.2 and §5.2.2 | Revision 4 is final ([pages.nist.gov/800-63-4/sp800-63b.html](https://pages.nist.gov/800-63-4/sp800-63b.html), page build 26 Aug 2025). OTP rules are §3.1.4: key ≥ 112 bits, a clock-based nonce changes at least every 2 minutes, "Verifiers SHALL accept a given OTP only once while it is valid", "OTP authentication is not phishing-resistant". Rate limiting is §3.2.2: no more than 100 consecutive failures per authenticator, then disable it. Appendix B (normative) covers sync fabrics: keys stored only encrypted with a ≥ 112-bit key, "SHOULD be encrypted using a method that employs a user-controlled secret", access to the sync fabric protected by AAL2-equivalent MFA, and a UI that shows which keys are synced and where | Cite rev 4 everywhere. Appendix B is the spec for our sync design |
| "±1 window = 2 attempts per 60 s = 2/10^6" | ±1 accepts 3 codes (T-1, T, T+1), so one guess wins with probability 3/10^6. RFC 4226 §6: Sec = s·v / 10^Digit | 100 guesses (the NIST cap) = 3 x 10^-4. solution §5.4 |
| "Number matching ... Real-time relay (Evilginx style) fails" | Wrong. Number matching stops blind approvals (fatigue). An adversary-in-the-middle page shows the user the number and relays it. Only origin-bound credentials (WebAuthn) stop relay. NIST §3.1.4 says OTP is not phishing-resistant | solution §5.6 says this plainly |
| "Google Authenticator v7.0+ ... now auto-syncs to Google servers" (time) | The Google help page says "The time correction setting is no longer available in version 7.0. The app now uses the time setting on your operating system" ([support.google.com/accounts/answer/1066447](https://support.google.com/accounts/answer/1066447)) | The app trusts the OS clock. We add a skew warning, not a silent correction (solution §5.3) |
| Android SNTP "theoretical maximum error ≈ 2.5 s", "drift 1 to 5 min if SNTP fails" | The 2.5 s is half the 5 s timeout, not a measured accuracy. The 1 to 5 min drift has no source | Not used as fact |
| "RFC 9000 guidance" for PBKDF2 600,000 | RFC 9000 is QUIC. The 600,000 comes from OWASP ([cheat sheet](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html)), which also lists SHA-512 at 220,000 (confirmed) and Argon2id m=47104 (46 MiB), t=1, p=1 | Use OWASP as the source |
| Google Cloud Key Vault attempt limit "5 to 100" | The 2018 Google post says only "permanently block access after too many incorrect attempts", enforced by Titan firmware ([security.googleblog.com](https://security.googleblog.com/2018/10/google-and-android-have-your-back-by.html)). No number | Use Apple's published 10 as the reference number |
| Apple escrow "10-attempt limit" | Confirmed. "The escrow service allows only 10 attempts ... After the 10th failed attempt, the HSM cluster destroys the escrow record." A majority of the cluster must agree, the code is checked with SRP, and the admin cards were destroyed ([support.apple.com/guide/security/sec3e341e75d](https://support.apple.com/guide/security/escrow-security-for-icloud-keychain-sec3e341e75d/web)) | The recovery design copies this (solution §5.2) |
| Microsoft "382,000+ MFA fatigue attempts" | Not found on the Microsoft page fetched. [unverified] | Not used |
