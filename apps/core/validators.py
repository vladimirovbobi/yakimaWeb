"""Reusable model field validators."""
from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible


@deconstructible
class MaxFileSizeValidator:
    """Reject files larger than `max_mb` megabytes.

    Deconstructible so Django can serialize it into migrations cleanly.
    """

    def __init__(self, max_mb: int):
        self.max_mb = int(max_mb)

    def __call__(self, file):
        max_bytes = self.max_mb * 1024 * 1024
        size = getattr(file, "size", None)
        if size is None:
            return
        if size > max_bytes:
            raise ValidationError(f"File too large. Max {self.max_mb}MB.")

    def __eq__(self, other):
        return isinstance(other, MaxFileSizeValidator) and other.max_mb == self.max_mb

    def __hash__(self) -> int:
        return hash(("MaxFileSizeValidator", self.max_mb))


def validate_max_size_mb(max_mb: int):
    """Functional helper kept for parity with the spec doc."""
    return MaxFileSizeValidator(max_mb)
