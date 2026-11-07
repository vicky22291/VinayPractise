# Payment and invoice reconciliation: fresh coding practice

Minimal Spring Boot setup with Java 21, Maven, MapStruct 1.6.3, an Echo controller, and one MockMvc request/response test. The payment and invoice reconciliation exercise starts in [TASK.md](TASK.md).

Open this directory as a Maven project in your IDE, or run:

```bash
./scripts/build.sh  # clean and package an executable JAR; skips test execution
./scripts/test.sh   # run all tests
./scripts/run.sh    # start the server
```

The scripts work from any directory when invoked by path and forward additional arguments to Maven. Maven and JDK 21 or newer must be installed. Build output and test reports are under `target/`.

```bash
./scripts/test.sh -Dtest=EchoControllerTest  # run one test class
PORT=9000 ./scripts/run.sh                  # change the default port (8101)
```

Stop the server with Ctrl+C. You can also run `mvn test` and `mvn spring-boot:run` directly.

Try [requests.http](requests.http), or:

```bash
curl -X POST http://localhost:8101/echo \
  -H 'Content-Type: application/json' \
  -d '{"message":"hello practice"}'
```

Response (HTTP 200):

```json
{"message":"hello practice"}
```

`EchoControllerTest` sends this JSON through MockMvc, prints the request and response, and checks the status, content type, and response body. It loads the Spring Boot context without starting a server. The test-only Mockito configuration avoids agent self-attachment on restricted JDKs.

`EchoController` injects `EchoMapper`, a MapStruct mapper registered as a Spring bean. Maven generates its implementation during compilation using the configured annotation processor; the existing MockMvc test exercises it through `/echo`. Generated sources appear in `target/generated-sources/annotations`. Reload the Maven project in your IDE after updating dependencies.

Add your practice code under `src/main/java/com/practice/stripe` and tests under `src/test/java/com/practice/stripe`.

Start with the current stage in `TASK.md`. Later-stage prompts remain in the neighboring `../practice-version/interviewer/` folder for your coach to reveal when you are ready.
