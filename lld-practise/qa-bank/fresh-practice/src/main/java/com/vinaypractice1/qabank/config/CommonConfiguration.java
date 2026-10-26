package com.vinaypractice1.qabank.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import java.time.Clock;

@Configuration
public class CommonConfiguration {

    @Bean
    public Clock clock() {
        return Clock.systemUTC();
    }
}
