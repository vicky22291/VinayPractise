# Interviewer: reveal one stage at a time

## Stage 2: Retry

Retry failed or timed-out deliveries using exponential backoff and a maximum attempt count. Make the clock injectable so retry timing can be tested without sleeping. The same event may be delivered more than once, so document what guarantee your sender provides and what the receiver must do.

## Stage 3: Recovery and ordering

Assume workers can crash between selecting a delivery and recording the response. Explain or implement a lease/claim mechanism so work can resume after a worker dies. Decide whether events must be ordered per endpoint; state the throughput and complexity trade-off.

## Interviewer follow-ups

- How do you prevent one failing endpoint from blocking other merchants?
- What identifiers should a receiver use to deduplicate deliveries?
- How would operators replay a delivery safely?
- Which states and metrics would you expose to support teams?
- What is your smallest safe first release, and how would you roll it out?
