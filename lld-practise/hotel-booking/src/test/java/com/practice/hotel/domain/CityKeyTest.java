package com.practice.hotel.domain;

import static org.assertj.core.api.Assertions.assertThat;

import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.CsvSource;

class CityKeyTest {

    @ParameterizedTest
    @CsvSource({"Mumbai", "' mumbai '", "MUMBAI"})
    void normalises(String city) {
        assertThat(CityKey.of(city)).isEqualTo(new CityKey("mumbai"));
    }
}
