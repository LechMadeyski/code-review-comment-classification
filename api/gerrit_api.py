import json
import time
from base64 import b64decode
from functools import lru_cache
from urllib.parse import quote, urljoin
from urllib.request import urlopen
from urllib.error import HTTPError
from typing import Any, cast

from limits import strategies, storage, RateLimitItemPerSecond

from api.api_cache import ApiCache
from api.blame_info import BlameInfo
from api.change_info import ChangeInfo
from api.comment_info import CommentInfo
from data.candidate_meta import CandidateMeta

GERRIT_RES_PREFIX = b")]}'"
MAGIC_PATHS = ["/COMMIT_MSG", "/MERGE_LIST", "/PATCHSET_LEVEL"]
PAGE_SIZE = 500
LIMIT = RateLimitItemPerSecond(5, 10)


class GerritApi:
    def __init__(self, base_url: str, project_name: str, cache: ApiCache | None, /, *, debug=False) -> None:
        self._base_url = base_url
        self._project_name = project_name
        self._cache = cache
        self._debug = debug
        self._limiter = strategies.FixedWindowRateLimiter(storage.MemoryStorage())

    @lru_cache
    def get_comment_info(self, meta: CandidateMeta) -> CommentInfo | None:
        """
        Endpoint: https://review.opendev.org/Documentation/rest-api-changes.html#get-comment
        Example:  https://review.opendev.org/changes/639653/revisions/44230773a53a10867d1485d2e8937b7a3510fae8/comments/9fdfeff1_719b5072
        """

        try:
            return self._fetch_json(f"/changes/{meta.change_number}/revisions/{meta.revision_id}/comments/{meta.comment_id}")
        except:
            return None

    def get_code_old(self, meta: CandidateMeta) -> str:
        try:
            return self._fetch_code(meta, old=True)
        except HTTPError as e:
            if e.code == 404:  # the file was just created - it doesn't have an old version
                return ""
            raise e

    def get_code_new(self, meta: CandidateMeta) -> str:
        return self._fetch_code(meta, old=False)

    def get_change_info(self, meta: CandidateMeta) -> ChangeInfo:
        """
        Endpoint: https://review.opendev.org/Documentation/rest-api-changes.html#get-change
        Example:  https://review.opendev.org/changes/639653?o=DETAILED_ACCOUNTS
        """

        return self._fetch_json(f"/changes/{meta.change_number}?o=DETAILED_ACCOUNTS")

    def get_all_file_changes(self, file_path: str, cutoff_time: str) -> list[ChangeInfo]:
        """
        Endpoint: https://review.opendev.org/Documentation/rest-api-changes.html#list-changes
        Example:  https://review.opendev.org/changes/?q=status:merged+project:openstack/nova+branch:master+before:2024-05-15+mergedbefore:2024-05-15+file:{nova%2Ftests%2Funit%2Fimage%2Ftest_glance.py}&S=0&n=500
        """

        q = GerritApi._build_query({
            "status": "merged",
            "project": self._project_name,
            "branch": "master",
            "before": cutoff_time,
            "mergedbefore": cutoff_time,
            "file": file_path
        })

        changes: list[ChangeInfo] = []
        more_changes = True
        while more_changes:
            changes += self._fetch_json(f"/changes/?q={q}&n={PAGE_SIZE}")
            more_changes = len(changes) < 0 and "_more_changes" in changes[-1]
        return changes

    def get_candidate_changes(self, page: int = 0) -> list[ChangeInfo]:
        """
        Endpoint: https://review.opendev.org/Documentation/rest-api-changes.html#list-changes
        Example:  https://review.opendev.org/changes/?q=status:merged+project:openstack/nova+branch:master+extension:py&S=0&n=500
        """

        try:
            q = GerritApi._build_query({
                "status": "merged",
                "project": self._project_name,
                "branch": "master",
                "extension": "py"
            })

            return self._fetch_json(f"/changes/?q={q}&S={page * PAGE_SIZE}&n={PAGE_SIZE}")
        except:
            return []

    def get_comments_for_change(self, change_id: str) -> list[CommentInfo]:
        """
        Endpoint: https://review.opendev.org/Documentation/rest-api-changes.html#list-comments
        Example:  https://review.opendev.org/changes/openstack%2Fnova~master~Ia45013fc988acb9517aea42c3caa1fa45d63892e/comments
        """

        try:
            comments_by_path = self._fetch_json(f"/changes/{change_id}/comments")
            for magic_path in MAGIC_PATHS:
                comments_by_path.pop(magic_path, None)
            return [
                cast(CommentInfo, {**comment, "path": path})
                for path, comments in comments_by_path.items()
                for comment in comments
            ]
        except:
            return []

    def get_blame(self, meta: CandidateMeta, old: bool) -> list[BlameInfo]:
        """
        Endpoint: https://review.opendev.org/Documentation/rest-api-changes.html#get-blame
        Example: https://review.opendev.org/changes/openstack%2Fnova~909474/revisions/8/files/nova%2Ftests%2Funit%2Fimage%2Ftest_glance.py/blame?base=1
        """

        try:
            query = "?base=1" if old else ""
            return self._fetch_json(f"/changes/{meta.change_number}/revisions/{meta.revision_id}/files/{meta.file_id}/blame{query}")
        except:
            return []

    def assemble_comment_url(self, change_number: int, patchset: str, path: str, line: int | None) -> str:
        query = f"@{line}" if line else ""
        return urljoin(self._base_url, f"/c/{self._project_name}/+/{change_number}/{patchset}/{path}{query}")

    @staticmethod
    def _build_query(operators: dict[str, str]) -> str:
        return "+".join(f"{key}:{{{quote(value, safe='')}}}" for key, value in operators.items())

    def _fetch_text(self, endpoint: str) -> str:
        url = urljoin(self._base_url, endpoint)
        if self._debug:
            print("-> GET " + url)

        if self._cache and (cached := self._cache.get(url)):
            if self._debug:
                print("<- (cached)")
            return cached

        try:
            while not self._limiter.test(LIMIT):
                time.sleep(0.1)
            self._limiter.hit(LIMIT)

            with urlopen(url, timeout=60) as res:
                data = res.read().removeprefix(GERRIT_RES_PREFIX).decode("utf-8")
                if self._cache:
                    self._cache.set(url, data)
                if self._debug:
                    print("<- (fetched)")
                return data
        except Exception as e:
            if self._debug:
                print(f"<- (error: {e})")
            raise e

    def _fetch_json(self, endpoint: str) -> Any:
        return json.loads(self._fetch_text(endpoint))

    def _fetch_code(self, meta: CandidateMeta, old: bool) -> str:
        query = "?parent=1" if old else ""
        text = self._fetch_text(
            f"/changes/{meta.change_number}/revisions/{meta.revision_id}/files/{meta.file_id}/content{query}")
        return b64decode(text).decode("utf-8")
