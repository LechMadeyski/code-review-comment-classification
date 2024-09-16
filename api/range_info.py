from typing import TypedDict


class RangeInfo(TypedDict):
    """
    The RangeInfo entity stores the coordinates of a range.
    https://review.opendev.org/Documentation/rest-api-changes.html#range-info
    """

    start: int
    """First index."""

    end: int
    """Last index."""
