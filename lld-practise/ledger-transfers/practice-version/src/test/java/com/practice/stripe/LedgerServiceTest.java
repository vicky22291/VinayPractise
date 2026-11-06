package com.practice.stripe;

import com.practice.stripe.domain.*;
import com.practice.stripe.exception.ApiException;
import com.practice.stripe.repository.LedgerRepository;
import com.practice.stripe.service.LedgerService;
import java.util.UUID;
import org.junit.jupiter.api.Test;
import static org.assertj.core.api.Assertions.*;

class LedgerServiceTest {
    private final LedgerService service = new LedgerService(new LedgerRepository());
    private final Account source = service.createAccount("usd", 1000, "source");
    private final Account destination = service.createAccount("USD", 0, "destination");

    @Test void transferIsBalancedAndRetryReturnsOriginalResult() {
        Transfer transfer = service.transfer(source.id(), destination.id(), 400, "move");
        assertThat(service.transfer(source.id(), destination.id(), 400, "move")).isEqualTo(transfer);
        assertThat(service.account(source.id()).balance()).isEqualTo(600);
        assertThat(service.account(destination.id()).balance()).isEqualTo(400);
        assertThat(service.entries()).extracting(Entry::amount).containsExactly(-400L, 400L);
        assertThat(service.entries()).allMatch(entry -> entry.transferId().equals(transfer.id()));
        assertThat(service.audit(source.id()).consistent()).isTrue();
        assertThat(service.audit(destination.id()).consistent()).isTrue();
    }

    @Test void rejectedTransfersChangeNeitherBalancesNorEntries() {
        Account eur = service.createAccount("EUR", 0, "eur");
        assertThatThrownBy(() -> service.transfer(source.id(), destination.id(), 1001, "overdraw")).hasMessageContaining("Insufficient");
        assertThatThrownBy(() -> service.transfer(source.id(), eur.id(), 1, "currency")).isInstanceOf(ApiException.class);
        assertThatThrownBy(() -> service.transfer(source.id(), source.id(), 1, "self")).isInstanceOf(ApiException.class);
        assertThatThrownBy(() -> service.transfer(source.id(), destination.id(), 0, "zero")).isInstanceOf(ApiException.class);
        assertThatThrownBy(() -> service.transfer(source.id(), UUID.randomUUID(), 1, "missing")).isInstanceOf(ApiException.class);
        assertThat(service.account(source.id())).isEqualTo(source);
        assertThat(service.account(destination.id())).isEqualTo(destination);
        assertThat(service.entries()).isEmpty();
    }

    @Test void overflowIsCheckedBeforeDebitingSource() {
        Account full = service.createAccount("USD", Long.MAX_VALUE, "full");
        assertThatThrownBy(() -> service.transfer(source.id(), full.id(), 1, "overflow")).isInstanceOf(ArithmeticException.class);
        assertThat(service.account(source.id())).isEqualTo(source);
        assertThat(service.account(full.id())).isEqualTo(full);
        assertThat(service.entries()).isEmpty();
    }

    @Test void reversalAppendsHistoryAndCannotBeRepeated() {
        Transfer original = service.transfer(source.id(), destination.id(), 400, "move");
        var originalEntries = service.entries();
        Transfer reversal = service.reverse(original.id(), "reverse");
        assertThat(reversal.reversalOf()).isEqualTo(original.id());
        assertThat(service.transfer(original.id()).reversedBy()).isEqualTo(reversal.id());
        assertThat(service.reverse(original.id(), "reverse")).isEqualTo(reversal);
        assertThatThrownBy(() -> service.reverse(original.id(), "another-key")).hasMessageContaining("already reversed");
        assertThatThrownBy(() -> service.reverse(reversal.id(), "reverse-reversal")).hasMessageContaining("Cannot reverse a reversal");
        assertThat(service.entries().subList(0, 2)).isEqualTo(originalEntries);
        assertThat(originalEntries).hasSize(2);
        assertThat(service.entries()).extracting(Entry::amount).containsExactly(-400L, 400L, -400L, 400L);
        assertThatThrownBy(() -> originalEntries.clear()).isInstanceOf(UnsupportedOperationException.class);
        assertThat(service.account(source.id())).isEqualTo(source);
        assertThat(service.account(destination.id())).isEqualTo(destination);
        assertThat(service.transfer(source.id(), destination.id(), 400, "move")).isEqualTo(original);
    }

    @Test void reversalNeedsFundsAndDoesNotMarkOriginalOnFailure() {
        Transfer original = service.transfer(source.id(), destination.id(), 400, "move");
        service.transfer(destination.id(), source.id(), 400, "spend");
        assertThatThrownBy(() -> service.reverse(original.id(), "reverse")).hasMessageContaining("Insufficient");
        assertThat(service.transfer(original.id()).reversedBy()).isNull();
        assertThat(service.entries()).hasSize(4);
        service.transfer(source.id(), destination.id(), 400, "refund-funding");
        assertThat(service.reverse(original.id(), "reverse").reversalOf()).isEqualTo(original.id());
    }

    @Test void conflictingIdempotencyKeysAreRejected() {
        service.transfer(source.id(), destination.id(), 400, "key");
        assertThatThrownBy(() -> service.transfer(source.id(), destination.id(), 401, "key")).hasMessageContaining("different request");
        assertThatThrownBy(() -> service.reverse(UUID.randomUUID(), "key")).hasMessageContaining("different request");
        assertThat(service.entries()).hasSize(2);
    }

    @Test void racingTransfersCannotOverdrawAndRemainBalanced() throws Exception {
        var results = Concurrently.run(20, i -> {
            try { service.transfer(source.id(), destination.id(), 100, "transfer-" + i); return true; }
            catch (ApiException rejected) { assertThat(rejected.status()).isEqualTo(409); return false; }
        });
        assertThat(results.stream().filter(Boolean::booleanValue).count()).isEqualTo(10);
        assertThat(service.account(source.id()).balance()).isZero();
        assertThat(service.account(destination.id()).balance()).isEqualTo(1000);
        assertThat(service.entries()).hasSize(20);
        assertThat(service.entries().stream().mapToLong(Entry::amount).sum()).isZero();
        assertThat(service.audit(source.id()).consistent()).isTrue();
        assertThat(service.audit(destination.id()).consistent()).isTrue();
    }

    @Test void racingReversalsAppendExactlyOneCorrection() throws Exception {
        Transfer original = service.transfer(source.id(), destination.id(), 400, "move");
        var results = Concurrently.run(10, i -> {
            try { service.reverse(original.id(), "reverse-" + i); return true; }
            catch (ApiException rejected) { assertThat(rejected.status()).isEqualTo(409); return false; }
        });
        assertThat(results.stream().filter(Boolean::booleanValue).count()).isEqualTo(1);
        assertThat(service.entries()).hasSize(4);
        assertThat(service.account(source.id())).isEqualTo(source);
    }

    @Test void simultaneousSameKeyTransfersOnce() throws Exception {
        var results = Concurrently.run(10, i -> service.transfer(source.id(), destination.id(), 400, "move"));
        assertThat(results).allMatch(results.getFirst()::equals);
        assertThat(service.entries()).hasSize(2);
    }
}
