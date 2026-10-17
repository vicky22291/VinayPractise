"""In-memory stand-in for the processor's HTTP API, used by tests and the CLI.

It behaves like the real processor in the ways that matter here:
- every successful POST /v1/charges creates exactly one charge
- a request with an Idempotency-Key that was seen before returns the first
  response instead of creating a new charge
- tests can queue timeouts that happen before or after the processor did its work
"""


class FakeProcessor:
    def __init__(self):
        self.charges = []  # every charge actually created
        self.requests = []  # (path, body, headers) for every attempt
        self.timeouts = []  # queue of "before" | "after"
        self.decline_numbers = set()
        self._responses = {}  # Idempotency-Key -> first response

    def post(self, path, body, headers=None):
        headers = dict(headers or {})
        self.requests.append((path, dict(body), headers))
        mode = self.timeouts.pop(0) if self.timeouts else None
        if mode == "before":
            raise TimeoutError("processor did not answer in time")
        key = headers.get("Idempotency-Key")
        if key is not None and key in self._responses:
            response = self._responses[key]
        else:
            response = self._handle(path, body)
            if key is not None:
                self._responses[key] = response
        if mode == "after":
            raise TimeoutError("processor did not answer in time")
        return dict(response)

    def _handle(self, path, body):
        if path != "/v1/charges":
            return {"status": 404, "error": {"type": "invalid_request_error", "code": "not_found"}}
        if body["card_number"] in self.decline_numbers:
            return {"status": 402, "error": {"type": "card_error", "code": "card_declined"}}
        charge = {
            "id": f"ch_{len(self.charges) + 1}",
            "amount": body["amount"],
            "currency": body["currency"],
        }
        self.charges.append(charge)
        return {"status": 200, **charge}
