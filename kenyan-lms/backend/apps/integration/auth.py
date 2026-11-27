"""Bearer authentication for read-only OneRoster clients."""
from rest_framework.authentication import BaseAuthentication, get_authorization_header
from rest_framework.exceptions import AuthenticationFailed

from apps.integration.clients import decode_assertion


class OneRosterAssertionAuthentication(BaseAuthentication):
    """Accept only a short-lived HS256 assertion from a configured client."""

    keyword = b"Bearer"

    def authenticate(self, request):
        header = get_authorization_header(request).split()
        if not header:
            return None
        if header[0].lower() != self.keyword.lower():
            raise AuthenticationFailed("Only bearer client assertions are accepted here.")
        if len(header) != 2:
            raise AuthenticationFailed("A single bearer client assertion is required.")
        try:
            token = header[1].decode("ascii")
        except UnicodeDecodeError as exc:
            raise AuthenticationFailed("The client assertion is not valid.") from exc

        result = decode_assertion(token)
        if result is None:
            raise AuthenticationFailed("A valid short-lived HS256 client assertion is required.")
        principal, claims = result
        return principal, {"client_id": principal.client_id, "jti": claims.get("jti", "")}

    def authenticate_header(self, request):
        return 'Bearer realm="OneRoster"'
