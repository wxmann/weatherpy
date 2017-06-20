import re
from datetime import datetime

import netCDF4

THREDDS_TIMESTAMP_FORMAT = '%Y%m%d_%H%M'


class DatasetAccessException(Exception):
    pass


def timestamp_from_dataset(dataset_name):
    match = re.search(r'\d{8}_\d{4}', dataset_name)
    matched_str = match.group(0)
    return datetime.strptime(matched_str, THREDDS_TIMESTAMP_FORMAT)


class ThreddsDatasetPlotter(object):
    def __init__(self, dataset):
        self.dataset = dataset

    def close(self):
        self.dataset.close()


def dap_plotter(catalog_ds, plotter):
    dap_url = catalog_ds.access_urls['OPENDAP']
    ds = netCDF4.Dataset(dap_url)
    return plotter(ds)