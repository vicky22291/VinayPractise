package com.practice.stripe;

import com.practice.stripe.domain.*;
import com.practice.stripe.exception.ApiException;
import com.practice.stripe.processor.*;
import com.practice.stripe.repository.PaymentRepository;
import com.practice.stripe.service.PaymentService;
import java.util.UUID;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import static org.assertj.core.api.Assertions.*;

class PaymentServiceTest {
    private final SimulatedProcessor processor = new SimulatedProcessor(false);
    private final PaymentService service = new PaymentService(new PaymentRepository(), processor);

    private Payment authorized(long amount) {
        Payment payment = service.create(amount, "usd", "create");
        return service.authorize(payment.id(), "authorize");
    }

    @Test void fullLifecycleAndOriginalRetrySnapshots() {
        Payment payment = authorized(1000);
        Capture capture = service.capture(payment.id(), null, "full");
        assertThat(capture.status()).isEqualTo(Capture.Status.SUCCEEDED);
        assertThat(service.get(payment.id()).status()).isEqualTo(Payment.Status.CAPTURED);
        assertThat(service.get(payment.id()).capturedAmount()).isEqualTo(1000);
        assertThat(service.authorize(payment.id(), "authorize")).isEqualTo(payment);
        assertThat(service.capture(payment.id(), null, "full")).isEqualTo(capture);
        assertThat(processor.chargeCount()).isEqualTo(1);
    }

    @Test void invalidTransitionsLeaveStateUnchanged() {
        Payment payment = service.create(100, "USD", "create");
        assertThatThrownBy(() -> service.capture(payment.id(), 50L, "early")).isInstanceOf(ApiException.class);
        assertThat(service.get(payment.id())).isEqualTo(payment);
        Payment canceled = service.cancel(payment.id(), "cancel");
        assertThatThrownBy(() -> service.authorize(payment.id(), "late-auth")).isInstanceOf(ApiException.class);
        assertThatThrownBy(() -> service.capture(payment.id(), 50L, "late-capture")).isInstanceOf(ApiException.class);
        assertThat(service.get(payment.id())).isEqualTo(canceled);
    }

    @Test void partialCaptureCannotOverdrawOrBeCanceled() {
        Payment payment = authorized(1000);
        service.capture(payment.id(), 400L, "partial");
        Payment partial = service.get(payment.id());
        assertThat(partial.status()).isEqualTo(Payment.Status.PARTIALLY_CAPTURED);
        assertThatThrownBy(() -> service.capture(payment.id(), 601L, "excess")).isInstanceOf(ApiException.class);
        assertThatThrownBy(() -> service.cancel(payment.id(), "cancel")).isInstanceOf(ApiException.class);
        assertThat(service.get(payment.id())).isEqualTo(partial);
        service.capture(payment.id(), 600L, "rest");
        assertThat(service.get(payment.id()).status()).isEqualTo(Payment.Status.CAPTURED);
    }

    @Test void keysCompareOperationTargetAndPayload() {
        Payment payment = authorized(1000);
        service.capture(payment.id(), 100L, "capture");
        assertThatThrownBy(() -> service.capture(payment.id(), 101L, "capture")).hasMessageContaining("different request");
        assertThatThrownBy(() -> service.cancel(payment.id(), "capture")).hasMessageContaining("different request");
        assertThatThrownBy(() -> service.capture(UUID.randomUUID(), 100L, "capture")).hasMessageContaining("different request");
    }

    @Test void acceptedButTimedOutCaptureIsReservedAndReconciledWithoutDoubleCharge() {
        var uncertainProcessor = new SimulatedProcessor(true);
        var uncertain = new PaymentService(new PaymentRepository(), uncertainProcessor);
        Payment payment = uncertain.create(1000, "USD", "create");
        uncertain.authorize(payment.id(), "authorize");
        Capture pending = uncertain.capture(payment.id(), 1000L, "capture");
        assertThat(pending.status()).isEqualTo(Capture.Status.UNKNOWN);
        assertThat(uncertain.get(payment.id()).reservedAmount()).isEqualTo(1000);
        assertThatThrownBy(() -> uncertain.capture(payment.id(), 1L, "another")).isInstanceOf(ApiException.class);
        assertThatThrownBy(() -> uncertain.cancel(payment.id(), "cancel")).isInstanceOf(ApiException.class);
        Capture settled = uncertain.reconcile(payment.id(), pending.id(), "reconcile");
        assertThat(settled.status()).isEqualTo(Capture.Status.SUCCEEDED);
        assertThat(uncertain.capture(payment.id(), 1000L, "capture")).isEqualTo(pending);
        assertThat(uncertain.reconcile(payment.id(), pending.id(), "observe")).isEqualTo(settled);
        assertThat(uncertain.get(payment.id()).reservedAmount()).isZero();
        assertThat(uncertain.get(payment.id()).capturedAmount()).isEqualTo(1000);
        assertThat(uncertainProcessor.chargeCount()).isEqualTo(1);
    }

    @Test void declinedCaptureReleasesReservation() {
        var rejected = new PaymentService(new PaymentRepository(), command -> CaptureProcessor.Outcome.DECLINED);
        Payment payment = rejected.create(100, "USD", "create");
        rejected.authorize(payment.id(), "authorize");
        assertThat(rejected.capture(payment.id(), 100L, "capture").status()).isEqualTo(Capture.Status.DECLINED);
        assertThat(rejected.get(payment.id()).reservedAmount()).isZero();
        assertThat(rejected.cancel(payment.id(), "cancel").status()).isEqualTo(Payment.Status.CANCELED);
    }

    @Test void processorExceptionRetainsOperationIdForReconciliation() {
        var calls = new AtomicInteger();
        var ids = new java.util.ArrayList<UUID>();
        var uncertain = new PaymentService(new PaymentRepository(), command -> {
            ids.add(command.captureId());
            if (calls.incrementAndGet() == 1) throw new IllegalStateException("socket closed");
            return CaptureProcessor.Outcome.SUCCEEDED;
        });
        Payment payment = uncertain.create(100, "USD", "create");
        uncertain.authorize(payment.id(), "authorize");
        Capture pending = uncertain.capture(payment.id(), null, "capture");
        uncertain.reconcile(payment.id(), pending.id(), "reconcile");
        assertThat(ids).containsExactly(pending.id(), pending.id());
        assertThat(uncertain.get(payment.id()).capturedAmount()).isEqualTo(100);
    }

    @Test void racingCapturesEnforceRemainingAuthorization() throws Exception {
        Payment payment = authorized(1000);
        var results = Concurrently.run(10, i -> {
            try { service.capture(payment.id(), 200L, "capture-" + i); return true; }
            catch (ApiException rejected) { assertThat(rejected.status()).isEqualTo(409); return false; }
        });
        assertThat(results.stream().filter(Boolean::booleanValue).count()).isEqualTo(5);
        assertThat(service.get(payment.id()).capturedAmount()).isEqualTo(1000);
        assertThat(processor.chargeCount()).isEqualTo(5);
    }

    @Test void simultaneousSameKeyChargesOnce() throws Exception {
        Payment payment = authorized(1000);
        var results = Concurrently.run(10, i -> service.capture(payment.id(), 200L, "same"));
        assertThat(results).allMatch(results.getFirst()::equals);
        assertThat(processor.chargeCount()).isEqualTo(1);
    }

    @Test void validatesMoneyCurrencyKeysAndMissingPayments() {
        assertThatThrownBy(() -> service.create(0, "USD", "x")).isInstanceOf(ApiException.class);
        assertThatThrownBy(() -> service.create(1, "US", "x")).isInstanceOf(ApiException.class);
        assertThatThrownBy(() -> service.create(1, "USD", " ")).isInstanceOf(ApiException.class);
        assertThatThrownBy(() -> service.get(UUID.randomUUID())).isInstanceOf(ApiException.class);
        Payment payment = authorized(100);
        assertThatThrownBy(() -> service.capture(payment.id(), -1L, "negative")).isInstanceOf(ApiException.class);
        assertThat(service.get(payment.id())).isEqualTo(payment);
    }
}
