package com.practice.hotel.domain;

import java.time.LocalDate;
import java.time.temporal.ChronoUnit;
import java.util.List;

// Nights run from checkIn (included) to checkOut (excluded). StayValidator checks the dates; this record never throws.
public record Stay(LocalDate checkIn, LocalDate checkOut) {

    public List<LocalDate> nights() {
        return checkIn.datesUntil(checkOut).toList();
    }

    public int nightCount() {
        return (int) ChronoUnit.DAYS.between(checkIn, checkOut);
    }
}
