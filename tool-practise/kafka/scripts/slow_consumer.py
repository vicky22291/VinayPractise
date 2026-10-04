"""Exercise 10: head-of-line blocking in a consumer group.

Consumes `tasks` as consumer group `task-runners`. A record whose value starts with
"slow" takes 20 s to process; everything else takes 0 s. Records are
processed one at a time, in offset order, which is the only way a
partition-ordered consumer can work without losing its place.

  python slow_consumer.py            # prints when each task finishes
"""
import time

from confluent_kafka import Consumer

c = Consumer({
    "bootstrap.servers": "kafka:19092",
    "group.id": "task-runners",
    "group.protocol": "consumer",          # KIP-848, the 4.x default to learn
    "enable.auto.commit": False,
    "auto.offset.reset": "earliest",
})
c.subscribe(["tasks"])
start = time.time()
idle = 0
while idle < 3:
    msg = c.poll(5.0)
    if msg is None:
        idle += 1
        continue
    if msg.error():
        raise SystemExit(msg.error())
    idle = 0
    value = msg.value().decode()
    produced = msg.timestamp()[1] / 1000
    if value.startswith("slow"):
        time.sleep(20)
    c.commit(message=msg, asynchronous=False)
    print(f"t+{time.time() - start:5.1f}s  p{msg.partition()} o{msg.offset()}  "
          f"{value:10} waited {time.time() - produced:5.1f}s since produce", flush=True)
c.close()
