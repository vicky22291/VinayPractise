package com.practice.stripe.service;

import com.practice.stripe.domain.*;
import java.util.*;
import java.util.regex.Pattern;
import org.springframework.stereotype.Service;

/** Stateless service: open-invoice indexes belong to one invocation, never to the JVM. */
@Service
public class ReconciliationService {
    // Letters, numbers, underscores and hyphens are identifier characters, including Unicode letters/numbers.
    private static final Pattern MEMO_ID = Pattern.compile("(?<![\\p{L}\\p{N}_-])INV-[0-9]+(?![\\p{L}\\p{N}_-])");
    private static final Comparator<Invoice> DUE_ORDER =
            Comparator.comparing(Invoice::dueDate).thenComparing(Invoice::id);

    /** Original stage-one contract. */
    public List<MatchResult> reconcile(List<String> payments, List<String> invoices) {
        return reconcile(payments, invoices, MatchingStage.MEMO_ONLY, 0);
    }

    /** All three stages, with the supplied tolerance in minor units. */
    public List<MatchResult> reconcile(List<String> payments, List<String> invoices, long tolerance) {
        return reconcile(payments, invoices, MatchingStage.TOLERANCE, tolerance);
    }

    public List<MatchResult> reconcile(List<String> paymentRows, List<String> invoiceRows,
                                       MatchingStage stage, long tolerance) {
        if (stage == null) throw new IllegalArgumentException("stage must not be null");
        if (tolerance < 0) throw new IllegalArgumentException("tolerance must be nonnegative");
        // Validate the complete batch before matching anything.
        List<Payment> payments = BatchParser.payments(paymentRows);
        var open = new OpenInvoices(BatchParser.invoices(invoiceRows));
        var results = new ArrayList<MatchResult>();
        for (Payment payment : payments) {
            Invoice invoice = open.memoMatch(payment.memo());
            MatchRule rule = MatchRule.MEMO;
            if (invoice == null && stage != MatchingStage.MEMO_ONLY) {
                invoice = open.exactMatch(payment.amount());
                rule = MatchRule.EXACT_AMOUNT;
            }
            if (invoice == null && stage == MatchingStage.TOLERANCE) {
                invoice = open.toleranceMatch(payment.amount(), tolerance);
                rule = MatchRule.TOLERANCE;
            }
            if (invoice == null) rule = MatchRule.NONE;
            else open.remove(invoice);
            results.add(new MatchResult(payment, invoice, rule));
        }
        return List.copyOf(results);
    }

    private static final class OpenInvoices {
        private final Map<String, Invoice> byId = new HashMap<>();
        private final NavigableMap<Long, NavigableSet<Invoice>> byAmount = new TreeMap<>();

        OpenInvoices(List<Invoice> invoices) {
            for (Invoice invoice : invoices) {
                byId.put(invoice.id(), invoice);
                byAmount.computeIfAbsent(invoice.amount(), ignored -> new TreeSet<>(DUE_ORDER)).add(invoice);
            }
        }

        Invoice memoMatch(String memo) {
            var matcher = MEMO_ID.matcher(memo);
            while (matcher.find()) {
                Invoice invoice = byId.get(matcher.group());
                if (invoice != null) return invoice;
            }
            return null;
        }

        Invoice exactMatch(long amount) {
            var candidates = byAmount.get(amount);
            return candidates == null ? null : candidates.first();
        }

        Invoice toleranceMatch(long amount, long tolerance) {
            // Saturating bounds avoid overflow, even for Long.MAX_VALUE amounts/tolerances.
            long low = amount < tolerance ? 0 : amount - tolerance;
            long high = tolerance > Long.MAX_VALUE - amount ? Long.MAX_VALUE : amount + tolerance;
            Invoice best = null;
            for (var bucket : byAmount.subMap(low, true, high, true).values()) {
                Invoice candidate = bucket.first();
                if (best == null || DUE_ORDER.compare(candidate, best) < 0) best = candidate;
            }
            return best;
        }

        void remove(Invoice invoice) {
            byId.remove(invoice.id());
            var bucket = byAmount.get(invoice.amount());
            bucket.remove(invoice);
            if (bucket.isEmpty()) byAmount.remove(invoice.amount());
        }
    }
}
