"""Voting + score sync + uniqueness tests."""
import pytest
from django.contrib.contenttypes.models import ContentType
from django.db import IntegrityError

from apps.forum.models import Flair, ForumThread, Vote


@pytest.mark.django_db
class TestVoting:
    @pytest.fixture
    def thread(self, user):
        flair = Flair.objects.create(slug="q", label="Question")
        return ForumThread.objects.create(
            author=user, flair=flair, title="Test", body="x"*10,
            moderation_status="approved",
        )

    def test_unique_vote_per_user(self, user, thread):
        ct = ContentType.objects.get_for_model(ForumThread)
        Vote.objects.create(target_type=ct, target_id=thread.pk, voter=user, value=1)
        with pytest.raises(IntegrityError):
            Vote.objects.create(target_type=ct, target_id=thread.pk, voter=user, value=-1)

    def test_value_constraint(self, user, thread):
        ct = ContentType.objects.get_for_model(ForumThread)
        with pytest.raises(IntegrityError):
            Vote.objects.create(target_type=ct, target_id=thread.pk, voter=user, value=0)

    def test_score_syncs_via_signal(self, user, realtor, thread):
        ct = ContentType.objects.get_for_model(ForumThread)
        Vote.objects.create(target_type=ct, target_id=thread.pk, voter=user, value=1)
        Vote.objects.create(target_type=ct, target_id=thread.pk, voter=realtor, value=1)
        thread.refresh_from_db()
        assert thread.score == 2

        # Flip one to downvote
        v = Vote.objects.get(voter=realtor)
        v.value = -1
        v.save()
        thread.refresh_from_db()
        assert thread.score == 0

    def test_delete_vote_decrements(self, user, thread):
        ct = ContentType.objects.get_for_model(ForumThread)
        v = Vote.objects.create(target_type=ct, target_id=thread.pk, voter=user, value=1)
        thread.refresh_from_db()
        assert thread.score == 1
        v.delete()
        thread.refresh_from_db()
        assert thread.score == 0


@pytest.mark.django_db
class TestHotScore:
    def test_higher_score_ranks_higher_at_same_age(self, user):
        flair = Flair.objects.create(slug="q", label="Question")
        a = ForumThread.objects.create(author=user, flair=flair, title="a", body="x"*10, score=100)
        b = ForumThread.objects.create(author=user, flair=flair, title="b", body="x"*10, score=10)
        assert a.hot_score > b.hot_score
