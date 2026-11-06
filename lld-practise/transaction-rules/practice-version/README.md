# Transaction rule evaluator: Java practice

This folder is the standalone workspace for this question. Open its pom.xml as a Maven project in your IDE, read TASK.md, and start coding in src/.

## Commands

```bash
cd lld-practise/transaction-rules/practice-version
mvn test                     # starter tests and your exercise tests
mvn compile exec:java        # plain Java entry point: com.practice.stripe.Practice
mvn spring-boot:run          # optional HTTP server on port 8092
mvn package                  # build an executable JAR
```

For another port: `PORT=9000 mvn spring-boot:run`.

## Configured libraries

- Java 21 compilation, verified using the installed JDK 27.
- Spring Boot 3.5.16, Spring Web, Jackson, and Jakarta Validation.
- MapStruct 1.6.3 with annotation processing.
- JUnit 5, Mockito, AssertJ, and MockMvc.
- Java's built-in HttpClient for outbound HTTP requests.

`GET /health` and `POST /echo` are starter examples. The three starter tests check HTTP wiring, JSON with the generated MapStruct mapper, and invalid-input validation. Use requests.http in your IDE to try the endpoints.

## Practice

TASK.md contains only the initial requirements. The mock interviewer can reveal later stages from interviewer/FOLLOWUPS.md as you finish. There are no exercise solutions in this starter.

Allow 5 minutes for clarifications, 5 for a sketch, 35 for code and tests, and 10 for extensions and trade-offs.

| Date | First working version (min) | Stage reached | One thing to improve |
|---|---:|---|---|
| | | | |
