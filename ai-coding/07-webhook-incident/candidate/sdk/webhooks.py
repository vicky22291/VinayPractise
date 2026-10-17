"""Verify the Hooks-Signature header on an incoming webhook.

    event = construct_event(request.body, request.headers["Hooks-Signature"], secret, now=int(time.time()))

Always pass the raw request body, never a re-encoded one.
"""
import hashlib
import hmac
import json

DEFAULT_TOLERANCE = 300  # seconds


class SignatureVerificationError(Exception):
    pass


def parse_header(header):
    timestamp, signatures = None, []
    for item in header.split(","):
        key, _, value = item.strip().partition("=")
        if key == "t":
            try:
                timestamp = int(value)
            except ValueError:
                timestamp = None
        elif key == "v1":
            signatures.append(value)
    if timestamp is None or not signatures:
        raise SignatureVerificationError("Unable to extract timestamp and signatures from header")
    return timestamp, signatures


def verify_signature(payload, header, secret, now, tolerance=DEFAULT_TOLERANCE):
    """Raise SignatureVerificationError unless `header` signs `payload` (bytes) recently enough."""
    timestamp, signatures = parse_header(header)
    expected = hmac.new(secret.encode(), f"{timestamp}.".encode() + payload, hashlib.sha256).hexdigest()
    if not any(hmac.compare_digest(expected, s) for s in signatures):
        raise SignatureVerificationError("No signatures found matching the expected signature for payload")
    if tolerance and now - timestamp > tolerance:
        raise SignatureVerificationError("Timestamp outside the tolerance zone")
    return True


def construct_event(payload, header, secret, now, tolerance=DEFAULT_TOLERANCE):
    """Verify, then decode the event."""
    verify_signature(payload, header, secret, now, tolerance)
    return json.loads(payload.decode("utf-8"))
