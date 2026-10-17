"""The JSON body merchants receive."""
import json

API_VERSION = "2026-09-30"


def envelope(event, delivery_id, attempt):
    return {
        "id": delivery_id,
        "object": "event",
        "api_version": API_VERSION,
        "type": event.type,
        "account": event.account_id,
        "created": event.created,
        "data": {"object": event.data},
        "request": {"attempt": attempt},
    }


def to_bytes(envelope):
    # Compact UTF-8. About 15% smaller than the default encoding on our traffic.
    return json.dumps(envelope, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
