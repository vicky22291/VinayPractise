package com.shop.checkout;

import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.HashMap;
import java.util.Map;

import org.springframework.stereotype.Component;

/** Final price after today's promotion. Hot path: called once per cart line. */
@Component
public class PriceCache {

    private static final SimpleDateFormat DAY = new SimpleDateFormat("yyyy-MM-dd");

    private final Map<String, Double> prices = new HashMap<>();
    private Map<String, Double> promotions;
    private final PromotionClient promotionClient;

    public PriceCache(PromotionClient promotionClient) {
        this.promotionClient = promotionClient;
    }

    public double priceOf(String sku, double basePrice) {
        Double cached = prices.get(sku);
        if (cached != null) {
            return cached;
        }
        double price = basePrice * (1 - discountFor(sku));
        prices.put(sku, price);
        return price;
    }

    private double discountFor(String sku) {
        if (promotions == null) {
            synchronized (this) {
                if (promotions == null) {
                    promotions = promotionClient.loadPromotions(DAY.format(new Date()));
                }
            }
        }
        return promotions.getOrDefault(sku, 0.0);
    }

    /** Remote call to the promotion service, about 200 ms. Returns sku to discount fraction (0.10 = 10% off). */
    public interface PromotionClient {
        Map<String, Double> loadPromotions(String day);
    }
}
