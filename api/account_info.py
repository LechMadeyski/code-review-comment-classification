from typing import TypedDict
from typing_extensions import NotRequired


class AccountInfo(TypedDict):
    """
    The AccountInfo entity contains information about an account.
    https://review.opendev.org/Documentation/rest-api-accounts.html#account-info
    """

    _account_id: int
    """The numeric ID of the account."""

    name: NotRequired[str]
    """
    The full name of the user.
    Only set if detailed account information is requested.
    See option DETAILED_ACCOUNTS for change queries and option DETAILS for account queries.
    """
