"""Anomaly detector — hourly scan over ActionLog/AccessLog."""
from __future__ import annotations

import pytest
from django.contrib.auth import get_user_model

from apps.audit.models import AccessLog, ActionLog, Surface
from apps.audit.services import anomaly_detector

User = get_user_model()


@pytest.fixture
def staff_user(db):
    return User.objects.create_user(
        email="op@yakimaweb.local",
        password="x" * 12,
        is_staff=True,
    )


@pytest.mark.django_db
class TestMassWrites:
    def test_threshold_triggers_high_severity(self, staff_user):
        for _ in range(anomaly_detector.MASS_WRITES_THRESHOLD + 5):
            ActionLog.objects.create(
                actor=staff_user, action="content.Post.update"
            )
        findings = anomaly_detector.detect()
        mass = [f for f in findings if f.pattern == "mass_writes_by_staff"]
        assert mass, "expected mass_writes_by_staff finding"
        assert mass[0].severity == anomaly_detector.SEV_HIGH
        assert mass[0].evidence["writes_in_hour"] >= (
            anomaly_detector.MASS_WRITES_THRESHOLD + 1
        )

    def test_below_threshold_silent(self, staff_user):
        for _ in range(5):
            ActionLog.objects.create(actor=staff_user, action="x")
        findings = anomaly_detector.detect()
        assert not [
            f for f in findings if f.pattern == "mass_writes_by_staff"
        ]


@pytest.mark.django_db
class TestSharedIPMultiUser:
    def test_three_users_same_subnet_triggers(self, db):
        users = [
            User.objects.create_user(email=f"u{i}@x.local", password="x" * 12)
            for i in range(4)
        ]
        for u in users:
            AccessLog.objects.create(
                actor=u,
                surface=Surface.OPERATOR,
                path="/operator/",
                method="GET",
                status_code=200,
                ip="10.0.0.5",
            )
        findings = anomaly_detector.detect()
        shared = [
            f for f in findings if f.pattern == "shared_ip_multi_user"
        ]
        assert shared
        assert shared[0].severity == anomaly_detector.SEV_HIGH
        assert "10.0.0.0/24" in shared[0].target_id


@pytest.mark.django_db
class TestMassFlagging:
    def test_six_flags_in_hour_triggers(self, db):
        u = User.objects.create_user(email="r@x.local", password="x" * 12)
        for _ in range(anomaly_detector.MASS_FLAG_THRESHOLD + 1):
            ActionLog.objects.create(
                actor=u, action="moderation.Flag.create"
            )
        findings = anomaly_detector.detect()
        flag = [f for f in findings if f.pattern == "mass_flagging"]
        assert flag, "expected mass_flagging finding"
        assert flag[0].severity == anomaly_detector.SEV_MEDIUM


@pytest.mark.django_db
class TestVendorReviewSurge:
    def test_review_burst_triggers(self, db):
        u = User.objects.create_user(email="r2@x.local", password="x" * 12)
        for _ in range(anomaly_detector.VENDOR_REVIEW_THRESHOLD + 1):
            ActionLog.objects.create(
                actor=u,
                action="marketplace.Review.create",
                target_id=42,
            )
        findings = anomaly_detector.detect()
        rev = [f for f in findings if f.pattern == "vendor_review_surge"]
        assert rev
        assert "vendor:42" in rev[0].target_id


@pytest.mark.django_db
class TestNewAccountBurst:
    def test_new_account_with_writes_triggers_medium(self, db):
        u = User.objects.create_user(
            email="brand-new@x.local", password="x" * 12
        )
        for _ in range(anomaly_detector.NEW_ACCOUNT_WRITES_THRESHOLD + 1):
            ActionLog.objects.create(actor=u, action="content.Post.create")
        findings = anomaly_detector.detect()
        burst = [f for f in findings if f.pattern == "new_account_burst"]
        assert burst, "expected new_account_burst finding"
        assert burst[0].severity == anomaly_detector.SEV_MEDIUM


@pytest.mark.django_db
class TestEmptyState:
    def test_no_data_returns_empty(self):
        assert anomaly_detector.detect() == []


@pytest.mark.django_db
class TestSeverityTags:
    def test_all_findings_have_known_severity(self, staff_user):
        for _ in range(anomaly_detector.MASS_WRITES_THRESHOLD + 5):
            ActionLog.objects.create(actor=staff_user, action="x")
        for f in anomaly_detector.detect():
            assert f.severity in {
                anomaly_detector.SEV_LOW,
                anomaly_detector.SEV_MEDIUM,
                anomaly_detector.SEV_HIGH,
            }
