## Part 3: disable dead endpoints, replay

1. **Disable.** When an attempt to an endpoint fails (timeout or non-2xx) and
   that endpoint's first failed attempt since its last success was more than
   259,200 seconds (3 days) before this one, disable the endpoint. A successful
   attempt ends the streak.
2. **On disable:** set `enabled = False`. Mark the failing delivery and every
   other pending delivery for that endpoint `"skipped"`. Call
   `notifier.endpoint_disabled(endpoint_id, account_id, at)` exactly once.
   `notifier` is a new optional argument:
   `Dispatcher(transport, clock, notifier=...)`.
3. **Enable.** Add `Dispatcher.enable(endpoint_id)`. It re-enables the
   endpoint and clears its failure streak.
4. **Replay.** Add `Dispatcher.replay(endpoint_id, since) -> int`. It queues one
   new delivery, due now, for every event of the endpoint's account that the
   endpoint subscribes to and that was created at or after `since`. It returns
   how many it queued.
   - Receivers see the original event ids.
   - A replayed delivery gets a full retry window, starting at the replay.
   - Replaying to a disabled endpoint raises `ValueError`.
