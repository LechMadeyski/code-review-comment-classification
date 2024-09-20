from typing import TypedDict
from typing_extensions import NotRequired


class CommentRange(TypedDict):
    """
    The CommentRange entity describes the range of an inline comment.
    https://review.opendev.org/Documentation/rest-api-changes.html#comment-range
    """

    start_line: int
    """The start line number of the range. (1-based)"""

    start_character: NotRequired[int]
    """The character position in the start line. (0-based)"""

    end_line: int
    """The end line number of the range. (1-based)"""

    end_character: NotRequired[int]
    """The character position in the end line. (0-based)"""
