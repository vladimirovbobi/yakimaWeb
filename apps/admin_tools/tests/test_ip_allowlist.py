"""IP allowlist middleware tests."""
import pytest
from django.test import override_settings

from apps.admin_tools.middleware import _ip_allowed


class TestIpAllowed:
    def test_exact_match(self):
        assert _ip_allowed("127.0.0.1", ["127.0.0.1"])
        assert not _ip_allowed("127.0.0.2", ["127.0.0.1"])

    def test_cidr(self):
        assert _ip_allowed("10.0.0.5", ["10.0.0.0/24"])
        assert not _ip_allowed("10.0.1.5", ["10.0.0.0/24"])

    def test_ipv6(self):
        assert _ip_allowed("::1", ["::1"])

    def test_invalid_ip_returns_false(self):
        assert not _ip_allowed("not.an.ip", ["127.0.0.1"])
        assert not _ip_allowed("", ["127.0.0.1"])

    def test_empty_allowlist_blocks_all(self):
        assert not _ip_allowed("127.0.0.1", [])
