from __future__ import annotations
from dataclasses import asdict, dataclass
from unittest import TestCase

import pandas as pd

from data.candidate_meta import CandidateMeta
from data.labels import Label


@dataclass(frozen=True, kw_only=True)
class CommentMeta(CandidateMeta):
    label: Label

    @property
    def feature_dict(self) -> dict:
        return {"comment_id": self.comment_id, "url": self.url, "label": self.label}

    @staticmethod
    def of(candidate: CandidateMeta, label: Label) -> CommentMeta:
        return CommentMeta(**asdict(candidate), label=label)


def load_comment_metas_from_dataset(dataset_path: str) -> list[CommentMeta]:
    df = pd.read_excel(dataset_path)
    return [CommentMeta(
        comment_id=row["comment_id"],
        revision_id=row["revision_id"],
        change_number=row["request_id"],
        file_path=row["file_name"],
        url=row["URL"],
        label=row["comment_group"]
    ) for _, row in df.iterrows()]


def load_comment_ids_from_dataset(dataset_path: str) -> set[str]:
    comments = load_comment_metas_from_dataset(dataset_path)
    return {c.comment_id for c in comments}


class TestCommentMeta(TestCase):
    def test_feature_dict(self):
        comment = CommentMeta(
            comment_id="9fdfeff1_719b5072",
            revision_id="44230773a53a10867d1485d2e8937b7a3510fae8",
            change_number="639653",
            file_path="nova/scheduler/client/report.py",
            url="https://review.opendev.org/c/openstack/nova/+/639653/3/nova/scheduler/client/report.py@1686",
            label="REFACTORING"
        )

        self.assertEqual(comment.feature_dict, {
            "comment_id": "9fdfeff1_719b5072",
            "url": "https://review.opendev.org/c/openstack/nova/+/639653/3/nova/scheduler/client/report.py@1686",
            "label": "REFACTORING"
        })

    def test_of(self):
        candidate = CandidateMeta(
            comment_id="9fdfeff1_719b5072",
            revision_id="44230773a53a10867d1485d2e8937b7a3510fae8",
            change_number="639653",
            file_path="nova/scheduler/client/report.py",
            url="https://review.opendev.org/c/openstack/nova/+/639653/3/nova/scheduler/client/report.py@1686"
        )

        self.assertEqual(
            CommentMeta.of(candidate, "REFACTORING"),
            CommentMeta(
                comment_id="9fdfeff1_719b5072",
                revision_id="44230773a53a10867d1485d2e8937b7a3510fae8",
                change_number="639653",
                file_path="nova/scheduler/client/report.py",
                url="https://review.opendev.org/c/openstack/nova/+/639653/3/nova/scheduler/client/report.py@1686",
                label="REFACTORING"
            )
        )
