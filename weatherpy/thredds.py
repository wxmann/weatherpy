import re
from datetime import datetime

_THREDDS_TIMESTAMP_FORMAT = '%Y%m%d_%H%M'


class TimeBasedTDSRequest(object):
    def __init__(self, request_date=None):
        self._user_request_date = request_date
        self._current_date_utc = datetime.utcnow().date()
        self._catalog = None
        self._catalog_datasets = None
        self._initialize_thredds_catalog()
        self._check_catalog_initialized()

    @property
    def request_date(self):
        return self._user_request_date or self._current_date_utc

    @request_date.setter
    def request_date(self, newdate):
        self._user_request_date = newdate
        self._initialize_thredds_catalog()
        self._check_catalog_initialized()

    def _initialize_thredds_catalog(self):
        raise NotImplementedError("Catalog needs to be initialized in subclasses")

    def _check_catalog_initialized(self):
        if self._catalog is None or self._catalog_datasets is None:
            raise RuntimeError("Catalog is not properly initialized in TDS Request implementation")

    def __len__(self):
        return len(self._catalog_datasets)

    def __contains__(self, item):
        try:
            self._timestamp_to_dataset(item)
            return True
        except DatasetAccessException:
            return False

    def __getitem__(self, item):
        if isinstance(item, int):
            dataset_name = self._index_to_dataset(item)
        elif isinstance(item, datetime):
            dataset_name = self._timestamp_to_dataset(item)
        else:
            raise DatasetAccessException("Can only access dataset through an index or timestamp")
        return self._open(dataset_name)

    def __iter__(self):
        return iter(self._catalog_datasets)

    def __call__(self, dataset_name):
        if dataset_name not in self._catalog_datasets:
            raise DatasetAccessException("Invalid Dataset: {}".format(dataset_name))
        return self._open(dataset_name)

    def _index_to_dataset(self, index):
        try:
            return self._catalog_datasets[index]
        except IndexError:
            raise DatasetAccessException("Index: {} out of bounds of breadth of datasets".format(index))

    def _timestamp_to_dataset(self, ts):
        timestamp_str = ts.strftime(_THREDDS_TIMESTAMP_FORMAT)
        for potential_dataset in self._catalog_datasets:
            if timestamp_str in potential_dataset:
                return potential_dataset
        raise DatasetAccessException("Dataset for timestamp: {} not found".format(ts))

    def _open(self, dataset_name, protocol):
        raise NotImplementedError("This must be implemented in subclasses")


class DatasetAccessException(Exception):
    pass


def timestamp_from_dataset(dataset_name):
    match = re.search(r'\d{8}_\d{4}', dataset_name)
    matched_str = match.group(0)
    return datetime.strptime(matched_str, _THREDDS_TIMESTAMP_FORMAT)
