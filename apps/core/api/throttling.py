"""Scoped throttles per docs/ICD.md rate-limit table.

Per-scope rates live in `config.settings.base.REST_FRAMEWORK.DEFAULT_THROTTLE_RATES`.
Each class here just declares the scope name; the framework looks up the rate
on each request and the `UserRateThrottle` base keys the bucket on user id.
"""
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle


class VoteThrottle(UserRateThrottle):
    scope = "vote"


class LeadThrottle(UserRateThrottle):
    scope = "lead"


class AIToolThrottle(UserRateThrottle):
    scope = "ai_tool"


class ImageCompressorThrottle(UserRateThrottle):
    """The compressor is local CPU (no $ cost) and users want to batch — give
    it a higher per-minute ceiling than the AI tools that hit Gemini."""
    scope = "image_compressor"


class CommentThrottle(UserRateThrottle):
    scope = "comment"


class ForumWriteThrottle(UserRateThrottle):
    scope = "forum_write"


class FlagThrottle(UserRateThrottle):
    scope = "flag"


class MessageThrottle(UserRateThrottle):
    scope = "message"


class FeaturedAnonThrottle(AnonRateThrottle):
    """Featured-services endpoint is public + cached, but should still cap
    anonymous traffic to defend against scrapers building a vendor list."""
    scope = "featured_anon"
