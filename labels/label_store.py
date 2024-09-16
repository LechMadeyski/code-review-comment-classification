import json
from pathlib import Path
from typing import TypedDict
from functools import lru_cache
import subprocess as sp

from data.labels import SkippableLabel

_DIR = Path(__file__).parent.resolve() / "annotations"
_TRANS = str.maketrans("@.", "--")


class AnnotatorLogEntry(TypedDict):
    meta: dict[str, str]
    timestamp: str
    label: SkippableLabel


def read_current_annotator_log() -> list[AnnotatorLogEntry]:
    path = _get_current_annotator_path()
    if not path.exists():
        return []
    with path.open("r") as f:
        return json.loads(f.read())


def write_current_annotator_log(log: list[AnnotatorLogEntry]) -> None:
    path = _get_current_annotator_path()
    with path.open("w") as f:
        f.write(json.dumps(log, indent=2))


def read_all_annotator_logs() -> list[list[AnnotatorLogEntry]]:
    logs = []
    for path in _DIR.iterdir():
        if path.is_file() and "".join(path.suffixes) == ".labels.json":
            with path.open("r") as f:
                logs.append(json.loads(f.read()))
    return logs


@lru_cache
def get_current_annotator_email() -> str:
    email_process = sp.run(["git", "config", "--global", "user.email"], capture_output=True)
    assert email_process.returncode == 0, "git not found in PATH"
    email = email_process.stdout.decode("utf-8").strip()
    assert len(email) > 0, "git email not set"
    return email


@lru_cache
def _get_current_annotator_path() -> Path:
    return _DIR / f"{get_current_annotator_email().translate(_TRANS)}.labels.json"
