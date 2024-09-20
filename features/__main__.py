import signal

from joblib import Parallel, delayed
import pandas as pd
from tqdm import tqdm

from api.gerrit_api import GerritApi
from api.api_cache import ApiCache
from data.comment_meta import CommentMeta, load_comment_metas_from_dataset, load_comment_ids_from_dataset
from features.feature_extractor import FeatureExtractor
from labels.data_labeler import DataLabeler

LABELED_DATASET_PATH = "../turzo2023towards/dataset/labeled_dataset.xlsx"
OUTPUT_DATASET_PATH = "dataset.xlsx"
CHUNK_SIZE = 8


def init_services() -> tuple[ApiCache, GerritApi, DataLabeler, FeatureExtractor]:
    used_ids = load_comment_ids_from_dataset(LABELED_DATASET_PATH)
    cache = ApiCache()
    api = GerritApi("https://review.opendev.org", "openstack/nova", cache)
    labeler = DataLabeler(used_ids, api)
    extractor = FeatureExtractor(api)
    return cache, api, labeler, extractor


def load_metas_and_entries(labeler: DataLabeler) -> tuple[list[CommentMeta], list[dict]]:
    metas = [*load_comment_metas_from_dataset(LABELED_DATASET_PATH), *labeler.ready_comment_metas]
    entries = []
    try:
        entries = pd.read_excel(OUTPUT_DATASET_PATH).to_dict(orient="records")
        entry_ids = {e["meta.comment_id"] for e in entries}
        metas = [m for m in metas if m.comment_id not in entry_ids]
        print(f"Skipping {len(entries)} records from the previous run... "
              f"Delete {OUTPUT_DATASET_PATH} to perform a clean generation.")
    except FileNotFoundError:
        print("No previous dataset found, starting from scratch...")
    return metas, entries


def main():
    cache, _, labeler, extractor = init_services()
    metas, entries = load_metas_and_entries(labeler)

    stopped = False

    def exit_handler(*_) -> None:
        nonlocal stopped
        if not stopped:
            print("\tCTRL+C detected, stopping at the next possible point...")
            stopped = True
    signal.signal(signal.SIGINT, exit_handler)

    with tqdm(initial=len(entries), total=len(entries)+len(metas)) as t:
        t.refresh()
        for start in range(0, len(metas), CHUNK_SIZE):
            chunk = metas[start:start+CHUNK_SIZE]
            new_entries = Parallel(n_jobs=-1, backend="threading")(delayed(extractor.extract)(meta) for meta in chunk)
            entries.extend(e for e in new_entries if e is not None)
            if stopped:
                break
            t.set_postfix({"cached": cache.hit_ratio})
            t.update(len(chunk))

    df = pd.json_normalize(entries)
    df = df.sort_values(by="meta.comment_id")
    df.to_excel(OUTPUT_DATASET_PATH, index=False)
    print(f"Saved {len(entries)} records to {OUTPUT_DATASET_PATH}!")


if __name__ == "__main__":
    main()
