from api.api_cache import ApiCache
from api.gerrit_api import GerritApi
from data.comment_meta import load_comment_ids_from_dataset
from labels.data_labeler import DataLabeler
from labels.server import run_server

LABELED_DATASET_PATH = "../turzo2023towards/dataset/labeled_dataset.xlsx"

if __name__ == "__main__":
    used_ids = load_comment_ids_from_dataset(LABELED_DATASET_PATH)

    api = GerritApi("https://review.opendev.org", "openstack/nova", ApiCache())
    labeler = DataLabeler(used_ids, api)

    run_server(api, labeler, port=8000)
