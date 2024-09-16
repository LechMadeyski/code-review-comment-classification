from typing import Any, Literal, TypeGuard

Label = Literal["DISCUSS", "DOCUMENTATION", "FALSE POSITIVE", "FUNCTION", "REFACTORING"]
SkippableLabel = Label | Literal["SKIP"]

LABELS: list[Label] = ["DISCUSS", "DOCUMENTATION", "FALSE POSITIVE", "FUNCTION", "REFACTORING"]
SKIPPABLE_LABELS: list[SkippableLabel] = LABELS + ["SKIP"]


def is_label(label: Any) -> TypeGuard[Label]:
    return label in LABELS


def is_skippable_label(label: Any) -> TypeGuard[SkippableLabel]:
    return label in SKIPPABLE_LABELS
