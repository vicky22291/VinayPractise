package com.practice.stripe.processor;

import java.util.HashMap;
import java.util.Map;
import java.util.UUID;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

/** Local processor simulator. A timeout can hide a successful charge; the next query returns that charge. */
@Component
public class SimulatedProcessor implements CaptureProcessor {
    private final Map<UUID, Command> charges = new HashMap<>();
    private final boolean timeoutAfterAccept;

    public SimulatedProcessor(@Value("${processor.timeout-after-accept:false}") boolean timeoutAfterAccept) {
        this.timeoutAfterAccept = timeoutAfterAccept;
    }

    @Override
    public synchronized Outcome capture(Command command) {
        Command existing = charges.get(command.captureId());
        if (existing != null) {
            if (!existing.equals(command)) throw new IllegalArgumentException("Processor key payload mismatch");
            return Outcome.SUCCEEDED;
        }
        charges.put(command.captureId(), command);
        return timeoutAfterAccept ? Outcome.UNKNOWN : Outcome.SUCCEEDED;
    }

    public synchronized int chargeCount() { return charges.size(); }
}
