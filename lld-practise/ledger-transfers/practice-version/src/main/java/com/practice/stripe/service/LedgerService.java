package com.practice.stripe.service;

import com.practice.stripe.domain.*;
import com.practice.stripe.exception.ApiException;
import com.practice.stripe.repository.LedgerRepository;
import java.math.BigInteger;
import java.util.List;
import java.util.UUID;
import org.springframework.stereotype.Service;

@Service
public class LedgerService {
    private record Request(String operation, Object payload) {}
    private record Opening(String currency, long balance) {}
    private record Move(UUID sourceId, UUID destinationId, long amount) {}
    public record Audit(UUID accountId, long storedBalance, BigInteger rebuiltBalance, boolean consistent) {}
    private final LedgerRepository repository;
    public LedgerService(LedgerRepository repository) { this.repository = repository; }

    public Account createAccount(String currency, long openingBalance, String key) {
        String normalized = Checks.currency(currency);
        if (openingBalance < 0) throw ApiException.invalid("Opening balance cannot be negative");
        return repository.transaction(s -> s.idempotency.execute(key,
                new Request("account", new Opening(normalized, openingBalance)), Account.class, () -> {
                    Account account = new Account(UUID.randomUUID(), normalized, openingBalance, openingBalance);
                    s.accounts.put(account.id(), account);
                    return account;
                }));
    }

    public Account account(UUID id) { return repository.transaction(s -> requireAccount(s, id)); }
    public Transfer transfer(UUID id) { return repository.transaction(s -> requireTransfer(s, id)); }
    public List<Entry> entries() { return repository.transaction(s -> List.copyOf(s.entries)); }

    public Transfer transfer(UUID sourceId, UUID destinationId, long amount, String key) {
        return repository.transaction(s -> s.idempotency.execute(key,
                new Request("transfer", new Move(sourceId, destinationId, amount)), Transfer.class,
                () -> post(s, sourceId, destinationId, amount, null)));
    }

    public Transfer reverse(UUID transferId, String key) {
        return repository.transaction(s -> s.idempotency.execute(key,
                new Request("reverse", transferId), Transfer.class, () -> {
                    Transfer original = requireTransfer(s, transferId);
                    if (original.reversalOf() != null) throw ApiException.conflict("Cannot reverse a reversal");
                    if (original.reversedBy() != null) throw ApiException.conflict("Transfer already reversed");
                    Transfer reversal = post(s, original.destinationId(), original.sourceId(), original.amount(), original.id());
                    s.transfers.put(original.id(), original.reversedBy(reversal.id()));
                    return reversal;
                }));
    }

    private Transfer post(LedgerRepository.State state, UUID sourceId, UUID destinationId, long amount, UUID reversalOf) {
        Checks.positive(amount, "amount");
        if (sourceId != null && sourceId.equals(destinationId)) throw ApiException.invalid("Accounts must be different");
        Account source = requireAccount(state, sourceId);
        Account destination = requireAccount(state, destinationId);
        if (!source.currency().equals(destination.currency())) throw ApiException.invalid("Account currencies differ");
        if (source.balance() < amount) throw ApiException.conflict("Insufficient funds");
        long credited = Math.addExact(destination.balance(), amount);
        Transfer transfer = new Transfer(UUID.randomUUID(), sourceId, destinationId, amount, source.currency(), reversalOf, null);
        Entry debit = new Entry(UUID.randomUUID(), transfer.id(), sourceId, -amount, source.currency());
        Entry credit = new Entry(UUID.randomUUID(), transfer.id(), destinationId, amount, source.currency());
        // All checks and arithmetic finish before mutation, so a rejected transfer changes nothing.
        state.accounts.put(sourceId, source.withBalance(source.balance() - amount));
        state.accounts.put(destinationId, destination.withBalance(credited));
        state.entries.addAll(List.of(debit, credit));
        state.transfers.put(transfer.id(), transfer);
        return transfer;
    }

    public Audit audit(UUID accountId) {
        return repository.transaction(s -> {
            Account account = requireAccount(s, accountId);
            BigInteger rebuilt = BigInteger.valueOf(account.openingBalance());
            for (Entry entry : s.entries) {
                if (entry.accountId().equals(accountId)) rebuilt = rebuilt.add(BigInteger.valueOf(entry.amount()));
            }
            return new Audit(accountId, account.balance(), rebuilt, rebuilt.equals(BigInteger.valueOf(account.balance())));
        });
    }

    private Account requireAccount(LedgerRepository.State s, UUID id) {
        Account account = s.accounts.get(id);
        if (account == null) throw ApiException.missing("Account not found");
        return account;
    }
    private Transfer requireTransfer(LedgerRepository.State s, UUID id) {
        Transfer transfer = s.transfers.get(id);
        if (transfer == null) throw ApiException.missing("Transfer not found");
        return transfer;
    }
}
