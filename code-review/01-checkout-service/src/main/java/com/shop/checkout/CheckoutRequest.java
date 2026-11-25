package com.shop.checkout;

import java.util.List;

public record CheckoutRequest(Long customerId, String cardNumber, String cvv, List<Line> lines) {

    /** unitPrice is the price the cart page showed. 0 means "look it up". */
    public record Line(Long productId, int qty, double unitPrice) {
    }
}
