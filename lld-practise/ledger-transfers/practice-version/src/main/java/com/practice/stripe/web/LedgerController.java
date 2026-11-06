package com.practice.stripe.web;

import com.practice.stripe.domain.*;
import com.practice.stripe.service.LedgerService;
import jakarta.validation.Valid;
import jakarta.validation.constraints.*;
import java.util.List;
import java.util.UUID;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.*;

@RestController
public class LedgerController {
    public record AccountRequest(@NotBlank String currency, @PositiveOrZero long openingBalance) {}
    public record TransferRequest(@NotNull UUID sourceId, @NotNull UUID destinationId, @Positive long amount) {}
    private final LedgerService service;
    public LedgerController(LedgerService service) { this.service = service; }

    @PostMapping("/accounts")
    @ResponseStatus(HttpStatus.CREATED)
    public Account create(@Valid @RequestBody AccountRequest request, @RequestHeader("Idempotency-Key") String key) {
        return service.createAccount(request.currency(), request.openingBalance(), key);
    }
    @GetMapping("/accounts/{id}")
    public Account account(@PathVariable UUID id) { return service.account(id); }
    @GetMapping("/accounts/{id}/audit")
    public LedgerService.Audit audit(@PathVariable UUID id) { return service.audit(id); }
    @PostMapping("/transfers")
    @ResponseStatus(HttpStatus.CREATED)
    public Transfer transfer(@Valid @RequestBody TransferRequest request, @RequestHeader("Idempotency-Key") String key) {
        return service.transfer(request.sourceId(), request.destinationId(), request.amount(), key);
    }
    @GetMapping("/transfers/{id}")
    public Transfer transfer(@PathVariable UUID id) { return service.transfer(id); }
    @PostMapping("/transfers/{id}/reversals")
    @ResponseStatus(HttpStatus.CREATED)
    public Transfer reverse(@PathVariable UUID id, @RequestHeader("Idempotency-Key") String key) { return service.reverse(id, key); }
    @GetMapping("/entries")
    public List<Entry> entries() { return service.entries(); }
}
