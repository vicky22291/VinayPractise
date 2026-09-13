# Slack / large-scale messaging platform

> One-line answer: a stateless websocket gateway tier in front of a sharded "channel server" tier, where exactly one owner per channel assigns a gapless per-channel sequence number, persists the message, then fans it out to the online members' gateways; offline and reconnecting devices catch up by asking "everything after my cursor" per channel, so ordering, unreads, and multi-device sync all fall out of one number.

Tier 1, problem #2 in [`hld/README.md`](../README.md). Reported at Databricks (15 reports), also Meta E6 ("Messenger / WhatsApp"), Google L6, Amazon, Microsoft ("Teams"), and Discord.

## Problem statement

Build the messaging core of Slack. Users belong to workspaces, join channels (public, private, DM, group DM), and send text messages with attachments, reactions, threads, and edits. Every online member of a channel sees a new message within a second, in the same order as everyone else. Offline devices see the full history when they reconnect. A user may be on 5 devices at once. Some channels have 100k+ members. Presence (online / away), typing indicators, unread counts, and search are expected. Workspaces have hard tenant boundaries, and some channels are shared across two workspaces (Slack Connect).

## Functional requirements

Core:
- Send a message to a channel or DM. Text up to 40 KB, optional attachment reference, thread parent, client-generated id for retry safety.
- Receive messages in real time on every connected device of every member of the channel.
- Read history: paginate backwards from any point, fetch "everything since cursor" on reconnect.
- Unread counts and mention badges per user per channel, correct across devices.
- Presence and typing indicators for users the client is currently looking at.
- Edit and delete a message; reactions.

Below the line (say it out loud):
- Search (index pipeline sketched in a deep dive, not designed in the interview).
- Voice / video (huddles), screen sharing.
- End-to-end encryption. Slack is not E2E; server-side search, compliance export, and retention policies depend on the server reading messages. Refusing this is a Staff signal.
- Bots, workflow builder, app platform, slash commands beyond the send path.
- File storage internals (attachments are a pointer to a blob store).

## Non-functional requirements

| Dimension | Target |
|---|---|
| Scale | 50 M DAU, 20 M peak concurrent connections, 3 B messages/day sent, ~35 k msgs/s avg, 350 k msgs/s peak |
| Fan-out | avg channel 30 members, p99 channel 5 k, max 500 k. Deliveries ~100 x sends: ~3.5 M deliveries/s peak |
| Latency | send to visible on another online client p50 < 200 ms, p99 < 1 s, in-region. History page p99 < 300 ms |
| Ordering | Total order per channel. Every reader sees the same sequence. No gaps, no reordering after delivery |
| Consistency | Read-your-writes for the sender. Causal + eventual for other members (bounded by delivery latency). Unread counts eventually correct within seconds |
| Availability | 99.99% for send and receive. Degrade presence and typing before degrading messages |
| Durability | A message acked to the sender is never lost. 3 replicas in 3 AZs before ack |
| Retention | Configurable per workspace, default forever. 3 B msgs/day x 1 KB = 3 TB/day, ~1 PB/yr hot + attachments |
| Tenancy | Workspace A can never read workspace B. Shared channels are the one deliberate exception |
| Multi-region | Workspace pinned to a home region for data residency. Cross-region shared channels allowed |

## What interviewers probe (the ladder)

1. Two users send to the same channel in the same millisecond. Who is first, and does every client agree? Where is the sequencer, and what happens when it dies?
2. A channel has 100k members. What melts when one message is sent, and what about `@channel`?
3. A user has 5 devices, one has been offline for a week. How does it catch up, and how do read state and unread counts stay right across devices?
4. Gateway node dies with 100k connections. What do the clients see, how fast do they reconnect, and how do you stop the reconnect storm from killing the rest?
5. Monday 9 am, a 500k-user workspace boots. What is in the boot payload, and how do you stop that from being the bottleneck? (Slack's real problem.)
6. Client sends, times out, retries. Is the message duplicated? Where is the dedup key, how long does it live?
7. Region dies. Which users are down, for how long, what data is at risk, and can a shared channel spanning two regions keep working?
8. How do you shard the message store, what is the hot partition, and what happens to a channel with 10 years of history?
9. Presence for a 100k-user workspace. Do you really send N x M updates? What do you drop first under load?
10. How do you migrate from workspace-sharded MySQL to channel-sharded storage with zero downtime? (Slack did this.)

## Files

| File | What it is |
|---|---|
| [`solution.md`](solution.md) | Full HLD, Bad / Good / Great ladders, nitty-gritty internals |
| [`diagrams.md`](diagrams.md) | The D1 to D12 diagram set |
| [`edge-cases.md`](edge-cases.md) | Every "what if" with a 60-second answer and a confidence box |
| [`deep-dives/ordering-and-sequencer.md`](deep-dives/ordering-and-sequencer.md) | Per-channel sequence, channel owner leases, failover, why Snowflake ids are not enough |
| [`deep-dives/fan-out-and-large-channels.md`](deep-dives/fan-out-and-large-channels.md) | Fan-out on write vs read, the 100k channel, backpressure, `@channel` |
| [`deep-dives/connection-layer.md`](deep-dives/connection-layer.md) | Websocket gateways, session registry, reconnect storms, boot payload |
| [`deep-dives/sync-offline-multi-device.md`](deep-dives/sync-offline-multi-device.md) | Cursors, gap fill, push as a wake-up, per-device read state, unread counts |
| [`deep-dives/message-storage.md`](deep-dives/message-storage.md) | Partition key, time buckets, hot channels, edits, deletes, retention, the Vitess migration |
| [`deep-dives/presence.md`](deep-dives/presence.md) | Why presence is eventual, subscription-based fan-out, cost math, load shedding |
| [`research/`](research/) | Raw web research notes with source links (real-world architectures, mechanisms, interview framing). Input to the files above, not study material |
| `slack-messaging.excalidraw` | My drawing. Missing until I draw it |
| `my-attempt.md` | My timed attempt before reading the solution |
