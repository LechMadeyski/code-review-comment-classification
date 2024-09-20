from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, Response
from fastapi.staticfiles import StaticFiles
import uvicorn

from api.gerrit_api import GerritApi
from data.labels import is_skippable_label
from features.feature_extractor import FeatureExtractor
from labels.data_labeler import DataLabeler
from labels.label_store import get_current_annotator_email

_CLIENT_DIR = Path(__file__).parent.resolve() / "client"


@dataclass(frozen=True, kw_only=True)
class TargetDto:
    id: str
    url: str
    startLine: int
    endLine: int
    content: str
    side: Literal["PARENT", "REVISION"]
    oldCode: str
    newCode: str


@dataclass(frozen=True, kw_only=True)
class InfoDto:
    currentAnnotatorEmail: str
    kirpendorffAlpha: float
    totalReadyCount: int
    annotatedByCurrentCount: int


def run_server(api: GerritApi, labeler: DataLabeler, port: int) -> None:
    def get_current_target() -> TargetDto:
        target = labeler.get_current_target()
        comment_info = api.get_comment_info(target)
        assert comment_info is not None
        comment = FeatureExtractor.extract_comment_features(comment_info)
        assert comment is not None
        line_range = FeatureExtractor.extract_line_range(comment_info)
        return TargetDto(
            id=target.comment_id,
            url=target.url,
            startLine=line_range["start_line"] or 0,
            endLine=line_range["end_line"] or 0,
            content=comment["text"],
            side=comment["side"],
            oldCode=api.get_code_old(target),
            newCode=api.get_code_new(target),
        )

    def annotate_current_target(label: str | None, res: Response) -> None:
        if not is_skippable_label(label):
            res.status_code = 400
            return
        labeler.annotate_current_target(label)

    def get_info() -> InfoDto:
        return InfoDto(
            currentAnnotatorEmail=get_current_annotator_email(),
            kirpendorffAlpha=labeler.krippendorff_alpha,
            totalReadyCount=len(labeler.ready_comment_metas),
            annotatedByCurrentCount=labeler.annotated_by_current_count,
        )

    server = FastAPI(docs_url="/api/swagger", openapi_url="/api/openapi.json", redoc_url=None)
    server.get("/api/target", tags=["API"])(get_current_target)
    server.put("/api/target", tags=["API"])(annotate_current_target)
    server.get("/api/info", tags=["API"])(get_info)
    server.mount("/", StaticFiles(directory=_CLIENT_DIR, html=True), name="static")

    try:
        print(f"Starting server at http://127.0.0.1:{port} (press CTRL+C to stop).")
        uvicorn.run(server, port=port, log_level="warning")
    except KeyboardInterrupt:
        print("Server stopped gracefully. Verify and commit your annotations.")
