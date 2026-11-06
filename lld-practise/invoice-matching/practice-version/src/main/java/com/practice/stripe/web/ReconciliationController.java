package com.practice.stripe.web;

import com.practice.stripe.domain.MatchResult;
import com.practice.stripe.domain.MatchingStage;
import com.practice.stripe.service.ReconciliationService;
import jakarta.validation.Valid;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.PositiveOrZero;
import java.util.List;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/reconciliations")
public class ReconciliationController {
    public record ReconcileRequest(@NotNull List<String> payments, @NotNull List<String> invoices,
                                   MatchingStage stage, @PositiveOrZero Long tolerance) {}
    public record ReconcileResponse(List<MatchResult> results) {}

    private final ReconciliationService service;

    public ReconciliationController(ReconciliationService service) { this.service = service; }

    @PostMapping
    public ReconcileResponse reconcile(@Valid @RequestBody ReconcileRequest request) {
        MatchingStage stage = request.stage() == null ? MatchingStage.TOLERANCE : request.stage();
        long tolerance = request.tolerance() == null ? 0 : request.tolerance();
        return new ReconcileResponse(service.reconcile(request.payments(), request.invoices(), stage, tolerance));
    }
}
