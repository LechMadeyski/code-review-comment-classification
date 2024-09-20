from typing import TypedDict

from api.range_info import RangeInfo


class BlameInfo(TypedDict):
    """
    The BlameInfo entity stores the commit metadata with the row coordinates where it applies.
    https://review.opendev.org/Documentation/rest-api-changes.html#blame-info
    """

    author: str
    """The author of the commit."""

    ranges: list[RangeInfo]
    """The blame row coordinates as RangeInfo entities."""
