package com.practice.stripe;

import com.practice.stripe.domain.*;
import com.practice.stripe.service.ReconciliationService;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.NullSource;
import org.junit.jupiter.params.provider.ValueSource;
import static org.assertj.core.api.Assertions.*;

class ReconciliationServiceTest {
    private final ReconciliationService service = new ReconciliationService();

    @Test void stageOneMatchesPromptExampleAndProducesItsDescriptions() {
        var results = service.reconcile(
                List.of("p1,500,Paying INV-12, thanks", "p2,500,Paying INV-1", "p3,700,Paying INV-12 again"),
                List.of("INV-1,500,2026-11-10", "INV-12,700,2026-11-12"));
        assertThat(results).extracting(MatchResult::description).containsExactly(
                "payment p1 (amount 500) pays invoice INV-12 due 2026-11-12",
                "payment p2 (amount 500) pays invoice INV-1 due 2026-11-10",
                "payment p3 (amount 700) has no matching invoice");
        assertThat(results).extracting(MatchResult::rule).containsExactly(MatchRule.MEMO, MatchRule.MEMO, MatchRule.NONE);
    }

    @Test void memoOrderWinsOverInvoiceOrderDueDateAndAmountAndSkipsClosedOrUnknownIds() {
        var results = service.reconcile(List.of("p1,100,INV-99, INV-2 and INV-1",
                        "p2,100,INV-2 INV-99 INV-1"),
                List.of("INV-1,100,2026-01-01", "INV-2,999,2026-12-01"), 1000);
        assertThat(results).extracting(r -> r.invoice().id()).containsExactly("INV-2", "INV-1");
        assertThat(results).allMatch(r -> r.rule() == MatchRule.MEMO);
        assertThat(results.getFirst().payment().memo()).isEqualTo("INV-99, INV-2 and INV-1");
    }

    @ParameterizedTest
    @ValueSource(strings = {"INV-12", "xINV-1", "INV-1x", "_INV-1", "INV-1_", "INV-1-extra",
            "prefix-INV-1", "éINV-1", "INV-1中", "inv-1", "INV-01", "INV-1٢"})
    void embeddedIdsPrefixesAndDifferentSpellingsDoNotMatch(String memo) {
        var result = service.reconcile(List.of("p,100," + memo), List.of("INV-1,100,2026-11-01")).getFirst();
        assertThat(result.rule()).isEqualTo(MatchRule.NONE);
        assertThat(result.invoice()).isNull();
    }

    @ParameterizedTest
    @ValueSource(strings = {"INV-1", "(INV-1), thanks", "INV-1/INV-2", "paid:INV-1.", "\tINV-1\t"})
    void punctuationAndWhitespaceDelimitWholeIds(String memo) {
        var result = service.reconcile(List.of("p,100," + memo), List.of("INV-1,100,2026-11-01")).getFirst();
        assertThat(result.rule()).isEqualTo(MatchRule.MEMO);
    }

    @Test void leadingZerosRemainPartOfInvoiceIdentity() {
        var results = service.reconcile(List.of("p1,0,INV-01", "p2,0,INV-1"),
                List.of("INV-1,0,2026-01-01", "INV-01,0,2026-01-01"));
        assertThat(results).extracting(r -> r.invoice().id()).containsExactly("INV-01", "INV-1");
    }

    @Test void stageOneDoesNotUseAmountFallbackAndEmptyMemoIsValid() {
        var results = service.reconcile(List.of("p1,500,"), List.of("INV-1,500,2026-01-01"));
        assertThat(results.getFirst().rule()).isEqualTo(MatchRule.NONE);
        assertThat(results.getFirst().payment().memo()).isEmpty();
    }

    @Test void exactFallbackUsesEarliestDateThenLexicalIdAndConsumesInvoicesInPaymentOrder() {
        var results = service.reconcile(List.of("p1,100,", "p2,100,", "p3,100,", "p4,100,"),
                List.of("INV-1,100,2026-12-01", "INV-2,100,2026-11-01", "INV-10,100,2026-11-01"),
                MatchingStage.EXACT_AMOUNT, 0);
        assertThat(results.subList(0, 3)).extracting(r -> r.invoice().id()).containsExactly("INV-10", "INV-2", "INV-1");
        assertThat(results).extracting(MatchResult::rule).containsExactly(
                MatchRule.EXACT_AMOUNT, MatchRule.EXACT_AMOUNT, MatchRule.EXACT_AMOUNT, MatchRule.NONE);
        assertThat(results).extracting(r -> r.payment().id()).containsExactly("p1", "p2", "p3", "p4");
    }

    @Test void consumedMemoReferenceCanFallBackToAnotherOpenInvoice() {
        var results = service.reconcile(List.of("p1,100,INV-1", "p2,100,INV-1"),
                List.of("INV-1,100,2026-11-01", "INV-2,100,2026-11-02"), MatchingStage.EXACT_AMOUNT, 0);
        assertThat(results).extracting(MatchResult::rule).containsExactly(MatchRule.MEMO, MatchRule.EXACT_AMOUNT);
        assertThat(results.get(1).invoice().id()).isEqualTo("INV-2");
    }

    @Test void stageTwoDoesNotApplyTolerance() {
        var result = service.reconcile(List.of("p,100,"), List.of("INV-1,101,2026-11-01"),
                MatchingStage.EXACT_AMOUNT, 10).getFirst();
        assertThat(result.rule()).isEqualTo(MatchRule.NONE);
    }

    @Test void exactAmountWinsOverEarlierToleranceInvoice() {
        var result = service.reconcile(List.of("p,100,"),
                List.of("INV-1,101,2026-01-01", "INV-2,100,2026-12-01"), 1).getFirst();
        assertThat(result.invoice().id()).isEqualTo("INV-2");
        assertThat(result.rule()).isEqualTo(MatchRule.EXACT_AMOUNT);
    }

    @Test void toleranceIsInclusiveAndUsesDueDateThenLexicalIdRatherThanClosestAmount() {
        var results = service.reconcile(List.of("p1,100,", "p2,100,", "p3,100,", "p4,100,", "p5,100,"),
                List.of("INV-1,101,2026-12-01", "INV-2,95,2026-01-01", "INV-10,105,2026-01-01",
                        "INV-3,94,2025-01-01", "INV-4,106,2025-01-01"), 5);
        assertThat(results.subList(0, 3)).extracting(r -> r.invoice().id()).containsExactly("INV-10", "INV-2", "INV-1");
        assertThat(results).extracting(MatchResult::rule).containsExactly(
                MatchRule.TOLERANCE, MatchRule.TOLERANCE, MatchRule.TOLERANCE, MatchRule.NONE, MatchRule.NONE);
    }

    @Test void toleranceBoundsDoNotOverflowAtLongLimits() {
        var results = service.reconcile(List.of("p1,9223372036854775807,", "p2,0,"),
                List.of("INV-1,0,2026-01-01", "INV-2,9223372036854775806,2026-01-02"), Long.MAX_VALUE);
        assertThat(results).extracting(r -> r.invoice().id()).containsExactly("INV-1", "INV-2");
        assertThat(results).allMatch(r -> r.rule() == MatchRule.TOLERANCE);
        var nearMax = service.reconcile(List.of("p,9223372036854775807,"),
                List.of("INV-1,0,2026-01-01", "INV-2,9223372036854775806,2026-01-02"), 1).getFirst();
        assertThat(nearMax.invoice().id()).isEqualTo("INV-2");
    }

    @Test void zeroAmountsAndZeroToleranceUseExactRule() {
        var result = service.reconcile(List.of("p,0,"), List.of("INV-1,0,2026-01-01"), 0).getFirst();
        assertThat(result.rule()).isEqualTo(MatchRule.EXACT_AMOUNT);
    }

    @Test void trimsStructuredFieldsButPreservesMemoAndReturnsImmutableResults() {
        var payments = new ArrayList<>(List.of(" p , 100 ,  INV-1, thanks  "));
        var invoices = new ArrayList<>(List.of(" INV-1 , 100 , 2026-01-01 "));
        var results = service.reconcile(payments, invoices);
        assertThat(results.getFirst().payment()).isEqualTo(new Payment("p", 100, "  INV-1, thanks  "));
        assertThat(payments).containsExactly(" p , 100 ,  INV-1, thanks  ");
        assertThat(invoices).containsExactly(" INV-1 , 100 , 2026-01-01 ");
        assertThatThrownBy(results::clear).isInstanceOf(UnsupportedOperationException.class);
        assertThat(service.reconcile(payments, invoices)).isEqualTo(results);
    }

    @Test void emptyListsAreValid() {
        assertThat(service.reconcile(List.of(), List.of())).isEmpty();
        assertThat(service.reconcile(List.of("p,100,"), List.of(), 100).getFirst().rule()).isEqualTo(MatchRule.NONE);
    }

    @ParameterizedTest
    @NullSource
    @ValueSource(strings = {"", "p,1", ",1,memo", "p,-1,memo", "p,+1,memo", "p,1.5,memo",
            "p,9223372036854775808,memo", "p,,memo", "p,١,memo"})
    void rejectsMalformedPaymentsWithRowNumber(String row) {
        assertThatThrownBy(() -> service.reconcile(Arrays.asList("good,1,", row), List.of()))
                .isInstanceOf(IllegalArgumentException.class).hasMessageStartingWith("payment row 2:");
    }

    @ParameterizedTest
    @NullSource
    @ValueSource(strings = {"", "INV-1,1", "inv-1,1,2026-01-01", "INV-,1,2026-01-01",
            "INV-1,-1,2026-01-01", "INV-1,9223372036854775808,2026-01-01", "INV-1,1,2026-02-29",
            "INV-1,1,2026-13-01", "INV-1,1,2026-1-1", "INV-1,1,2026-01-01,extra"})
    void rejectsMalformedInvoicesWithRowNumber(String row) {
        assertThatThrownBy(() -> service.reconcile(List.of(), Arrays.asList(row)))
                .isInstanceOf(IllegalArgumentException.class).hasMessageStartingWith("invoice row 1:");
    }

    @Test void rejectsDuplicateIdsNullListsNullStageAndNegativeTolerance() {
        assertThatThrownBy(() -> service.reconcile(List.of("p,1,", " p ,2,"), List.of()))
                .hasMessageContaining("duplicate payment ID: p");
        assertThatThrownBy(() -> service.reconcile(List.of(), List.of("INV-1,1,2026-01-01", "INV-1,2,2026-01-02")))
                .hasMessageContaining("duplicate invoice ID: INV-1");
        assertThatThrownBy(() -> service.reconcile(null, List.of())).hasMessageContaining("payment rows must not be null");
        assertThatThrownBy(() -> service.reconcile(List.of(), null)).hasMessageContaining("invoice rows must not be null");
        assertThatThrownBy(() -> service.reconcile(List.of(), List.of(), null, 0)).hasMessageContaining("stage");
        assertThatThrownBy(() -> service.reconcile(List.of(), List.of(), -1)).hasMessageContaining("tolerance");
    }

    @Test void validatesUnreferencedInvoicesAndTrailingPaymentsBeforeReturningAnyResults() {
        assertThatThrownBy(() -> service.reconcile(List.of("p,1,INV-1"),
                List.of("INV-1,1,2026-01-01", "broken"))).hasMessageStartingWith("invoice row 2:");
        assertThatThrownBy(() -> service.reconcile(List.of("p,1,INV-1", "broken"),
                List.of("INV-1,1,2026-01-01"))).hasMessageStartingWith("payment row 2:");
    }
}
