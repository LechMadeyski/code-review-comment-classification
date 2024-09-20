from dataclasses import dataclass
from urllib.parse import quote
from unittest import TestCase


@dataclass(frozen=True, kw_only=True)
class CandidateMeta:
    comment_id: str
    revision_id: str
    change_number: str
    file_path: str
    url: str

    @property
    def file_id(self) -> str:
        return quote(self.file_path, safe="")


class TestCandidateMeta(TestCase):
    def test_file_id(self):
        meta = CandidateMeta(
            comment_id="9fdfeff1_719b5072",
            revision_id="44230773a53a10867d1485d2e8937b7a3510fae8",
            change_number="639653",
            file_path="nova/scheduler/client/report.py",
            url="https://review.opendev.org/c/openstack/nova/+/639653/3/nova/scheduler/client/report.py@1686"
        )

        self.assertEqual(meta.file_id, "nova%2Fscheduler%2Fclient%2Freport.py")
