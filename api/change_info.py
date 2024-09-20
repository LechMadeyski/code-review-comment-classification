from typing import TypedDict
from typing_extensions import NotRequired

from api.account_info import AccountInfo


class ChangeInfo(TypedDict):
    """
    The ChangeInfo entity contains information about a change.
    https://review.opendev.org/Documentation/rest-api-changes.html#change-info
    """

    id: str
    """The ID of the change in the format "'<project>~<branch>~<Change-Id>'", where 'project' and 'branch' are URL encoded."""

    created: str
    """The timestamp of when the change was created."""

    _number: int
    """The change number."""

    owner: AccountInfo
    """The owner of the change as an AccountInfo entity."""

    current_revision: NotRequired[str]
    """
    The commit ID of the current patch set of this change.
    Only set if the current revision is requested or if all revisions are requested.
    """

    _more_changes: bool
    """
    Whether the query would deliver more results if not limited. Only set on the last change that is returned.
    """
