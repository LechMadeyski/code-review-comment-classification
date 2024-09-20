from typing import Any

from api.blame_info import BlameInfo
from api.change_info import ChangeInfo


def calculate_blame_metrics(blame: list[BlameInfo], owner_name: str, reviewer_name: str, start_line: int | None = None, end_line: int | None = None) -> dict[str, Any]:
    all_lines = _count_all_lines(blame)
    if start_line is None:
        start_line = 1
    if end_line is None:
        end_line = all_lines

    owner_lines = _count_lines_by_account(blame, owner_name, start_line, end_line)
    reviewer_lines = _count_lines_by_account(blame, reviewer_name, start_line, end_line)

    return {
        "by_owner": {
            "lines": owner_lines,
            "volume": owner_lines / all_lines if all_lines > 0 else 0
        },
        "by_reviewer": {
            "lines": reviewer_lines,
            "volume": reviewer_lines / all_lines if all_lines > 0 else 0
        }
    }


def _count_all_lines(blame: list[BlameInfo]) -> int:
    lines = 0
    for entry in blame:
        for range in entry["ranges"]:
            lines = max(lines, range["end"])
    return lines


def _count_lines_by_account(blame: list[BlameInfo], account_name: str, start_line: int, end_line: int) -> int:
    lines = 0
    for entry in blame:
        if entry["author"] == account_name:
            for range in entry["ranges"]:
                lines += max(min(range["end"], end_line) - max(range["start"], start_line) + 1, 0)
    return lines


def calculate_change_metrics(changes: list[ChangeInfo], owner_id: int, reviewer_id: int) -> dict[str, Any]:
    all_changes = len(changes)
    owner_changes = sum(1 for c in changes if c["owner"]["_account_id"] == owner_id)
    reviewer_changes = sum(1 for c in changes if c["owner"]["_account_id"] == reviewer_id)

    return {
        "count": all_changes,
        "unique_authors": len({c["owner"]["_account_id"] for c in changes}),
        "by_owner": {
            "count": owner_changes,
            "volume": owner_changes / all_changes if all_changes > 0 else 0
        },
        "by_reviewer": {
            "count": reviewer_changes,
            "volume": reviewer_changes / all_changes if all_changes > 0 else 0
        }
    }
