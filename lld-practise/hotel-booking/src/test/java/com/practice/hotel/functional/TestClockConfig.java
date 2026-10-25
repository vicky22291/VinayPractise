package com.practice.hotel.functional;

import java.time.Clock;
import java.time.Instant;
import java.time.ZoneOffset;

import org.springframework.boot.test.context.TestConfiguration;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Primary;

@TestConfiguration(proxyBeanMethods = false)
public class TestClockConfig {

    public static final Instant NOW = Instant.parse("2026-10-24T09:15:02.123Z");

    @Bean
    @Primary
    Clock fixedClock() {
        return Clock.fixed(NOW, ZoneOffset.UTC);
    }
}
