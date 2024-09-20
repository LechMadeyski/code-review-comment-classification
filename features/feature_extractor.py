from typing import Any
from unittest import TestCase

from api.gerrit_api import GerritApi
from api.comment_info import CommentInfo
from data.comment_meta import CommentMeta
from data.line_range import LineRange
from features.ast_utils import has_syntax_error, extract_context, calculate_code_metrics
from features.text_utils import extract_range, line_count, volume
from features.process_utils import calculate_blame_metrics, calculate_change_metrics


class FeatureExtractor:
    def __init__(self, api: GerritApi):
        self._api = api

    def extract(self, meta: CommentMeta) -> dict | None:
        change_info = self._api.get_change_info(meta)
        comment_info = self._api.get_comment_info(meta)
        if change_info is None or comment_info is None:
            return None

        owner_name = change_info["owner"]["name"]
        reviewer_name = comment_info["author"]["name"]

        comment = self.extract_comment_features(comment_info)
        line_range = self.extract_line_range(comment_info)

        code_old = self._api.get_code_old(meta)
        code_new = self._api.get_code_new(meta)

        blame_old = self._api.get_blame(meta, old=True)
        blame_new = self._api.get_blame(meta, old=False)

        if comment is None or has_syntax_error(code_old) or has_syntax_error(code_new):
            return None

        code_comment_side = code_old if comment["side"] == "PARENT" else code_new
        blame_comment_side = blame_old if comment["side"] == "PARENT" else blame_new

        code_range = extract_range(code_comment_side, **line_range)
        code_context, ctx_tree, ctx_start, ctx_end = extract_context(code_comment_side, **line_range)

        old_metrics = {
            **calculate_code_metrics(code_old),
            **calculate_blame_metrics(blame_old, owner_name, reviewer_name)
        }
        new_metrics = {
            **calculate_code_metrics(code_new),
            **calculate_blame_metrics(blame_new, owner_name, reviewer_name)
        }

        changes = calculate_change_metrics(
            self._api.get_all_file_changes(
                file_path=meta.file_path,
                cutoff_time=change_info["created"],
            ),
            change_info["owner"]["_account_id"],
            comment_info["author"]["_account_id"]
        )

        return {
            "meta": {**meta.feature_dict, **line_range},
            "comment": comment,
            "code": {
                "old": old_metrics,
                "new": new_metrics,
                "range": {
                    "text": code_range,
                    "volume": volume(code_range, code_comment_side),
                    "len": len(code_range),
                    "lines": line_count(code_range),
                    **calculate_blame_metrics(blame_comment_side, owner_name, reviewer_name, **line_range)
                },
                "context": {
                    "text": code_context,
                    "volume": volume(code_context, code_comment_side),
                    **calculate_code_metrics(code_context, ctx_tree),
                    **calculate_blame_metrics(blame_comment_side, owner_name, reviewer_name, ctx_start, ctx_end)
                },
                "diff": self._diff_features(old_metrics, new_metrics),
            },
            "changes": changes
        }

    @staticmethod
    def extract_comment_features(comment_info: CommentInfo) -> dict[str, Any] | None:
        text = comment_info.get("message", "").strip()
        if len(text) == 0:
            return None
        return {
            "text": text,
            "side": comment_info.get("side", "REVISION"),
            "len": len(text),
        }

    @staticmethod
    def extract_line_range(comment_info: CommentInfo) -> LineRange:
        if comment_range := comment_info.get("range"):
            start_line = comment_range["start_line"]
            end_line = comment_range["end_line"]
            if "end_character" in comment_range and comment_range["end_character"] == 0:
                end_line -= 1
            return {"start_line": start_line, "end_line": end_line}

        if line := comment_info.get("line"):
            return {"start_line": line, "end_line": line}

        return {"start_line": None, "end_line": None}

    @staticmethod
    def _diff_features(old_features: dict, new_features: dict) -> dict:
        result = {}
        common_keys = old_features.keys() & new_features.keys()

        for key in common_keys:
            old = old_features[key]
            new = new_features[key]

            if isinstance(old, int) or isinstance(old, float):
                result[key] = new - old
            elif isinstance(old, dict):
                result[key] = FeatureExtractor._diff_features(old, new)

        return result


class TestFeatureExtractor(TestCase):
    def test_extract_comment_features(self):
        fe = FeatureExtractor(None)

        self.assertEqual(fe.extract_comment_features(
            {"message": "Hello, world!"}),
            {"text": "Hello, world!", "side": "REVISION", "len": 13}
        )
        self.assertEqual(fe.extract_comment_features(
            {"message": "", "side": "PARENT"}),
            None
        )
        self.assertEqual(fe.extract_comment_features(
            {"message": "thanks", "side": "PARENT"}),
            {"text": "thanks", "side": "PARENT", "len": 6}
        )

    def test_extract_line_range(self):
        fe = FeatureExtractor(None)

        self.assertEqual(fe.extract_line_range(
            {"range": {"start_line": 1, "end_line": 2}}),
            {"start_line": 1, "end_line": 2}
        )
        self.assertEqual(fe.extract_line_range(
            {"range": {"start_line": 6, "start_character": 5, "end_line": 9, "end_character": 0}}),
            {"start_line": 6, "end_line": 8}
        )
        self.assertEqual(fe.extract_line_range(
            {"line": 3}),
            {"start_line": 3, "end_line": 3}
        )

    def test_diff_features(self):
        self.assertEqual(FeatureExtractor._diff_features(
            {"a": 3, "b": {"c": 4, "d": 5}},
            {"a": 5, "b": {"c": 0}}),
            {"a": 2, "b": {"c": -4}}
        )
