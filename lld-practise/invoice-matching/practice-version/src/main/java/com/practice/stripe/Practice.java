package com.practice.stripe;

import com.practice.stripe.domain.MatchingStage;
import com.practice.stripe.service.ReconciliationService;
import java.util.List;

/** Runnable examples for all stages: mvn compile exec:java. */
public class Practice {
    public static void main(String[] args) {
        var service = new ReconciliationService();
        var invoices = List.of("INV-1,500,2026-11-10", "INV-12,700,2026-11-12");
        var payments = List.of("p1,500,Paying INV-12, thanks", "p2,500,Paying INV-1",
                "p3,700,Paying INV-12 again");
        System.out.println("Stage 1: memo order and one match per invoice");
        service.reconcile(payments, invoices).forEach(result -> System.out.println(result.description()));

        var fallbackInvoices = List.of("INV-1,500,2026-11-10", "INV-2,505,2026-11-01",
                "INV-3,495,2026-11-02");
        var fallbackPayments = List.of("p1,500,no reference", "p2,500,no reference", "p3,500,no reference");
        for (var stage : List.of(MatchingStage.EXACT_AMOUNT, MatchingStage.TOLERANCE)) {
            System.out.println("\n" + stage + " (tolerance 5 minor units)");
            service.reconcile(fallbackPayments, fallbackInvoices, stage, 5).forEach(result ->
                    System.out.println(result.description() + " [" + result.rule() + "]"));
        }
    }
}
