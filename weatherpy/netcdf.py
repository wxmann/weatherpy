import netCDF4


class netcdf_open(object):
    def __init__(self, dataset_source):
        self.dataset = netCDF4.Dataset(dataset_source)

    def __enter__(self):
        return self.dataset

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return None

    def close(self):
        try:
            self.dataset.close()
        except:
            pass