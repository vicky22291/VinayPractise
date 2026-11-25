package com.shop.checkout;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/v2/checkout")
public class CheckoutController {

    private static final Logger log = LoggerFactory.getLogger(CheckoutController.class);

    private final CheckoutService checkout;

    public CheckoutController(CheckoutService checkout) {
        this.checkout = checkout;
    }

    @PostMapping
    public ResponseEntity<Order> checkout(@RequestBody CheckoutRequest req) {
        log.info("checkout request {}", req);
        try {
            Order order = checkout.placeOrder(req);
            return ResponseEntity.ok(order);
        } catch (Exception e) {
            log.error("checkout failed", e);
            return ResponseEntity.status(500).build();
        }
    }
}
