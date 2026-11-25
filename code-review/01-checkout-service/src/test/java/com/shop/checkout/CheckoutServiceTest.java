package com.shop.checkout;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyDouble;
import static org.mockito.ArgumentMatchers.anyLong;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;

import java.util.List;
import java.util.Optional;

import org.junit.jupiter.api.Test;

class CheckoutServiceTest {

    @Test
    void placesOrder() throws Exception {
        ProductRepository products = mock(ProductRepository.class);
        OrderRepository orders = mock(OrderRepository.class);
        PaymentClient payments = mock(PaymentClient.class);
        PriceCache prices = mock(PriceCache.class);

        Product shoe = new Product(1L, "SKU-1", "Running shoe", 59.90, 5);
        when(products.findById(1L)).thenReturn(Optional.of(shoe));
        when(prices.priceOf("SKU-1", 59.90)).thenReturn(59.90);
        when(orders.save(any())).thenAnswer(inv -> {
            Order o = inv.getArgument(0);
            o.setId(42L);
            return o;
        });
        when(payments.charge(anyLong(), anyString(), anyString(), anyDouble())).thenReturn("ch_123");

        CheckoutService service = new CheckoutService(products, orders, mock(AuditRepository.class),
                payments, prices, mock(OrderEventPublisher.class), new OrderStats());

        Order order = service.placeOrder(new CheckoutRequest(7L, "4111111111111111", "123",
                List.of(new CheckoutRequest.Line(1L, 2, 0))));

        assertEquals(OrderStatus.PAID, order.getStatus());
        assertEquals(3, shoe.getStock());
    }
}
