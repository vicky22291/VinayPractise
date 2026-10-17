from hooks.clock import FakeClock
from hooks.dispatcher import Dispatcher
from hooks.models import Endpoint
from hooks.transport import FakeTransport, Response

T0 = 1_791_968_400  # 2026-10-14T09:00:00Z
SECRET = "whsec_test_123"


def make_dispatcher(*endpoints):
    clock = FakeClock(T0)
    transport = FakeTransport()
    d = Dispatcher(transport, clock)
    for ep in endpoints or [Endpoint("we_1", "acct_1", "https://merchant.example/hooks", SECRET)]:
        d.endpoints.add(ep)
        transport.route(ep.url, lambda body, headers: Response(200, "ok"))
    return d, transport, clock
