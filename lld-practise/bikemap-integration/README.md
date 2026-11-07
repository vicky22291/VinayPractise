# BikeMap integration Java practice

Open [practice-version](practice-version/README.md) for a standalone Java version of the [BikeMap integration exercise](../../ai-coding/03-bikemap-integration/README.md).

```mermaid
%% Candidate application integrates with a local vendor simulator
flowchart LR
    R["Recorded ride"] -->|read file| J["Java practice application"]
    J -->|HTTP requests| V["MapDraw local vendor"]
    V -->|response| J
    class R store
    class J service
    class V external
    classDef store fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#111
    classDef service fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    classDef external fill:#e5e7eb,stroke:#6b7280,stroke-width:2px,color:#111,stroke-dasharray:4 3
```

The workspace includes the existing ride fixture, full API reference, unchanged Python vendor simulator, and a Java starter. Read [TASK.md](practice-version/TASK.md) first. The five stages are revealed one at a time; there is no exercise solution in this workspace.

It uses the same Java 21, Spring Boot, Jackson, MapStruct, and test libraries as the other Stripe practice projects. Java's built-in HTTP client is configured in the starter. Maven runs the Java code; Python 3 runs only the local vendor.

The command line is the main interview surface. Spring Boot's `/health` and `/echo` endpoints are optional environment examples, not exercise requirements. This keeps API integration practice focused while retaining the familiar project setup.
