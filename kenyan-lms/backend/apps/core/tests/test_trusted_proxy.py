"""Forwarded HTTPS headers are only accepted from the configured proxy."""
from django.test import RequestFactory, TestCase, override_settings

from apps.core.middleware import TrustedProxyHeaderMiddleware


class TrustedProxyHeaderTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.middleware = TrustedProxyHeaderMiddleware(lambda request: request)

    @override_settings(TRUSTED_PROXY_IPS=["10.0.0.1"])
    def test_untrusted_peer_loses_forwarded_headers(self):
        request = self.factory.get(
            "/", REMOTE_ADDR="203.0.113.9", HTTP_X_FORWARDED_PROTO="https",
            HTTP_X_FORWARDED_HOST="evil.example",
        )
        self.middleware(request)
        self.assertNotIn("HTTP_X_FORWARDED_PROTO", request.META)
        self.assertNotIn("HTTP_X_FORWARDED_HOST", request.META)

    @override_settings(TRUSTED_PROXY_IPS=["10.0.0.1"])
    def test_trusted_proxy_headers_are_kept(self):
        request = self.factory.get(
            "/", REMOTE_ADDR="10.0.0.1", HTTP_X_FORWARDED_PROTO="https"
        )
        self.middleware(request)
        self.assertEqual(request.META["HTTP_X_FORWARDED_PROTO"], "https")
