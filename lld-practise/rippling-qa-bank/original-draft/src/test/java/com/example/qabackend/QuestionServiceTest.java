package com.example.qabackend;

import com.example.qabackend.service.QuestionService;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;

import static org.junit.jupiter.api.Assertions.*;

@SpringBootTest
class QuestionServiceTest {

    @Autowired
    QuestionService service;

    @Test
    void createQuestion_success() {
        var q = service.createQuestion("Title", "Desc", "user1");
        assertNotNull(q.getId());
    }
}
