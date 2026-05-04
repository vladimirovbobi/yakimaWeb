"""Scoped throttles per docs/ICD.md rate-limit table."""
from rest_framework.throttling import UserRateThrottle


class VoteThrottle(UserRateThrottle):
    scope = "vote"


class LeadThrottle(UserRateThrottle):
    scope = "lead"


class AIToolThrottle(UserRateThrottle):
    scope = "ai_tool"


class CommentThrottle(UserRateThrottle):
    scope = "comment"


class ForumWriteThrottle(UserRateThrottle):
    scope = "forum_write"


class FlagThrottle(UserRateThrottle):
    scope = "flag"


class MessageThrottle(UserRateThrottle):
    scope = "message"
