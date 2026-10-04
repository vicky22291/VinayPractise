-- Exercise 11. Two tables: one captured as plain CDC, one used as a transactional outbox.
CREATE TABLE accounts (
  id      int PRIMARY KEY,
  owner   text NOT NULL,
  balance int  NOT NULL
);

CREATE TABLE payments (
  id     text PRIMARY KEY,
  amount int  NOT NULL,
  state  text NOT NULL
);

-- Debezium's outbox event router reads these column names by default.
CREATE TABLE outbox (
  id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  aggregatetype text  NOT NULL,   -- picks the topic: outbox.event.<aggregatetype>
  aggregateid   text  NOT NULL,   -- becomes the Kafka key: per-payment order
  type          text  NOT NULL,   -- event name, copied into a header
  payload       jsonb NOT NULL
);
