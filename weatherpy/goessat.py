from contextlib import contextmanager
from datetime import datetime

import netCDF4 as nc
from siphon.catalog import TDSCatalog


@contextmanager
def plotter(url):
    dataset = nc.Dataset(url)
    yield PlotSession(dataset)
    dataset.close()


class PlotSession(object):
    def __init__(self, dataset):
        self.dataset = dataset


class DataRequest(object):

    def __init__(self, sattype, sector, request_date=None):
        self.sector = sector
        self.sattype = sattype
        self._request_date = request_date
        self._initialize_request_date = datetime.utcnow().date()
        self._catalog = None
        self._catalog_datasets = None
        self._initialize_thredds_catalog()

    @property
    def request_date(self):
        return self._request_date or self._initialize_request_date

    @request_date.setter
    def request_date(self, newdate):
        self._request_date = newdate
        self._initialize_thredds_catalog()

    def _initialize_thredds_catalog(self):
        url = 'http://thredds.ucar.edu/thredds/catalog/satellite/{}/{}/{}/catalog.xml'.format(self.sattype, self.sector,
                                                                                              self._get_datestr())
        self._catalog = TDSCatalog(url)
        self._catalog_datasets = sorted(self._catalog.datasets.keys())

    def _get_datestr(self):
        if self._request_date is None:
            return 'current'
        else:
            return self._request_date.strftime('%Y%m%d')

    def __len__(self):
        return len(self._catalog_datasets)

    def __contains__(self, item):
        try:
            self._get_from_ts(item)
            return True
        except DatasetAccessException:
            return False

    def __getitem__(self, item):
        if isinstance(item, int):
            dataset_name = self._get_from_index(item)
        elif isinstance(item, datetime):
            dataset_name = self._get_from_ts(item)
        else:
            raise DatasetAccessException("Can only access dataset through an index or timestamp")
        return self._open(dataset_name)

    def __iter__(self):
        return iter(self._catalog_datasets)

    def __call__(self, dataset_name):
        if dataset_name not in self._catalog_datasets:
            raise DatasetAccessException("Invalid Dataset: {}".format(dataset_name))
        return self._open(dataset_name)

    def _get_from_index(self, index):
        try:
            return self._catalog_datasets[index]
        except IndexError:
            raise DatasetAccessException("Index: {} out of bounds of breadth of datasets".format(index))

    def _get_from_ts(self, ts):
        timestamp_str = ts.strftime('%Y%m%d_%H%M')
        for potential_dataset in self._catalog_datasets:
            if timestamp_str in potential_dataset:
                return potential_dataset
        raise DatasetAccessException("Dataset for timestamp: {} not found".format(ts))

    def _open(self, dataset_name, protocol='OPENDAP'):
        if protocol != 'OPENDAP':
            raise NotImplementedError("Only OPENDAP protocol supported at this time!")
        dataset = self._catalog.datasets[dataset_name]
        url = dataset.access_urls[protocol]
        return nc.Dataset(url)


class DatasetAccessException(Exception):
    pass
