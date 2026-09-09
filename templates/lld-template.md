# LLD: <Problem Name>

> One-line answer: <core abstraction and the patterns used>

## 1. Requirements and scope
- In scope: ...
- Out of scope: ...
- Clarifying questions I would ask: ...

## 2. Core entities

```mermaid
classDiagram
    class Foo {
        -String id
        +doThing() Result
    }
    class Strategy {
        <<interface>>
        +apply() void
    }
    Foo --> Strategy : uses

    style Foo fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#111
    style Strategy fill:#fce7f3,stroke:#db2777,stroke-width:2px,color:#111
```

## 3. Patterns used

| Pattern | Where | Why |
|---|---|---|
| Strategy | ... | swap algorithm without touching callers |

## 4. Lifecycle

```mermaid
stateDiagram-v2
    [*] --> Created
    Created --> Active
    Active --> Done
    Done --> [*]
```

## 5. Code

```java
public interface Foo { }
```

## 6. Concurrency
- Shared mutable state: ...
- Locking strategy: ...
- Why this is safe: ...

## 7. Extensibility seams
- "If asked to add X" -> ...
