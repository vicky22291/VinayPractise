package com.practice.hotel.api;

import java.io.IOException;
import java.time.Clock;

import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.core.Ordered;
import org.springframework.core.annotation.Order;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

// Reads the clock once per request; everything after uses this value.
@Component
@Order(Ordered.HIGHEST_PRECEDENCE)
public class RequestTimeFilter extends OncePerRequestFilter {

    public static final String REQUEST_TIME_ATTRIBUTE = "requestTime";

    private final Clock clock;

    public RequestTimeFilter(Clock clock) {
        this.clock = clock;
    }

    @Override
    protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response, FilterChain chain)
            throws ServletException, IOException {
        request.setAttribute(REQUEST_TIME_ATTRIBUTE, clock.instant());
        chain.doFilter(request, response);
    }
}
