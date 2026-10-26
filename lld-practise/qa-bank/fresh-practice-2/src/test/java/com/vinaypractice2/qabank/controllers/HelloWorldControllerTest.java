package com.vinaypractice2.qabank.controllers;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.InstanceOfAssertFactories.map;

import com.vinaypractice2.qabank.controllers.HelloWorldController;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.test.web.servlet.assertj.MockMvcTester;

// Slice test: @WebMvcTest loads only this controller's web layer, so it starts faster than
// @SpringBootTest. If the controller gets a service, add it as a @MockitoBean field.
// MockMvcTester converts the JSON body back into an object, so we assert on data, not JSON paths.
@WebMvcTest(HelloWorldController.class)
class HelloWorldControllerTest {

    @Autowired
    MockMvcTester mvc;

    @Test
    void helloDefaultsToWorld() {
        assertThat(mvc.get().uri("/hello"))
                .hasStatusOk()
                .bodyJson()
                .convertTo(map(String.class, String.class))
                .containsEntry("message", "Hello, World!");
    }

    @Test
    void helloUsesNameParam() {
        assertThat(mvc.get().uri("/hello").param("name", "Vinay"))
                .hasStatusOk()
                .bodyJson()
                .convertTo(map(String.class, String.class))
                .containsEntry("message", "Hello, Vinay!");
    }
}
