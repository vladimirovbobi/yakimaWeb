"""Audit tests — staff writes get logged, anon writes don't."""
import pytest

from apps.accounts.models import RealtorProfile
from apps.audit.models import ActionLog


@pytest.mark.django_db
class TestActionLogSignals:
    def test_staff_save_creates_log(self, staff, rf):
        from apps.audit.middleware import _local
        req = rf.get("/admin/")
        req.user = staff
        _local.request = req

        try:
            staff.full_name = "Updated"
            staff.save()
            logs = ActionLog.objects.filter(actor=staff)
            assert logs.exists()
            assert any("User.update" in log.action for log in logs)
        finally:
            _local.request = None

    def test_non_staff_save_skipped(self, user):
        from apps.audit.middleware import _local
        _local.request = None

        before = ActionLog.objects.count()
        user.full_name = "Member Update"
        user.save()
        # Non-staff user save should NOT create log
        assert ActionLog.objects.count() == before
