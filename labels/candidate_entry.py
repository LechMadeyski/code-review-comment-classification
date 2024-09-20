
from collections import Counter
from dataclasses import dataclass
from unittest import TestCase

from data.candidate_meta import CandidateMeta
from data.labels import Label, SkippableLabel, LABELS


@dataclass(kw_only=True)
class CandidateEntry:
    meta: CandidateMeta
    labels: list[SkippableLabel]
    my_label: SkippableLabel | None

    @property
    def resolved_label(self) -> Label | None:
        winners = [label for label, count in Counter(self.labels).items() if label != "SKIP" and count >= 2]
        if len(winners) != 1:
            return None
        return winners[0]

    @property
    def label_counts(self) -> list[int]:
        counter = Counter(self.labels)
        return [counter[label] for label in LABELS]


class TestCandidateEntry(TestCase):
    META = CandidateMeta(
        comment_id="9fdfeff1_719b5072",
        revision_id="44230773a53a10867d1485d2e8937b7a3510fae8",
        change_number="639653",
        file_path="nova/scheduler/client/report.py",
        url="https://review.opendev.org/c/openstack/nova/+/639653/3/nova/scheduler/client/report.py@1686"
    )

    def test_resolved_label(self):
        def assert_label(labels, expected):
            self.assertEqual(CandidateEntry(meta=self.META, labels=labels, my_label=None).resolved_label, expected)

        assert_label([], None)
        assert_label(["FALSE POSITIVE"], None)
        assert_label(["DISCUSS", "DISCUSS"], "DISCUSS")
        assert_label(["DISCUSS", "DISCUSS", "DISCUSS"], "DISCUSS")
        assert_label(["DISCUSS", "FUNCTION", "DOCUMENTATION", "FUNCTION"], "FUNCTION")
        assert_label(["SKIP", "SKIP", "SKIP"], None)
        assert_label(["SKIP", "SKIP", "DISCUSS"], None)
        assert_label(["REFACTOR", "REFACTOR", "DISCUSS", "DISCUSS"], None)

    def test_label_counts(self):
        def assert_counts(labels, expected):
            self.assertEqual(CandidateEntry(meta=self.META, labels=labels, my_label=None).label_counts, expected)

        assert_counts(LABELS, [1, 1, 1, 1, 1])
        assert_counts(["DISCUSS"], [1, 0, 0, 0, 0])
        assert_counts(["DOCUMENTATION"], [0, 1, 0, 0, 0])
        assert_counts(["FALSE POSITIVE"], [0, 0, 1, 0, 0])
        assert_counts(["FUNCTION"], [0, 0, 0, 1, 0])
        assert_counts(["REFACTORING"], [0, 0, 0, 0, 1])
        assert_counts(["SKIP"], [0, 0, 0, 0, 0])
        assert_counts(LABELS * 3, [3, 3, 3, 3, 3])
        assert_counts(["DISCUSS", "DISCUSS", "FUNCTION", "FUNCTION"], [2, 0, 0, 2, 0])
