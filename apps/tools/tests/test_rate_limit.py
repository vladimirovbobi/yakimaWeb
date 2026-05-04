"""Rate limiter unit tests."""
import pytest
from django.core.cache import cache

from apps.tools.models import Tool
from apps.tools.services.rate_limit import check_and_consume, usage_today


@pytest.fixture(autouse=True)
def _flush_cache():
    cache.clear()
    yield
    cache.clear()


@pytest.mark.django_db
class TestRateLimit:
    @pytest.fixture
    def tool(self):
        return Tool.objects.create(
            slug="test-tool", name="Test", description="x",
            model_id="gemini-2.5-flash", is_enabled=True,
            member_daily_limit=3, realtor_daily_limit=10,
        )

    def test_member_under_limit(self, user, tool):
        ok, reason = check_and_consume(user, tool)
        assert ok and reason == "ok"
        assert usage_today(user, tool) == 1

    def test_member_hits_limit(self, user, tool):
        for _ in range(3):
            assert check_and_consume(user, tool)[0]
        ok, reason = check_and_consume(user, tool)
        assert not ok and reason == "rate_limited"

    def test_realtor_higher_limit(self, realtor, tool):
        for _ in range(3):
            assert check_and_consume(realtor, tool)[0]
        # Member would be capped here, realtor isn't
        ok, _ = check_and_consume(realtor, tool)
        assert ok

    def test_disabled_tool_blocks(self, user, tool):
        tool.is_enabled = False
        tool.save()
        ok, reason = check_and_consume(user, tool)
        assert not ok and reason == "tool_disabled"

    def test_staff_bypass(self, staff, tool):
        for _ in range(20):
            ok, _ = check_and_consume(staff, tool)
            assert ok
