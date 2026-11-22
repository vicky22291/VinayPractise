# Notification platform: verified facts survey

Scope: a notification platform for up to 1M notifications per second at peak over APNs, FCM, SMS, email and an in-app inbox. Critical traffic (chat, order and payment events, OTP) must arrive in about 1 second. Promotional traffic (one campaign to thousands or millions of users) can be batched. Every type has an expiry. Context: the prompt is reported at Coupang, so Korean rules matter.

Survey date: 2026-11-22.

## How to read the status column

- **verified**: the page was opened (curl, jina reader or WebFetch) and the text was grepped or quoted. The URL is the page that was opened.
- **secondary**: the fact came only from a search-result excerpt or a third-party page. The primary page was not opened.
- **unverified**: the claim is from memory or from a conflicting source. Do not use it in an interview without checking.
- **conflict**: two sources disagree. See the Conflicts section.

## Method

- Tools: WebSearch (about 25 calls), WebFetch (about 10 calls), curl with `-A "Mozilla/5.0"` plus a tag stripper run with `python3 -I`, and `r.jina.ai` for JavaScript-heavy pages. Greps used `-i -E` on the fetched text.
- Total search and fetch calls: about 55.
- Pages that returned a JavaScript shell or a 404 were not used as evidence. Those claims are marked unverified.
- Not fetched: hellointerview.com (per instructions), any medium.com aggregator, dev.to, Wikipedia, ByteByteGo, DesignGurus, algomaster, oneuptime.

---

## 1. FCM (Firebase Cloud Messaging, HTTP v1)

| # | Fact | Value | URL | Status |
|---|---|---|---|---|
| 1.1 | Default downstream send quota per project | 600,000 messages per minute (600K). Quota counts messages, not requests. Minutes are not clock-aligned. | https://firebase.google.com/docs/cloud-messaging/throttling-and-quotas | verified |
| 1.2 | Quota is a token bucket of 1 minute | "the HTTP v1 API allots 600K Quota Tokens for each 1-minute Token Bucket" | https://firebase.google.com/docs/cloud-messaging/scale-fcm | verified |
| 1.3 | Quota covers over 99% of developers | "The default quota of 600k messages per minute covers over 99% of FCM developers" | https://firebase.google.com/docs/cloud-messaging/throttling-and-quotas | verified |
| 1.4 | How to raise the send quota (normal path) | Usage at or above 80% of quota for at least 5 consecutive minutes, plus error ratio under 5%. Then request up to +25% in Cloud Console, row "Send requests per minute", under QUOTA & SYSTEM LIMITS. | https://firebase.google.com/docs/cloud-messaging/throttling-and-quotas | verified |
| 1.5 | Temporary event or large launch quota | Must go through Firebase Support. Request "at least 15 days in advance" (page text). Large-request notice wording was cut off in the fetch. | https://firebase.google.com/docs/cloud-messaging/throttling-and-quotas | verified (15 days); the 18M/30-day wording is conflict, see Conflicts |
| 1.6 | Speed of quota increase handling | "most requests will be handled within 2 weeks" if all requirements are met | https://firebase.google.com/docs/cloud-messaging/troubleshooting | secondary (search excerpt) |
| 1.7 | Max messages per device, Android | 240 messages per minute and 5,000 messages per hour to a single device | https://firebase.google.com/docs/cloud-messaging/throttling-and-quotas | verified |
| 1.8 | Max message rate to one device, iOS | "For iOS, we return an error when the rate exceeds APNs limits." | https://firebase.google.com/docs/cloud-messaging/throttling-and-quotas | verified |
| 1.9 | Collapsible message burst limit | Burst of 20 messages per app per device, refill of 1 message every 3 minutes | https://firebase.google.com/docs/cloud-messaging/throttling-and-quotas | verified |
| 1.10 | Collapse keys per message | "A maximum of 4 different collapse keys is allowed at any given time." The page does not say "per device" in that sentence. | https://firebase.google.com/docs/cloud-messaging/concept-options (jina copy) | verified (scope per device is an inference) |
| 1.11 | Default message TTL | 4 weeks if not set | https://firebase.google.com/docs/reference/fcm/rest/v1/projects.messages | verified |
| 1.12 | Max message TTL | 4 weeks. TTL 0 means send immediately. | https://firebase.google.com/docs/reference/fcm/rest/v1/projects.messages | verified |
| 1.13 | Normal vs high priority | Normal is the default. Normal is "delivered immediately when the device is not sleeping", and Doze may delay it. High means FCM "attempts to deliver ... immediately" and can wake a sleeping device. | https://firebase.google.com/docs/cloud-messaging/android-message-priority (fetched as the `android-message-priority` page via curl; text quoted in the grep) | verified |
| 1.14 | Deprioritization of high priority on Android | If FCM sees messages that do not produce user-visible notifications, high priority may be lowered to normal or proxied to Google Play services. FCM uses 7 days of behavior, per app instance. Showing a visible notification restores normal treatment. | https://firebase.google.com/docs/cloud-messaging/android-message-priority | verified |
| 1.15 | Proxying scope | Proxying is default for Android Q+ with Play services 19054000+. "Messages sent through HTTP v1 API are proxied, but messages sent through the Firebase console or legacy APIs will not be proxied." Beta. | https://firebase.google.com/docs/cloud-messaging/android-message-priority | verified |
| 1.16 | Drop in delivery metrics from proxying | "you may experience a drop of up to 15% in notification delivery metrics" | https://firebase.google.com/docs/cloud-messaging/android-message-priority | verified (WebFetch quote) |
| 1.17 | Multicast batch size per call | "You can specify up to 500 FIDs and/or tokens per invocation." Uses sendEachForMulticast. | https://firebase.google.com/docs/cloud-messaging/send-message | verified |
| 1.18 | Legacy batch methods in Admin SDKs | Node.js: sendAll, sendMulticast, sendToDevice etc. removed in v13.0.0 (12 Nov 2024). Python: send_all and send_multicast dropped in v7.0.0 (17 Jul 2025). Replace with sendEach / sendEachForMulticast. | https://firebase.google.com/support/release-notes/admin/node and https://firebase.google.com/support/release-notes/admin/python | secondary (search excerpts; release-note pages not opened) |
| 1.19 | Legacy FCM HTTP (server key) shutdown date | Google's date is in conflict. One search said Google deprecated legacy send APIs on 20 Jun 2023 and shutdown starts 22 Jul 2024. Azure and Expo say cutoff 20 Jun 2024. Google's own migration page was fetched and did not show the date. | https://firebase.google.com/docs/cloud-messaging/migrate-v1 | unverified (conflict) |
| 1.20 | Auth change for v1 | v1 needs an OAuth 2.0 access token, not a server key | https://firebase.google.com/docs/cloud-messaging/migrate-v1 | secondary (search summary) |
| 1.21 | Topic fanout concurrency | Max 1,000 concurrent fanouts per project. Excess may be rejected or deferred. | https://firebase.google.com/docs/cloud-messaging/topic-messaging | verified |
| 1.22 | Topic fanout rate | "A fanout rate of 10,000 QPS for an individual project is not uncommon, but that number is not a guarantee." Capacity is divided among projects and among concurrent fanouts. "This fanout rate quota is not adjustable." | https://firebase.google.com/docs/cloud-messaging/topic-messaging | verified |
| 1.23 | Scale of FCM | "FCM processes millions of requests per second (RPS)." | https://firebase.google.com/docs/cloud-messaging/scale-fcm | verified |
| 1.24 | Ramp guidance | "At minimum, ramp from 0 to the max RPS across a 60 second time-window." Front-loading quota creates oscillations. | https://firebase.google.com/docs/cloud-messaging/scale-fcm | verified |
| 1.25 | Retry on FCM 500 | Retry with exponential backoff | https://firebase.google.com/docs/cloud-messaging/scale-fcm | verified |
| 1.26 | Payload size limit (FCM) | Not confirmed. The 4096-byte figure is from memory. | (not found) | unverified |

Notes for the design:
- The default 600K/min is about 10,000 messages per second per project. That is the single biggest constraint for a 1M/s peak. A 1M/s peak needs quota planning with Google months ahead, or sharding across projects if policy allows. Verify the policy first. Sharding across projects is an inference, not documented here.
- Per device caps (240/min, 5,000/hour) are far above normal use. They protect battery. They matter for a fan-out bug, not for normal traffic.

---

## 2. APNs (Apple Push Notification service, HTTP/2 provider API)

| # | Fact | Value | URL | Status |
|---|---|---|---|---|
| 2.1 | Transport | HTTP/2 provider API. Multiple connections allowed. "APNs allows multiple concurrent streams for each connection, but don't assume a specific number of streams." | https://developer.apple.com/documentation/usernotifications/sending-notification-requests-to-apns (jina copy) | verified |
| 2.2 | Streams with token auth | "when using an authentication token, APNs allows only one stream until you post a request with a valid authentication token." | https://developer.apple.com/documentation/usernotifications/sending-notification-requests-to-apns | verified |
| 2.3 | HTTP/2 PRIORITY frames | "APNs ignores HTTP/2 PRIORITY frames, so don't send them on your streams." | https://developer.apple.com/documentation/usernotifications/sending-notification-requests-to-apns | verified |
| 2.4 | Spread load | "Avoid push bursts over selective connections. Diversifying push traffic over many connections..." | https://developer.apple.com/documentation/usernotifications/sending-notification-requests-to-apns | verified |
| 2.5 | Payload limit (standard) | 4 KB (4096 bytes). Must not be compressed. | https://developer.apple.com/documentation/usernotifications/sending-notification-requests-to-apns | verified |
| 2.6 | Payload limit (VoIP) | 5 KB (5120 bytes) | https://developer.apple.com/documentation/usernotifications/sending-notification-requests-to-apns | verified |
| 2.7 | apns-expiration, nonzero | UNIX epoch seconds (UTC). "If the value is nonzero, APNs stores the notification and tries to deliver it at least once, repeating the attempt as needed until the specified date." | https://developer.apple.com/documentation/usernotifications/sending-notification-requests-to-apns | verified |
| 2.8 | apns-expiration, 0 | "If the value is 0, APNs attempts to deliver the notification only once and doesn't store it." | same | verified |
| 2.9 | Storage window | APNs "may store the notification for 30 days or less, depending on the date you specify" | same | verified |
| 2.10 | Expiry is best effort | "APNs uses best efforts to honor the expiry date without any guarantee." | same | verified |
| 2.11 | Offline storage per app | "APNs stores only one notification per bundle ID." "In most cases, the latest notification is stored." Not guaranteed when several are stored in a short time. | same | verified |
| 2.12 | apns-priority values | 10 = send immediately. 5 = send based on power considerations. 1 = prioritize power, "prevent awakening the device." Default if omitted is 10. | same | verified |
| 2.13 | Priority 5 and 1 behavior | Notifications with priority 5 and 1 "might get grouped and delivered in bursts"; may be throttled, saved, or not delivered. | same | verified |
| 2.14 | apns-collapse-id | Max 64 bytes. Exceeding it returns 400 BadCollapseId. | same and https://developer.apple.com/documentation/usernotifications/handling-notification-responses-from-apns | verified |
| 2.15 | 410 Unregistered / ExpiredToken | Token inactive for the topic. "There is no need to send further pushes to the same device token." | https://developer.apple.com/documentation/usernotifications/handling-notification-responses-from-apns | verified |
| 2.16 | 410 timestamp | Millisecond epoch when APNs confirmed the token invalid. Included only with 410. Use it to delete stale tokens. | same | verified |
| 2.17 | 429 TooManyProviderTokenUpdates | "Update the authentication token no more than once every 20 minutes." | same | verified |
| 2.18 | 429 TooManyRequests | Too many requests to the same device token. Retry with delay. | same | verified |
| 2.19 | 413 PayloadTooLarge | Do not retry | same | verified |
| 2.20 | Retry rule | "After 15 minutes, you can retry JSON payloads that receive response status codes that begin with 5XX." Do not retry BadDeviceToken, DeviceTokenNotForTopic, Forbidden, ExpiredToken, Unregistered, PayloadTooLarge. | same | verified |
| 2.21 | JWT provider token lifetime | Refresh at least every hour, reuse for up to 60 minutes. | https://developer.apple.com/documentation/usernotifications/setting-up-a-remote-notification-server/establishing-a-token-based-connection-to-apns | unverified (page returned 404 on direct fetch and no text came back from jina) |
| 2.22 | Connections | No fixed number is given. Use several connections, count depends on load. | https://developer.apple.com/documentation/usernotifications/sending-notification-requests-to-apns | verified (no number given) |

Notes for the design:
- Critical push (chat, OTP) should use priority 10 and a short expiration. Promotional push should use priority 5 and collapse ids. Keep priority 1 for background-only content.
- Offline behavior is the key trap. APNs keeps one notification per bundle ID. A 1M-message campaign to offline devices does not produce 1M stored messages on the device side. Only the latest survives in most cases.

---

## 3. Twilio SMS

| # | Fact | Value | URL | Status |
|---|---|---|---|---|
| 3.1 | ValidityPeriod range | Integer seconds from 1 to 36,000. Default 36,000 (10 hours). | https://www.twilio.com/docs/messaging/api/message-resource | verified |
| 3.2 | ValidityPeriod effect | "If a queued Message exceeds the validity_period, the Message is not sent." | same | verified |
| 3.3 | Recommended minimum | "A validity_period greater than 5 is recommended." | same | verified |
| 3.4 | Queue duration | "Messages will persist in the queue for a maximum of 10 hours." | https://www.twilio.com/docs/messaging/guides/account-based-throughput-overview | verified |
| 3.5 | Default in scaling guide | "Twilio queues your messages for 10 hours (36000 seconds) by default" | https://www.twilio.com/docs/messaging/guides/scaling-queueing-latency | verified |
| 3.6 | OTP example in scaling guide | Example: OTP "needs to be delivered urgently, let's assume within 180 seconds." Promo on its own Messaging Service with its own Validity Period. | same | verified (example only, not a rule) |
| 3.7 | Short code throughput | "Twilio short code numbers have an available throughput of 100 messages per second (MPS)." | https://www.twilio.com/docs/messaging/guides/account-based-throughput-overview | verified |
| 3.8 | Toll-free throughput (US) | 3 MPS default per toll-free number to US and Canada. Higher through sales. | https://help.twilio.com/articles/4411046744987-Toll-Free-SMS-and-MMS-messaging-throughput-MPS- | secondary (search excerpt) |
| 3.9 | Long code throughput outside US | 10 MPS for non-US/Canada destinations | https://help.twilio.com/articles/1260803225669-Message-throughput-MPS-and-Trust-Scores-for-A2P-10DLC-in-the-US | secondary (search excerpt) |
| 3.10 | US long code throughput | Set by A2P 10DLC brand type, campaign type and trust score. Older page says 1 MPS. | same | conflict (see Conflicts) |
| 3.11 | Account-level cap | Capacity set at the parent account. Traffic above the limit is queued. | https://www.twilio.com/docs/messaging/guides/account-based-throughput-overview | secondary (search summary) |
| 3.12 | Queue overflow error | Error 30001: queue overflow; messages can only be queued for 10 hours then fail | https://www.twilio.com/docs/api/errors/30001 | secondary (search excerpt) |
| 3.13 | GSM-7 segment size | 160 chars single; 153 per part when concatenated | https://www.twilio.com/docs/glossary/what-sms-character-limit | secondary (search excerpt) |
| 3.14 | UCS-2 segment size | 70 chars single; 67 per part when concatenated | https://www.twilio.com/docs/glossary/what-is-ucs-2-character-encoding and https://www.twilio.com/docs/glossary/what-sms-character-limit | secondary (search excerpt) |
| 3.15 | Encoding switch | "One non-GSM-7 character switches the whole message to UCS-2." Emoji, smart quotes, long dashes trigger it. | https://www.twilio.com/docs/glossary/what-sms-character-limit | secondary (search excerpt) |
| 3.16 | Toll-free multi-part | 152 GSM-7 and 66 UCS-2 per part for US and Canada toll-free | same | secondary (search excerpt) |
| 3.17 | Billing | Per segment, not per message | same | secondary (search excerpt) |

Korean text note: Korean Hangul is not in GSM-7. A Korean SMS is UCS-2. One Korean SMS segment holds 70 characters, and a multi-part segment holds 67. A 1M-recipient Korean campaign of 140 characters is 2 segments per message.

---

## 4. Amazon SES and bulk sender rules

| # | Fact | Value | URL | Status |
|---|---|---|---|---|
| 4.1 | Sandbox limits | 200 messages per 24 hours, 1 message per second. | https://docs.aws.amazon.com/ses/latest/dg/manage-sending-quotas.html | verified |
| 4.2 | Quota is rolling | "This quota is calculated on a rolling time period." | same | verified |
| 4.3 | Production access | Request to leave sandbox; can request quota in same request. | https://docs.aws.amazon.com/ses/latest/dg/request-production-access.html | secondary (search excerpt) |
| 4.4 | Response time for quota increase | Answered "within up to 24 hours" for sending quota or rate increase requests. Production access decision "within a 96-hour period". | https://docs.aws.amazon.com/ses/latest/dg/manage-sending-quotas-request-increase.html | secondary (search excerpt) |
| 4.5 | Current max send rate and quota | Read with GetSendQuota (MaxSendRate, Max24HourSend) | https://docs.aws.amazon.com/ses/latest/APIReference/API_GetSendQuota.html | secondary (search excerpt; per-account values not in docs) |
| 4.6 | Gmail bulk threshold | Starting February 1, 2024, senders of more than 5,000 messages per day to Gmail must meet extra requirements. | https://support.google.com/a/answer/81126?hl=en | verified |
| 4.7 | Gmail spam rate target | "Keep spam rates reported in Postmaster Tools below 0.30%." (Gmail-side page) | https://support.google.com/a/answer/81126?hl=en | verified |
| 4.8 | Stricter Google wording | "Keep spam rates reported in Postmaster Tools below 0.10% and avoid ever reaching a spam rate of 0.30% or higher." | same | verified (conflict with 4.7) |
| 4.9 | One-click unsubscribe | "Marketing messages and subscribed messages must support one-click unsubscribe, and include a clearly visible unsubscribe link in the message body." | same | verified |
| 4.10 | Headers | Use `List-Unsubscribe-Post: List-Unsubscribe=One-Click` plus `List-Unsubscribe` header. Page cites RFC 2369 and RFC 8058. | same | verified |
| 4.11 | Yahoo rules | Yahoo accepts POST one-click and mailto. Not opened. | https://www.bird.com/docs/knowledge-base/deliverability/gmail-yahoo-requirements (vendor page, not primary) | unverified |
| 4.12 | Transactional exemption | Receipts, password resets and 2FA codes are generally exempt from one-click unsubscribe | vendor page (not primary) | unverified |
| 4.13 | Per-user Gmail sending limit | 2,000 messages per day per user account; 3,000 unique recipients per day | https://support.google.com/a/answer/166852?hl=en | secondary (search excerpt) |
| 4.14 | Spam rate calculation | Calculated daily | https://support.google.com/a/answer/81126?hl=en | secondary (search excerpt) |

---

## 5. Korea: Act on Promotion of Information and Communications Network Utilization (정보통신망법), Article 50

| # | Fact | Value (Korean text quoted where verified) | URL | Status |
|---|---|---|---|---|
| 5.1 | Enforcement of the amended Act | "시행 2026. 10. 2. (법률 제21988호, 2026. 9. 29., 일부개정)" | https://www.law.go.kr/LSW/lsLawLinkInfo.do?chrClsCd=010202&lsJoLnkSeq=1000688185&lsId=000030 | verified |
| 5.2 | Art 50(1) prior explicit consent | "누구든지 전자적 전송매체를 이용하여 영리목적의 광고성 정보를 전송하려면 그 수신자의 명시적인 사전 동의를 받아야 한다." | same | verified |
| 5.3 | Art 50(1) exception | Listed exceptions apply, which are decided in the decree. Transaction-based exception period of 6 months is from the decree and is secondary only. | same (exceptions list); 6 months from search excerpt of law.go.kr 해석례 | verified (the exception exists); 6 months secondary |
| 5.4 | Art 50(3) night rule | "오후 9시부터 그 다음 날 오전 8시까지의 시간에 ... 영리목적의 광고성 정보를 전송하려는 자는 ... 별도의 사전 동의를 받아야 한다." | same | verified |
| 5.5 | Night rule email carve-out | "다만, 대통령령으로 정하는 매체의 경우에는 그러하지 아니하다." The decree names e-mail. | same (carve-out text verified); decree naming e-mail from search excerpt | verified (carve-out); secondary (e-mail named in decree) |
| 5.6 | Art 50(4) disclosure items | Item 1: "전송자의 명칭 및 연락처". Item 2: how to refuse or withdraw consent easily. | same | verified |
| 5.7 | Art 50(8) periodic re-check of consent | "수신동의를 받은 자는 ... 정기적으로 광고성 정보 수신자의 수신동의 여부를 확인하여야 한다." The "2년" period is not in the Act text. It is probably in the decree. | same | verified (periodic duty); 2-year period unverified in the Act |
| 5.8 | Fine for night and re-check breaches | Up to 30 million KRW (3천만원). | search excerpt only | unverified |
| 5.9 | "(광고)" label | Not in Article 50 text. Kakao's policy requires "(광고)" at the front of advertising messages sent from a channel. | https://kakaobusiness.gitbook.io/main/ad/infotalk/operations | verified (as Kakao policy, not law) |
| 5.10 | Consent wording | KISA says a consent request must say it is "광고성 정보 수신동의". Wording like "혜택 알림" or "정보제공" is not clear enough. | https://www.kisa.or.kr/402/form?postSeq=2577 | secondary (search excerpt) |

Design notes for Korea:
- Promotional push and SMS to Korean users need opt-in marked as advertising consent, separate from service consent. Those consents need a re-check record (Art 50(8)).
- Between 21:00 and 08:00 the platform needs a second consent flag for SMS and push. Email is carved out by decree.
- Critical traffic (order, payment, OTP) is informational. The advertising rules do not apply, but any cross-sell line inside it can make it advertising.

## 5b. Kakao AlimTalk (informational) and Friend Talk (advertising)

| # | Fact | Value | URL | Status |
|---|---|---|---|---|
| 5b.1 | AlimTalk is informational | Informational messages are those "정보통신망법 안내서에 '영리목적 광고성 정보의 예외'에 해당하는 메시지" | https://kakaobusiness.gitbook.io/main/ad/infotalk/operations | verified |
| 5b.2 | Advertising definition | Message sent to earn economic gain that carries information on the sender or goods/services | same | verified |
| 5b.3 | Judgement criteria | (1) special price or discount, (2) promotion or event for product or service, (3) mixed content even if info is main | same | verified |
| 5b.4 | Advertising messages must show | (광고) label, sender contact, opt-out method | same | verified |
| 5b.5 | Only informational content in AlimTalk | Order and booking confirmation, payment history, delivery status. Event or coupon messages cannot be sent. | https://cs.kakao.com/helps_html/1073208553?locale=ko | secondary (search excerpt) |
| 5b.6 | Friend Talk | Advertising allowed, only to users who added the channel | https://cs.kakao.com/helps_html/1073198348?locale=ko | secondary (search excerpt) |
| 5b.7 | Friend Talk night block | "20:50~08:00" blocked | (no primary page located) | unverified (old third-party excerpt) |
| 5b.8 | Template review time | 2 business days | https://kakaobusiness.gitbook.io/main/ad/infotalk/audit | secondary (search excerpt) |

---

## 6. Real systems (published numbers only where the page shows them)

| # | System (company) | Published figures | URL | Status |
|---|---|---|---|---|
| 6.1 | Uber real-time push (RAMEN) | 80% of API gateway requests were polling calls (before the change). "At peak, this system pushed over 70,000 QPS push messages per second ... by maintaining up to 600,000 concurrent streaming connections." Later: "more than 1.5M concurrent connections and pushes over 250,000 messages per second." Three priority buckets. TTL "from a few seconds to up to 30 minutes", persisted and retried until TTL. | https://www.uber.com/blog/real-time-push-platform/ | verified (fetched via jina). Date of the 250k figure is not on the page; the post is dated 18 Dec 2020 per search metadata |
| 6.2 | LinkedIn Air Traffic Controller (ATC) | "currently processes over a billion requests per day"; "more than 546 million members"; cut member complaints "in half". Member-to-member messaging: latency "less than a second", uses high-priority Kafka topics. Daily batch of "a hundred million requests" tolerates hours of latency. Local RocksDB reads take "a couple of milliseconds" vs "10ms to 100ms" for remote calls. Decides drop, in-app only, or in-app plus push. | https://engineering.linkedin.com/blog/2018/03/air-traffic-controller--member-first-notifications-at-linkedin | verified |
| 6.3 | Netflix RENO (Rapid Event Notification System) | About 150k events per second at peak. Delivery per platform is parallel and isolated. Pushes to APNs and FCM. Stale events dropped; only online devices get pushes; duplicates merged. Hybrid push plus poll because smart TVs are often offline. | https://netflixtechblog.com/rapid-event-notification-system-at-netflix-6deb1d2b57d1 | secondary (search excerpt; full post not opened; the 150k figure is from the excerpt) |
| 6.4 | Groupon push marketing | "almost half a billion notifications a day"; about 70 million users; campaigns of about 60M audience to be delivered within a 2-hour window | https://medium.com/groupon-eng/groupon-push-marketing-how-we-send-almost-half-a-billion-notifications-a-day-4d77a160694a | verified (fetched via jina). Company's own publication on Medium |
| 6.5 | Airbnb OMNI (Promotions and Communications Platform) | "nearly 50 billion communications every year"; Delivery Service typical end-to-end latency "less than 30 seconds"; uses Amazon SQS to queue per-channel delivery workers (email, SMS, push) | https://medium.com/airbnb-engineering/airbnbs-promotions-and-communications-platform-6266f1ffe2bd | verified (fetched via jina) |
| 6.6 | Pinterest NEP (Notification Event Processor) | Architecture description only. No per-second or per-day numbers were found in the search excerpt. | https://medium.com/pinterest-engineering/nep-notification-system-and-relevance-a7fff21986c7 | unverified (no numbers; page not fully read) |
| 6.7 | Coupang | No Coupang engineering post on push notification infrastructure was found. Coupang Engineering blog exists on Medium (Korean tag too). A Coupang job posting describes a messaging platform backend that handles "over 100,000 events per second" with 99.9999% availability. Not an engineering post. | https://medium.com/@coupang-engineering (blog home, secondary) and https://www.wanted.co.kr/wd/362767 (job posting, which of the two search results it matches is not confirmed) | unverified (job posting, not an engineering post) |

Design notes from these systems:
- Uber and LinkedIn both separate "decide" (filter, priority, channel) from "send". LinkedIn says ATC "does not send the notification itself."
- Netflix and Uber both use persistent connections for online devices and fall back to push plus retry for offline ones. TTL is the control.

## 7. Vendor throughput (OneSignal, Braze, AWS SNS and AWS push)

| # | Vendor | Figure | URL | Status |
|---|---|---|---|---|
| 7.1 | AWS SNS regional message quota | Messages per second, per account, per region, combining Publish and PublishBatch. A 10-entry PublishBatch counts as 10 messages. | https://docs.aws.amazon.com/general/latest/gr/sns.html | verified |
| 7.2 | SNS quota values | The quota table lists 30,000 and 9,000 messages per second for some regions (the search summary names N. Virginia at 30,000 and Oregon and Ireland at 9,000) and 1,500 for others. | same | verified for the table; region mapping secondary |
| 7.3 | SNS PublishBatch size | Max 10 PublishBatchRequestEntries | same | verified |
| 7.4 | SNS mobile push action TPS | 15 TPS for a publish action | (AWS SDK Java reference, old) | unverified (old SDK page, conflicting 30 TPS figure) |
| 7.5 | AWS End User Messaging Push campaign rate | 25,000 notifications per second per campaign, adjustable | https://docs.aws.amazon.com/push-notifications/latest/userguide/load-balancer-limits.html | secondary (search excerpt) |
| 7.6 | OneSignal | No fixed per-second cap. Throttle is a user setting per minute (e.g. 1,019/min becomes 960/min). API create and cancel share a rate limit; 429 with Retry-After. Webhooks not throttled. | https://documentation.onesignal.com/reference/rate-limits and https://documentation.onesignal.com/docs/throttling | secondary (search excerpt) |
| 7.7 | OneSignal "850,000+ per second" | Press-style claim from 2018 | https://appdevelopermagazine.com/onesignal-hits-850,000+-push-notifications-per-second/ | secondary; marketing claim, not a limit |
| 7.8 | Braze | No per-second limit. Limits set per minute from 10 to 500,000 per minute. Messages aborted if delayed 72 hours or more by a low rate limit. Push platforms share one limit. | https://www.braze.com/docs/user_guide/messaging/messaging_fundamentals/frequency_capping (search excerpt, and the rate-limiting page) | secondary (search excerpt) |

---

## Conflicts and corrections

1. **FCM legacy shutdown date.** Azure Notification Hubs and Expo say the cutoff was 20 June 2024. A search summary attributed to Google said deprecation on 20 June 2023 with shutdown from 22 July 2024. The Google migration page did not show either date in the fetch. Do not quote a date until Google's page is opened. Status: unverified.
2. **Gmail spam rate.** Gmail-side wording says "below 0.30%". Workspace admin wording says "below 0.10% and avoid ever reaching 0.30% or higher". Use 0.1% as the design target and 0.3% as the hard line. Both are verified on the same Google support URL family.
3. **Gmail bulk threshold wording.** The page says "more than 5,000 messages per day" in one place and "5,000 or more" in another. Treat the threshold as about 5,000 per day.
4. **FCM quota increase wait.** The FAQ says "most requests ... within 2 weeks". The quota page says temp events need a request "at least 15 days in advance". Both are Google pages. Plan for 15 days or more.
5. **Twilio queue length.** Older Twilio guidance says 4 hours. The current docs say 10 hours (36,000 seconds) in three places. Use 10 hours.
6. **Twilio US long code throughput.** An older page says 1 MPS. The current A2P 10DLC page says it depends on brand, campaign and trust score. Do not assume 1 MPS. Check the account.
7. **Twilio segment header wording.** One Twilio page says the header is 6 bytes. Another says 7 GSM-7 characters or 3 UCS-2 characters. The resulting limits (153 and 67) match. Use 153 and 67.
8. **Korean 2-year re-check.** The "2년" period is not in Article 50 text that was fetched. It is probably in the decree. Use "periodic re-check, period set by decree" in design docs until the decree is read.
9. **Korean "(광고)" label.** Not in the Act text. It is Kakao channel policy. Do not cite it as a law requirement.
10. **Korean night rule for email.** The Act text carves out media set by decree. The decree is read as naming e-mail. Secondary only.
11. **APNs "last notification only".** It is one per bundle ID in most cases, and "not always guaranteed when multiple notifications are stored in a short duration". Do not design around exact delivery of every stored item.
12. **APNs expiration 0.** Folklore says "0 means discard". The official text says deliver once and do not store. A push can still arrive late, so "0" is not a hard deadline.
13. **FCM high priority is always immediate.** Folklore. FCM can lower it to normal or proxy it after 7 days of no visible notification, per app instance.
14. **FCM batch APIs removed.** sendAll and sendMulticast are removed in the Node and Python Admin SDKs (secondary). Java still lists sendAll as deprecated. Check the SDK version.
15. **SNS 15 TPS vs regional quota.** The 15 TPS figure is from an old SDK page. The current quota page is in messages per second per region. Check the console.
16. **OneSignal 850,000 per second.** Marketing. Not a documented limit.
17. **Uber numbers.** 70,000 QPS (600,000 connections) and 250,000 messages per second (1.5M connections) are from different points in time. Quote both with their context.
18. **Netflix 150k events per second.** From a search excerpt only. Verify on the full post before quoting.
19. **Korean Friend Talk night block of 20:50 to 08:00.** Not found on a primary page. Do not use.

---

## Numbers to use in the design

Each line has the URL that supports it. Use the status shown.

1. FCM default send quota: 600,000 messages per minute per project (about 10,000/s). verified. https://firebase.google.com/docs/cloud-messaging/throttling-and-quotas
2. FCM quota increase: up to +25%, requested when usage is at or above 80% for 5 minutes. verified. https://firebase.google.com/docs/cloud-messaging/throttling-and-quotas
3. FCM per device (Android): 240 messages per minute, 5,000 per hour. verified. https://firebase.google.com/docs/cloud-messaging/throttling-and-quotas
4. FCM message TTL: default 4 weeks, max 4 weeks, 0 means immediate. verified. https://firebase.google.com/docs/reference/fcm/rest/v1/projects.messages
5. FCM topic fanout: max 1,000 concurrent fanouts per project; about 10,000 QPS per project "not uncommon", not guaranteed, not adjustable. verified. https://firebase.google.com/docs/cloud-messaging/topic-messaging
6. FCM multicast batch: up to 500 tokens per call. verified. https://firebase.google.com/docs/cloud-messaging/send-message
7. APNs payload: 4 KB standard, 5 KB VoIP, no compression. verified. https://developer.apple.com/documentation/usernotifications/sending-notification-requests-to-apns
8. APNs expiration: nonzero stores up to 30 days or less; 0 means one attempt and no storage. verified. https://developer.apple.com/documentation/usernotifications/sending-notification-requests-to-apns
9. APNs priority: 10 immediate, 5 power-aware, 1 power-first. verified. same URL
10. APNs collapse id: max 64 bytes. verified. same URL
11. APNs token provider updates: at most once every 20 minutes (429 otherwise). verified. https://developer.apple.com/documentation/usernotifications/handling-notification-responses-from-apns
12. Twilio ValidityPeriod: 1 to 36,000 seconds, default 36,000 (10 hours). verified. https://www.twilio.com/docs/messaging/api/message-resource
13. Twilio short code throughput: 100 MPS. verified. https://www.twilio.com/docs/messaging/guides/account-based-throughput-overview
14. SMS segments: GSM-7 160/153, UCS-2 70/67 (Korean text is UCS-2). secondary. https://www.twilio.com/docs/glossary/what-sms-character-limit
15. SES sandbox: 200 per day, 1 per second. verified. https://docs.aws.amazon.com/ses/latest/dg/manage-sending-quotas.html
16. Gmail bulk line: 5,000 per day from 1 Feb 2024; one-click unsubscribe required; spam rate target 0.1%, hard line 0.3%. verified. https://support.google.com/a/answer/81126?hl=en
17. Korea night rule: no advertising 21:00 to 08:00 without separate consent (email carved out by decree). verified (rule), secondary (email carve-out). https://www.law.go.kr/LSW/lsLawLinkInfo.do?chrClsCd=010202&lsJoLnkSeq=1000688185&lsId=000030
18. Uber push: about 70,000 push messages per second at peak with 600,000 connections (2020 post); 250,000 per second later. verified. https://www.uber.com/blog/real-time-push-platform/
19. LinkedIn ATC: over 1 billion requests per day; member messaging under 1 second. verified. https://engineering.linkedin.com/blog/2018/03/air-traffic-controller--member-first-notifications-at-linkedin
20. Airbnb OMNI: nearly 50 billion communications a year; delivery typically under 30 seconds end to end. verified. https://medium.com/airbnb-engineering/airbnbs-promotions-and-communications-platform-6266f1ffe2bd

---

## Least sure (for the reporter)

1. FCM legacy HTTP shutdown date (1.19). Sources disagree and Google's page was not confirmed.
2. APNs JWT token lifetime (2.21). The Apple page did not load.
3. Korean decree details: the 2-year re-check period, the (광고) wording in law, and the email carve-out (5.5, 5.7, 5.9).
4. Twilio US long code and toll-free throughput (3.8 to 3.10). Sources are old and new mixed.
5. Netflix RENO 150k events per second (6.3). Taken from a search excerpt; full post not opened.

## Gaps not filled

- FCM payload size limit (1.26): not found in fetched text.
- Yahoo sender rules (4.11): vendor page only.
- Pinterest and Slack notification numbers: no primary numbers found.
- Coupang push: no engineering post found in Korean or English search.
