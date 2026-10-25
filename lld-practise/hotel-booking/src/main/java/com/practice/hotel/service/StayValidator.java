package com.practice.hotel.service;

import java.time.Instant;
import java.time.LocalDate;
import java.time.ZoneOffset;
import java.time.temporal.ChronoUnit;

import com.practice.hotel.domain.Stay;
import com.practice.hotel.error.InvalidStayException;

// The one place for the stay rules, shared by Create Reservation and the date filter of Search Hotels.
public final class StayValidator {

    public static final int MAX_NIGHTS = 30;
    // Inventory rows cover this many days from today, so checkOut can be at most this far ahead.
    public static final int MAX_DAYS_AHEAD = 365;

    private StayValidator() {
    }

    // The UTC date of requestTime, because hotels have no time zone yet.
    public static LocalDate today(Instant requestTime) {
        return LocalDate.ofInstant(requestTime, ZoneOffset.UTC);
    }

    public static Stay requireValidStay(LocalDate checkIn, LocalDate checkOut, Instant requestTime) {
        if (checkIn == null || checkOut == null) {
            throw new InvalidStayException("checkIn and checkOut must be sent together");
        }
        if (!checkOut.isAfter(checkIn)) {
            throw new InvalidStayException("checkOut must be after checkIn");
        }
        if (ChronoUnit.DAYS.between(checkIn, checkOut) > MAX_NIGHTS) {
            throw new InvalidStayException("a stay must be at most " + MAX_NIGHTS + " nights");
        }
        LocalDate today = today(requestTime);
        if (checkIn.isBefore(today)) {
            throw new InvalidStayException("checkIn must not be before today (" + today + ")");
        }
        if (checkOut.isAfter(today.plusDays(MAX_DAYS_AHEAD))) {
            throw new InvalidStayException("checkOut must be at most " + MAX_DAYS_AHEAD + " days after today (" + today + ")");
        }
        return new Stay(checkIn, checkOut);
    }
}
