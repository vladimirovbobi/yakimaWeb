"""Scoped throttles per docs/ICD.md rate-limit table."""
from rest_framework.throttling import UserRateThrottle


class VoteThrottle(UserRateThrottle):
    scope = "vote"


class LeadThrottle(UserRateThrottle):
    scope = "lead"


class AIToolThrottle(UserRateThrottle):
    scope = "ai_tool"
