"""The Hooks-Signature header.

    Hooks-Signature: t=<unix seconds>,v1=<hex HMAC-SHA256 of "<t>." + body>

Receivers verify it with sdk.webhooks.verify_signature.
"""
import hashlib
import hmac

HEADER = "Hooks-Signature"
SCHEME = "v1"


def compute(secret, timestamp, payload):
    signed = f"{timestamp}.".encode() + payload
    return hmac.new(secret.encode(), signed, hashlib.sha256).hexdigest()


def sign(payload, secret, timestamp):
    """Header value for `payload` (bytes) signed at `timestamp`."""
    return f"t={timestamp},{SCHEME}={compute(secret, timestamp, payload)}"

