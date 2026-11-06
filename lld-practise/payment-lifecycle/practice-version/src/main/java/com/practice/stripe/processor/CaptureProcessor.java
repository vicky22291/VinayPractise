package com.practice.stripe.processor;

import java.util.UUID;

public interface CaptureProcessor {
    record Command(UUID captureId, UUID paymentId, long amount, String currency) {}
    enum Outcome { SUCCEEDED, DECLINED, UNKNOWN }

    /** The processor must deduplicate by captureId, including after an accepted request times out. */
    Outcome capture(Command command);
}
