import re
from datetime import datetime

THREDDS_TIMESTAMP_FORMAT = '%Y%m%d_%H%M'


class DatasetAccessException(Exception):
    pass


def timestamp_from_dataset(dataset_name):
    match = re.search(r'\d{8}_\d{4}', dataset_name)
    matched_str = match.group(0)
    return datetime.strptime(matched_str, THREDDS_TIMESTAMP_FORMAT)
