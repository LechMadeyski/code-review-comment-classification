from typing import TypedDict


class _SelectedLineRange(TypedDict):
    start_line: int
    end_line: int


class _FileLineRange(TypedDict):
    start_line: None
    end_line: None


LineRange = _SelectedLineRange | _FileLineRange
