package com.practice.stripe.web;

import com.practice.stripe.domain.*;
import com.practice.stripe.service.ProrationCalculator;
import jakarta.validation.Valid;
import jakarta.validation.constraints.*;
import java.time.Instant;
import java.util.List;
import org.springframework.web.bind.annotation.*;

@RestController
public class ProrationController {
    public record Request(@NotBlank String currency, @NotNull Instant start, @NotNull Instant end,
                          @NotNull Plan initial, @NotNull List<PlanChange> changes,
                          @Min(0) @Max(10000) int discountBasisPoints) {}
    private final ProrationCalculator calculator;
    public ProrationController(ProrationCalculator calculator) { this.calculator = calculator; }

    @PostMapping("/prorations")
    public Proration calculate(@Valid @RequestBody Request request) {
        return calculator.calculate(request.currency(), request.start(), request.end(), request.initial(), request.changes(), request.discountBasisPoints());
    }
}
