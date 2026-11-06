package com.practice.stripe.config;

import com.practice.stripe.domain.RetryPolicy;
import java.time.Clock;
import java.time.Duration;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class DeliveryConfig {
    @Bean public Clock clock() { return Clock.systemUTC(); }
    @Bean public RetryPolicy retryPolicy() {
        return new RetryPolicy(3, Duration.ofSeconds(1), Duration.ofMinutes(1), Duration.ofSeconds(30));
    }
}
