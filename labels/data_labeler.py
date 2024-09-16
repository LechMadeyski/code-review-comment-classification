from math import isnan
from dataclasses import asdict
from datetime import datetime
from itertools import count

import krippendorff

from api.gerrit_api import GerritApi
from data.candidate_meta import CandidateMeta
from data.comment_meta import CommentMeta
from data.labels import SkippableLabel, LABELS
from labels.candidate_entry import CandidateEntry
import labels.label_store as store


class DataLabeler:
    def __init__(self, used_ids: set[str], api: GerritApi) -> None:
        self._used_ids = used_ids
        self._api = api
        self._candidate_entries = self._aggregate_logs()

    @property
    def ready_comment_metas(self) -> list[CommentMeta]:
        return [
            CommentMeta.of(entry.meta, label)
            for entry in self._candidate_entries
            if (label := entry.resolved_label)
        ]

    @property
    def annotated_by_current_count(self) -> int:
        return len(store.read_current_annotator_log())

    @property
    def krippendorff_alpha(self) -> float:
        try:
            alpha = krippendorff.alpha(
                value_counts=[entry.label_counts for entry in self._candidate_entries],
                value_domain=LABELS,
                level_of_measurement="nominal",
            )
            return 0. if isnan(alpha) else alpha
        except:
            return 0.

    def get_current_target(self) -> CandidateMeta:
        # 1. Find candidates annotated by others, but not by me
        for entry in self._candidate_entries:
            if entry.my_label is None and entry.resolved_label is None:
                return entry.meta

        # 2. Find fresh candidates in the API
        used_ids = self._used_ids | {e.meta.comment_id for e in self._candidate_entries}
        for page in count():
            for change in self._api.get_candidate_changes(page):
                for comment in self._api.get_comments_for_change(change["id"]):
                    if comment["id"] in used_ids or not comment["message"] or "in_reply_to" in comment or not comment["path"].endswith(".py") or change["owner"]["_account_id"] == comment["author"]["_account_id"]:
                        continue
                    candidate = CandidateMeta(
                        comment_id=comment["id"],
                        revision_id=comment["commit_id"],
                        change_number=str(change["_number"]),
                        file_path=comment["path"],
                        url=self._api.assemble_comment_url(
                            change["_number"],
                            comment["patch_set"],
                            comment["path"],
                            comment.get("line", None),
                        )
                    )
                    if self._api.get_comment_info(candidate) is None:
                        continue
                    return candidate

        assert False, "unreachable, count() is an infinite iterator"

    def annotate_current_target(self, label: SkippableLabel) -> None:
        meta = self.get_current_target()

        entry = next((e for e in self._candidate_entries if e.meta == meta), None)
        if entry is None:
            entry = CandidateEntry(meta=meta, labels=[], my_label=None)
            self._candidate_entries.append(entry)

        entry.labels.append(label)
        entry.my_label = label

        log = store.read_current_annotator_log()
        log.append({
            "meta": asdict(meta),
            "timestamp": datetime.now().isoformat(),
            "label": label,
        })
        store.write_current_annotator_log(log)

    def _aggregate_logs(self) -> list[CandidateEntry]:
        candidates: dict[str, CandidateEntry] = {}
        updated_at: dict[str, str] = {}

        for annotator_log in store.read_all_annotator_logs():
            for log_entry in annotator_log:
                comment_id = log_entry["meta"]["comment_id"]
                if comment_id in candidates:
                    candidates[comment_id].labels.append(log_entry["label"])
                    updated_at[comment_id] = max(updated_at[comment_id], log_entry["timestamp"])
                else:
                    candidates[comment_id] = CandidateEntry(
                        meta=CandidateMeta(**log_entry["meta"]),
                        labels=[log_entry["label"]],
                        my_label=None
                    )
                    updated_at[comment_id] = log_entry["timestamp"]

        for log_entry in store.read_current_annotator_log():
            candidates[log_entry["meta"]["comment_id"]].my_label = log_entry["label"]

        return list(sorted(candidates.values(), key=lambda c: updated_at[c.meta.comment_id]))
