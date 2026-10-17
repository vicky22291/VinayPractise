"""Status codes by name, so code can say `codes.temporary_redirect` instead of 307.

Every name is also available in upper case: `codes.OK == codes.ok == 200`.
"""

_codes = {
    200: ("ok", "okay", "all_ok"),
    201: ("created",),
    202: ("accepted",),
    204: ("no_content",),
    301: ("moved_permanently", "moved"),
    302: ("found",),
    303: ("see_other", "other"),
    304: ("not_modified",),
    307: ("temporary_redirect", "temporary_moved"),
    308: ("permanent_redirect",),
    400: ("bad_request", "bad"),
    401: ("unauthorized",),
    403: ("forbidden",),
    404: ("not_found",),
    405: ("method_not_allowed",),
    408: ("request_timeout",),
    409: ("conflict",),
    413: ("request_entity_too_large",),
    429: ("too_many_requests",),
    500: ("internal_server_error", "server_error"),
    502: ("bad_gateway",),
    503: ("service_unavailable", "unavailable"),
    504: ("gateway_timeout",),
}


class _Codes:
    def __getitem__(self, key):
        return getattr(self, key, None)

    def __repr__(self):
        return "<lookup 'status_codes'>"


codes = _Codes()
for _code, _titles in _codes.items():
    for _title in _titles:
        setattr(codes, _title, _code)
        setattr(codes, _title.upper(), _code)

REDIRECT_STATI = (
    codes.moved,
    codes.found,
    codes.other,
    codes.temporary_redirect,
    codes.permanent_redirect,
)
