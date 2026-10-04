# Real-World 2FA and Authenticator Architectures: A Survey

Research compiled from primary sources: company blogs, security whitepapers, incident reports, GitHub repositories, and official documentation. Updated October 2026.

---

## 1. Google Authenticator

### Open-Source History

Google Authenticator Android repository was archived on April 6, 2021 ([github.com/google/google-authenticator-android](https://github.com/google/google-authenticator-android)). The archived README states: "the application is no longer actively maintained" and the open source version "is not an officially supported Google product with no guarantees of continued upstream changes." The official Play Store app has remained proprietary.

### Cloud Sync Launch and Encryption

Google Authenticator's cloud sync feature encrypts codes both in transit and at rest ([support.google.com/accounts/answer/1066447](https://support.google.com/accounts/answer/1066447)). Codes are synced to a user's Google Account and synchronized across all their devices, but the encryption model used, whether end-to-end or server-side encryption, is not specified in official documentation.

The sync feature requires version 6.0+ on Android or 4.0+ on iOS. When a user signs into their Google Account on a new device, codes are automatically synced.

### Transfer Accounts QR Export

Authenticator supports manual QR code export via Menu > Transfer accounts > Export accounts. Users select accounts to transfer, and the app generates one or more QR codes. On a new device, Menu > Transfer accounts > Import accounts scans the QR codes to import ([support.google.com/accounts/answer/1066447](https://support.google.com/accounts/answer/1066447)).

### Time Correction Feature Removal

Version 7.0 removed the manual time correction setting. The app now relies on the device's operating system time, simplifying configuration ([support.google.com/accounts/answer/1066447](https://support.google.com/accounts/answer/1066447)).

### Install Count

Google Authenticator has over 100 million downloads on the Play Store ([play.google.com/store/apps/details?id=com.google.android.apps.authenticator2](https://play.google.com/store/apps/details?id=com.google.android.apps.authenticator2)).

### E2EE Status

As of October 2026, Google's official support pages do not explicitly state that cloud sync uses end-to-end encryption. The Mysk criticism (February 2023) highlighted the lack of E2EE in sync, but Christiaan Brand's response and any subsequent E2EE implementation are not documented in the current Help Center ([support.google.com/accounts/answer/1066447](https://support.google.com/accounts/answer/1066447)).

---

## 2. Authy (Twilio)

### Encrypted Backups Architecture

Authy's backups use zero-knowledge encryption where encryption and decryption occur only on the user's device, never in Authy's cloud ([www.twilio.com/en-us/blog/how-the-authy-two-factor-backups-work](https://www.twilio.com/en-us/blog/how-the-authy-two-factor-backups-work)).

**Key Derivation:** Password is salted with a secure random value and processed through PBKDF2 with **100,000 rounds**. The implementation uses NIST-recommended PBKDF2 as the underlying key derivation function.

**Encryption Algorithm:** AES-256 in CBC mode, with a unique initialization vector (IV) for each account. Keys shorter than 128 bits are padded using PKCS#5.

**Data Transmission:** Only the encrypted result, salt, and IV are sent to Authy's servers. The encryption/decryption key is never transmitted, implementing true zero-knowledge architecture.

### Multi-Device Feature

Multi-device is controlled via Settings > Devices > "Allow Multi-Device." When enabled, users can install Authy on new devices and add them to their account. When disabled, no new instances can be added, though existing devices remain active ([www.twilio.com/en-us/blog/products/understanding-authys-multi-device-feature](https://www.twilio.com/en-us/blog/products/understanding-authys-multi-device-feature)).

New devices authenticate via SMS/voice or by using an already-trusted device's approval ("inherited trust"). Authy recommends enabling multi-device on at least two devices for backup, then disabling it to reduce attack surface.

For crypto users (Coinbase, Gemini), SMS/voice authentication is disabled, requiring device-based approval instead. Users who lose their phone with multi-device disabled face a **24-hour account recovery wait period**.

### July 2024 Security Incident

On July 1, 2024, Twilio disclosed that an unauthenticated endpoint allowed threat actors to identify phone numbers associated with Authy accounts ([www.twilio.com/en-us/changelog/Security_Alert_Authy_App_Android_iOS](https://www.twilio.com/en-us/changelog/Security_Alert_Authy_App_Android_iOS)). The attacker did not obtain a bulk phone number list; instead, they tested millions of phone numbers using multiple IP addresses to enumerate which were associated with Authy accounts. The endpoint is used exclusively by the Authy app during device registration and not by business customers. No evidence of system breach or MFA code compromise was found.

### Desktop Apps End of Life

[Information not located in primary sources; marked as unverified].

### User Count

Authy serves millions of users across customers including Twitch, Coinbase, and SendGrid. As of November 2022, Twilio deprecated the Authy SMS/Voice API and closed it to new customers, migrating services to the Twilio Verify API ([www.twilio.com/authy](https://www.twilio.com/authy)).

---

## 3. Microsoft Authenticator

### Cloud Backup and Restore

On iOS, Microsoft Authenticator encrypts backup data with the user's personal Microsoft account and stores it in iCloud. Account backup and restore works only on the same device type (iOS backup cannot restore to Android). Recovery occurs automatically when the app is freshly installed and signed into a new device of the same platform ([support.microsoft.com/en-us/account-billing/restore-account-credentials-from-microsoft-authenticator](https://support.microsoft.com/en-us/account-billing/restore-account-credentials-from-microsoft-authenticator)).

Push notifications for cloud-restored accounts work only for Microsoft personal, work, or school accounts. Third-party accounts (Google, Facebook) do not receive push notifications after restore.

### Push Notifications with Number Matching

Number matching is enabled by default for all Microsoft Authenticator push notifications ([learn.microsoft.com/en-us/entra/identity/authentication/how-to-mfa-number-match](https://learn.microsoft.com/en-us/entra/identity/authentication/how-to-mfa-number-match)). When a user responds to an MFA push notification, a number appears on both the sign-in screen and the Authenticator notification. The user must enter that number in Authenticator to complete approval. Number matching is supported for MFA, self-service password reset (SSPR), combined SSPR and MFA registration, AD FS adapter, and NPS extension. **Users cannot opt out of number matching.**

On the same device, iOS and Android users can reply Yes/No instead of entering the number when signing into Microsoft mobile apps like Authenticator, Teams, or Outlook (web and browsers still require entering the number).

**Enforcement Date:** Number matching enforcement for Entra ID admin center began October 15, 2024 ([learn.microsoft.com/en-us/entra/identity/authentication/concept-mandatory-multifactor-authentication](https://learn.microsoft.com/en-us/entra/identity/authentication/concept-mandatory-multifactor-authentication)).

### Passwordless Phone Sign-In

Microsoft Authenticator supports passwordless phone sign-in, allowing users to approve sign-in requests directly from the app instead of entering passwords.

---

## 4. Duo (Cisco)

### Push Architecture and Verified Push

Duo Push sends authentication requests to a mobile device. Verified Push adds a second factor by requiring users to enter a numeric code displayed in the Duo Prompt on the authentication device into the Duo Mobile app, confirming that the user initiating sign-in is the same person approving it ([duo.com/docs/authentication-methods-security-guide](https://duo.com/docs/authentication-methods-security-guide)). This mitigates MFA fatigue and push harassment attacks.

### Mobile Restore

Duo Restore for third-party accounts provides encrypted restoration of authenticator accounts to new devices (encryption details not specified in public documentation).

### Scale

Duo Security processes **1.3 billion monthly authentications**, translating to approximately 40+ million authentications per day ([duo.com/resources/ebooks/2024-duo-trusted-access-report](https://duo.com/resources/ebooks/2024-duo-trusted-access-report)). The 2024 Duo Trusted Access Report analyzed over 16 billion authentications. Duo serves over 40,000 customers globally across 100+ countries.

---

## 5. Okta Verify and Twilio Verify TOTP API

### Server-Side TOTP Verification

Twilio Verify TOTP API implements RFC-6238 time-based one-time passwords. A Factor of type `totp` contains the seed (secret) used to generate codes. Verification is initiated by creating a Challenge with the TOTP code as the `authPayload` (3 to 8 characters) ([www.twilio.com/docs/verify/totp/technical-overview](https://www.twilio.com/docs/verify/totp/technical-overview)).

**Rate Limits and Window Parameters:**
- Challenge verification attempts: maximum 5 attempts per Challenge for TOTP ([www.twilio.com/docs/api/errors/60308](https://www.twilio.com/docs/api/errors/60308))
- TOTP Code Time-To-Live: **300 seconds** (5 minutes), hard-coded and not configurable ([support.okta.com/help/s/article/okta-verify-totp-code-time-to-live](https://support.okta.com/help/s/article/okta-verify-totp-code-time-to-live))
- Status check rate limits: 60 requests/minute, 180 requests/hour, 250 requests/day
- Service rate limits: general limit of 1 request per 30 seconds per phone number with exponential backoff

**Okta Verify TOTP:** Okta Verify generates six-digit codes every 30 seconds. Clock drift tolerance can be configured: if drift interval is 3 and time step is 15 seconds, the server accepts codes 45 seconds before or after the user's entry ([developer.okta.com/docs/guides/authenticators-okta-verify/aspnet/main/](https://developer.okta.com/docs/guides/authenticators-okta-verify/aspnet/main/), [support.okta.com/help/s/article/offline-code-generation-protocol-in-okta-verify](https://support.okta.com/help/s/article/offline-code-generation-protocol-in-okta-verify)).

---

## 6. Password Managers with TOTP

### 1Password

1Password uses **Two-Secret Key Derivation (2SKD)** combining a user's master password with a machine-generated 128-bit Secret Key. The Secret Key is unique per account and never stored on 1Password's servers. Attackers need both the password and the Secret Key to decrypt vault data ([1password.com/blog/developers-how-we-use-srp-and-you-can-too](https://1password.com/blog/developers-how-we-use-srp-and-you-can-too), [support.1password.com/files/msp/1password-security.pdf](https://support.1password.com/files/msp/1password-security.pdf)).

1Password uses Secure Remote Password (SRP) as a password-authenticated key exchange (PAKE), allowing authentication without transmitting the master password over the network.

### Bitwarden

Bitwarden supports two key derivation functions ([bitwarden.com/help/kdf-algorithms/](https://bitwarden.com/help/kdf-algorithms/)):

**PBKDF2-SHA256:** Master password is salted with username and hashed via HMAC-SHA-256 with a default of **700,000 iterations** (configurable).

**Argon2id:** Winner of the 2015 Password Hashing Competition. Default settings: KDF memory 32 (MiB), KDF iterations 6, KDF parallelism 4. Argon2id resists both side-channel attacks and GPU cracking.

Bitwarden also offers a Bitwarden Authenticator app that generates TOTP codes for services supporting two-factor authentication, syncing via Bitwarden cloud.

### Apple Passwords

Apple's Passwords app stores verification codes for websites and apps that support two-factor authentication. Codes sync across all devices via iCloud Keychain with end-to-end encryption ([support.apple.com/en-us/120758](https://support.apple.com/en-us/120758)). Information stored in Passwords is encrypted on the device and cannot be viewed by Apple. All iCloud Keychain data is end-to-end encrypted ([support.apple.com/guide/security/icloud-keychain-security-overview-sec1c89c6f3b/web](https://support.apple.com/guide/security/icloud-keychain-security-overview-sec1c89c6f3b/web)).

---

## 7. Open-Source E2EE Authenticators

### Ente Auth

Ente Auth uses **XChaCha20-Poly1305** for encryption, **Argon2id** for key derivation, and **libsodium** (externally audited cryptographic library) for all primitives ([help.ente.io/auth/faq/](https://help.ente.io/auth/faq/)).

All data is encrypted end-to-end, including tags, type, account, issuer, notes, and pinned/trash status. Ente's servers have no visibility into encrypted content. For encrypted export (Ver 1), Ente uses Argon2id for key derivation and XChaCha20-Poly1305 for encryption.

Recovery is via a permanent **24-word recovery phrase**. Ente cannot provide or regenerate the recovery key due to end-to-end encryption ([ente.io/faq/security-and-privacy/forgot-password/](https://ente.io/faq/security-and-privacy/forgot-password/)).

### 2FAS

2FAS supports cloud backups to Google Drive and iCloud with end-to-end encryption ([2fas.com/support/2fas-auth-security-privacy/is-2fas-backup-safe/](https://2fas.com/support/2fas-auth-security-privacy/is-2fas-backup-safe/)). Tokens are protected by Apple and Google cloud encryption plus 2FAS's own encryption layer. Users can optionally encrypt exported backups (`.2fas` files) with a custom password; unencrypted exports are JSON with readable secret keys ([2fas.com/support/2fas-auth-mobile-app/where-is-my-google-drive-backup-file-is-it-encrypted/](https://2fas.com/support/2fas-auth-mobile-app/where-is-my-google-drive-backup-file-is-it-encrypted/)).

### Aegis

Aegis vault format specification ([github.com/beemdevelopment/Aegis/blob/master/docs/vault.md](https://github.com/beemdevelopment/Aegis/blob/master/docs/vault.md)):

**Encryption:** AES-256 in GCM mode as AEAD cipher for confidentiality, integrity, and authenticity.

**Master Key:** Random 256-bit key encrypts all vault contents via AES-GCM.

**Key Derivation (Password Slot):** Scrypt derives a 256-bit key from user password with parameters: N=2^15 (32,768), r=8, p=1. Random 256-bit salt protects against rainbow table attacks.

**Multiple Credential Slots:** Vault can be unlocked via multiple credentials:
- Raw slot (0x00): Direct master key storage
- Password slot (0x01): Master key encrypted with password-derived key via AES-GCM
- Biometric slot (0x02): Master key encrypted with Android KeyStore-backed key (requires fingerprint/face unlock)

Each slot contains an encrypted copy of the master key via key wrapping. The specification states: "NIST strongly recommends not exceeding 2^32 invocations when using random nonces with GCM," and Aegis acknowledges this "is assumed never to be exceeded."

---

## 8. Major Security Incidents

### Retool (August 2023)

A Retool employee's personal Google account was compromised after the attacker gained access to a browser where credentials had been synced. The employee had enabled Google Authenticator's cloud sync feature, allowing the attacker to access all MFA codes. The attacker then obtained the employee's Okta session and accessed Retool's VPN and admin systems. 27 Retool cloud customers (all in crypto) had their accounts compromised and later restored ([retool.com/blog/mfa-isnt-mfa](https://retool.com/blog/mfa-isnt-mfa)).

**Lesson:** Cloud-synced TOTP codes without end-to-end encryption become a single point of failure if the cloud account is compromised. Hardware keys were immune to this attack.

### Uber (September 2022)

An attacker purchased an Uber contractor's compromised corporate password on the dark web. The attacker repeatedly triggered MFA approval requests until the contractor accepted one out of fatigue. This MFA fatigue attack granted the attacker access to the contractor's account, and via escalation, internal tools including G-Suite and Slack ([www.uber.com](https://www.uber.com)).

**Lesson:** Repeated push notifications without rate-limiting or user education enable fatigue attacks. Verified Push (numeric confirmation) mitigates this.

### Cisco Talos (May 2022)

An employee's credentials were compromised via a personal Google account where browser passwords had been synced. The attacker conducted voice phishing attacks with various accents, impersonating support staff, attempting to convince the victim to accept MFA push notifications. After multiple days of attempts, the attacker succeeded in obtaining one MFA push acceptance, gaining VPN access. The threat actor then enrolled new MFA devices and accessed domain controllers ([blog.talosintelligence.com/recent-cyber-attack/](https://blog.talosintelligence.com/recent-cyber-attack/)).

**Lesson:** Voice phishing + MFA fatigue remains effective against push notifications without number matching. Browser credential sync creates compound risk.

### Twilio / 0ktapus (August 2022)

A phishing campaign (0ktapus) targeted 130+ organizations with SMS phishing to Okta users. Threat actors used phishing sites mimicking Okta login pages and simple phishing kits (Nuxt.js frontend, Django backend) to intercept credentials and TOTP codes in real-time ([www.group-ib.com/blog/0ktapus/](https://www.group-ib.com/blog/0ktapus/)).

**Campaign Scale:**
- 9,931 compromised user credentials
- 5,441 compromised MFA codes
- 169 unique phishing domains
- 136 unique email domains affected

Twilio was subsequently breached, allowing attackers to re-register Signal accounts to new devices ([www.group-ib.com/blog/0ktapus/](https://www.group-ib.com/blog/0ktapus/)).

**Lesson:** Phishing sites with real-time TOTP relay defeat time-based codes. Only hardware keys were immune.

### Reddit (February 2023)

Reddit employees were targeted with a phishing site impersonating Reddit's internal intranet. The phishing site attempted to steal credentials and TOTP two-factor-authentication tokens. The site relayed TOTP codes to the attacker in real-time, allowing compromise of accounts protected by TOTP ([retool.com/blog/mfa-isnt-mfa](https://retool.com/blog/mfa-isnt-mfa)). Accounts protected by hardware security keys were not vulnerable. Reddit internal documents and code were exfiltrated.

**Lesson:** Real-time TOTP relay via phishing defeats TOTP entirely. Hardware keys (U2F/WebAuthn) are the only MFA method immune to phishing.

### MGM (September 2023)

Attackers identified an MGM IT administrator on LinkedIn, gathered personal information, and called MGM's corporate help desk impersonating that administrator. Claiming to be locked out of their MFA device while traveling, they requested an MFA reset. The help desk complied. Using the reset, the attackers authenticated to MGM's Okta SSO and pivoted through enterprise applications. ALPHV/BlackCat ransomware was deployed, encrypting hundreds of ESXi servers. Business was fully restored within 9 days ([morphisec.com/blog/mgm-resorts-alphv-spider-ransomware-attack/](https://www.morphisec.com/blog/mgm-resorts-alphv-spider-ransomware-attack/)).

**Lesson:** MFA can be reset via social engineering if help desk procedures lack verification rigor. Identity verification at the help desk is critical.

### Snowflake (2024)

Snowflake customers without MFA enabled were breached using stolen credentials harvested by infostealer malware (Vidar, RISEPRO, LummaC2). Attackers directly logged into Snowflake accounts with compromised usernames and passwords. Over 165 organizations were affected, including Ticketmaster, Advance Auto Parts, and Santander Bank ([nightfall.ai/blog/what-happened-in-the-snowflake-data-breach](https://www.nightfall.ai/blog/what-happened-in-the-snowflake-data-breach)). None of the breached accounts had MFA enabled.

**Lesson:** MFA is not a compliance checkbox; enforcement is mandatory. MFA absence leaves accounts vulnerable to credential-stuffing attacks even from well-resourced threat actors.

---

## 9. Scale Statistics

**Google Authenticator:**
- Over 100 million downloads on Google Play ([play.google.com/store/apps/details?id=com.google.android.apps.authenticator2](https://play.google.com/store/apps/details?id=com.google.android.apps.authenticator2))

**Google 2-Step Verification:**
- Auto-enabled for over 150 million people ([blog.google/innovation-and-ai/technology/safety-security/reducing-account-hijacking/](https://blog.google/innovation-and-ai/technology/safety-security/reducing-account-hijacking/))
- 50% decrease in account compromise among auto-enrolled users

**Microsoft MFA:**
- More than 99.9% of compromised accounts do not have MFA ([learn.microsoft.com/en-us/partner-center/security/security-at-your-organization](https://learn.microsoft.com/en-us/partner-center/security/security-at-your-organization))
- MFA can block over 99.9% of account compromise attacks ([www.microsoft.com/en-us/security/blog/2019/08/20/one-simple-action-you-can-take-to-prevent-99-9-percent-of-account-attacks/](https://www.microsoft.com/en-us/security/blog/2019/08/20/one-simple-action-you-can-take-to-prevent-99-9-percent-of-account-attacks/))
- 300 million fraudulent sign-in attempts to Microsoft cloud services daily ([www.microsoft.com/en-us/security/blog/2019/08/20/one-simple-action-you-can-take-to-prevent-99-9-percent-of-account-attacks/](https://www.microsoft.com/en-us/security/blog/2019/08/20/one-simple-action-you-can-take-to-prevent-99-9-percent-of-account-attacks/))

**Duo:**
- 1.3 billion monthly authentications (40+ million per day) ([duo.com/resources/ebooks/2024-duo-trusted-access-report](https://duo.com/resources/ebooks/2024-duo-trusted-access-report))
- 40,000+ customers globally ([duo.com/resources/ebooks/2024-duo-trusted-access-report](https://duo.com/resources/ebooks/2024-duo-trusted-access-report))

**Authy:**
- Millions of users; serves customers like Twitch, Coinbase, SendGrid

---

## 10. Comparison Table: Product Matrix

| Product | Secret Storage on Device | Cloud Backup | E2EE? | Key Derivation | Recovery Path | Push? | Open Source? |
|---|---|---|---|---|---|---|---|
| Google Authenticator | Plaintext in local vault | Yes, to Google Account | Not E2EE (server-side encryption) | N/A for sync | Recover via Google Account; 24-word export codes unavailable | No | Closed source (archived fork 2021) |
| Authy | Encrypted (AES-256-CBC) | Yes, encrypted backups | Zero-knowledge (device-side encryption) | PBKDF2 100k rounds | 24-hour wait, SMS/voice/trusted device | No | Closed source |
| Microsoft Authenticator | Encrypted (local device) | Yes, to iCloud (iOS) | Encrypted in transit | N/A for backup | Restore via iCloud; passwordless phone sign-in | Yes, push + number matching | Closed source |
| Duo | Encrypted | Not documented | Verified Push only | N/A | Help desk restore (Verified Push available) | Yes, Verified Push | Closed source |
| Okta Verify | Encrypted | Depends on Okta backend | No | N/A | Okta account recovery | Optional | Closed source |
| Twilio Verify | Server-side only | N/A (API service) | No | N/A | Depends on implementation | No | Closed source |
| 1Password | Encrypted (2SKD + SRP) | Yes, encrypted | Yes (2SKD) | 2SKD (128-bit Secret Key) + SRP | Recovery codes + Secret Key backup | No | Closed source |
| Bitwarden | Encrypted (local) | Yes, encrypted | Yes | PBKDF2 (700k) or Argon2id (6 iter, 32 MiB) | Master password recovery only | No | Open source |
| Apple Passwords | Encrypted (device) | Yes, iCloud Keychain | Yes, E2EE | Device encryption only | iCloud recovery | No | Closed source |
| Ente Auth | Encrypted (device) | Yes, encrypted | Yes, E2EE | Argon2id + XChaCha20-Poly1305 | 24-word recovery phrase (no password reset) | No | Open source (ente-io/ente) |
| 2FAS | Encrypted (device) | Yes, Google Drive / iCloud | Yes, E2EE + optional password | Optional custom password | Device-based recovery; 24-hour wait if multi-device disabled | No | Open source (twofas) |
| Aegis | Encrypted (AES-256-GCM) | Encrypted export only | Yes (local only) | Scrypt (32k, r=8, p=1); supports password + biometric slots | Recovery code (slot format) | No | Open source (beemdevelopment/Aegis) |

---

## Key Architectural Findings

**Secret Derivation Trend:** PBKDF2 (100k-700k iterations) dominates client implementations; Argon2id gaining adoption in newer systems. Mobile constraints favor lower iteration counts (Aegis: N=32k).

**Cloud Backup Models:**
- Google & Microsoft: Server-side encryption (not E2EE).
- Authy: Zero-knowledge (client-side encryption, server stores only ciphertext).
- Ente, 2FAS, Aegis: E2EE with recovery keys or passphrases.

**Incident Pattern:** Phishing + real-time TOTP relay defeats TOTP-only deployments. Hardware keys (U2F/WebAuthn) remain immune. Number matching (Duo Verified Push, Microsoft Authenticator) raises the bar.

**Multi-Factor MFA:** Verified Push + numeric confirmation > push-only > TOTP > SMS.

---

**Sources:**
- [github.com/google/google-authenticator-android](https://github.com/google/google-authenticator-android)
- [support.google.com/accounts/answer/1066447](https://support.google.com/accounts/answer/1066447)
- [www.twilio.com/en-us/blog/how-the-authy-two-factor-backups-work](https://www.twilio.com/en-us/blog/how-the-authy-two-factor-backups-work)
- [www.twilio.com/en-us/changelog/Security_Alert_Authy_App_Android_iOS](https://www.twilio.com/en-us/changelog/Security_Alert_Authy_App_Android_iOS)
- [support.microsoft.com/en-us/account-billing/restore-account-credentials-from-microsoft-authenticator](https://support.microsoft.com/en-us/account-billing/restore-account-credentials-from-microsoft-authenticator)
- [learn.microsoft.com/en-us/entra/identity/authentication/how-to-mfa-number-match](https://learn.microsoft.com/en-us/entra/identity/authentication/how-to-mfa-number-match)
- [duo.com/docs/authentication-methods-security-guide](https://duo.com/docs/authentication-methods-security-guide)
- [duo.com/resources/ebooks/2024-duo-trusted-access-report](https://duo.com/resources/ebooks/2024-duo-trusted-access-report)
- [www.twilio.com/docs/verify/totp/technical-overview](https://www.twilio.com/docs/verify/totp/technical-overview)
- [support.okta.com/help/s/article/okta-verify-totp-code-time-to-live](https://support.okta.com/help/s/article/okta-verify-totp-code-time-to-live)
- [1password.com/blog/developers-how-we-use-srp-and-you-can-too](https://1password.com/blog/developers-how-we-use-srp-and-you-can-too)
- [bitwarden.com/help/kdf-algorithms/](https://bitwarden.com/help/kdf-algorithms/)
- [support.apple.com/en-us/120758](https://support.apple.com/en-us/120758)
- [help.ente.io/auth/faq/](https://help.ente.io/auth/faq/)
- [2fas.com/support/2fas-auth-security-privacy/is-2fas-backup-safe/](https://2fas.com/support/2fas-auth-security-privacy/is-2fas-backup-safe/)
- [github.com/beemdevelopment/Aegis/blob/master/docs/vault.md](https://github.com/beemdevelopment/Aegis/blob/master/docs/vault.md)
- [retool.com/blog/mfa-isnt-mfa](https://retool.com/blog/mfa-isnt-mfa)
- [blog.talosintelligence.com/recent-cyber-attack/](https://blog.talosintelligence.com/recent-cyber-attack/)
- [www.group-ib.com/blog/0ktapus/](https://www.group-ib.com/blog/0ktapus/)
- [morphisec.com/blog/mgm-resorts-alphv-spider-ransomware-attack/](https://www.morphisec.com/blog/mgm-resorts-alphv-spider-ransomware-attack/)
- [nightfall.ai/blog/what-happened-in-the-snowflake-data-breach](https://www.nightfall.ai/blog/what-happened-in-the-snowflake-data-breach)
- [learn.microsoft.com/en-us/partner-center/security/security-at-your-organization](https://learn.microsoft.com/en-us/partner-center/security/security-at-your-organization)
- [www.microsoft.com/en-us/security/blog/2019/08/20/one-simple-action-you-can-take-to-prevent-99-9-percent-of-account-attacks/](https://www.microsoft.com/en-us/security/blog/2019/08/20/one-simple-action-you-can-take-to-prevent-99-9-percent-of-account-attacks/)

---

## Spot-check corrections (editor, 2026-10-03)

Checked by fetching the sources directly. The survey text above is left as the agent wrote it. Where they disagree, this table wins.

| Claim in the survey | What the source says | Effect on the design |
|---|---|---|
| Microsoft number matching "enforcement ... began October 15, 2024" | The cited page is about mandatory MFA for the Entra admin portals, a different policy. Number matching was enforced for all Authenticator push notifications from **May 8, 2023** (secondary: [BleepingComputer](https://www.bleepingcomputer.com/news/microsoft/microsoft-enforces-number-matching-to-fight-mfa-fatigue-attacks/); the current Microsoft Learn page no longer states the date) | Use May 2023 |
| Google Authenticator E2EE "not explicitly stated" | The help page says only "Google encrypts Authenticator codes both in transit and at rest" ([support.google.com/accounts/answer/1066447](https://support.google.com/accounts/answer/1066447), fetched 2026-10-03). No end-to-end claim. The page also says a newly set up Authenticator "may take up to 7 days" to become a sign-in option for the Google Account, and that deleting a synced code deletes it on all devices | We read this as server-side encryption. solution §4.4 builds that version, §5.1 replaces it |
| Google 2SV "150 million auto-enabled, 50% decrease" | Confirmed ([blog.google](https://blog.google/technology/safety-security/reducing-account-hijacking/)) | Used in §10.8 |
| Authy PBKDF2 100,000 rounds, AES-256-CBC | Confirmed: "We use 100,000 rounds", AES-256 in CBC mode with a different IV per account ([twilio.com/blog](https://www.twilio.com/blog/how-the-authy-two-factor-backups-work)). CBC has no integrity tag; the design uses an AEAD instead | Used in §10.7 and §10.8 |
| Authy July 2024 incident | Twilio's alert confirms an unauthenticated endpoint exposed data "including phone numbers". It does not state a count. The ~33 M figure comes from the attackers' claim [secondary] | Quote without the number |
| Retool, 27 cloud customers | Confirmed, including the Google Authenticator sync point ([retool.com/blog/mfa-isnt-mfa](https://retool.com/blog/mfa-isnt-mfa)) | The motivating incident for solution §5.1 |
| Duo "1.3 billion monthly authentications" | The report page is gated and was not re-fetched. [unverified] | Not used as a design number |
