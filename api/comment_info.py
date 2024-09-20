from typing import TypedDict
from typing_extensions import NotRequired

from api.account_info import AccountInfo
from api.comment_range import CommentRange


class CommentInfo(TypedDict):
    """
    The CommentInfo entity contains information about an inline comment.
    https://review.opendev.org/Documentation/rest-api-changes.html#comment-info
    """

    patch_set: NotRequired[str]
    """The patch set number for the comment; only set in contexts where comments may be returned for multiple patch sets."""

    id: str
    """The URL encoded UUID of the comment."""

    path: NotRequired[str]
    """
    The file path for which the inline comment was done.
    Not set if returned in a map where the key is the file path.
    """

    line: NotRequired[int]
    """
    The number of the line for which the comment was done.
    If range is set, this equals the end line of the range.
    If neither line nor range is set, it’s a file comment.
    """

    range: NotRequired[CommentRange]
    """The range of the comment as a CommentRange entity."""

    in_reply_to: NotRequired[str]
    """The URL encoded UUID of the comment to which this comment is a reply."""

    message: NotRequired[str]
    """The comment message."""

    author: NotRequired[AccountInfo]
    """
    The author of the message as an AccountInfo entity.
    Unset for draft comments, assumed to be the calling user.
    """

    commit_id: NotRequired[str]
    """Hex commit SHA-1 (40 characters string) of the commit of the patchset to which this comment applies."""
