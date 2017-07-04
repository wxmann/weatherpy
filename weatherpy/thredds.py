import re
from datetime import datetime

import netCDF4


class DatasetAccessException(Exception):
    pass


class DatasetContextManager(object):
    def __init__(self, dataset):
        self.dataset = dataset

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return None

    def close(self):
        try:
            self.dataset.close()
        except:
            pass


def dap_plotter(catalog_ds, plotter):
    dap_url = catalog_ds.access_urls['OPENDAP']
    ds = netCDF4.Dataset(dap_url)
    return plotter(ds)