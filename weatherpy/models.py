from datetime import datetime, timedelta

import cartopy.crs as ccrs
import netCDF4 as nc
import numpy as np

import config
from weatherpy import uaplots
from weatherpy.maps import mappers
from weatherpy.thredds import DatasetAccessException


class GfsPlotter(object):

    plotvarmap = {
        uaplots.MSLP: 'prmslmsl'
    }

    # TODO: get the basetime from the dataset somehow
    def __init__(self, dataset, basetime):
        self.dataset = dataset
        self._wrapped_data = NcDatasetWrapper(dataset)
        self._basetime = basetime

        self._plot_cls = uaplots.MSLP
        self._lats = self._wrapped_data.dimension_values('lat')
        self._lons = self._wrapped_data.dimension_values('lon')
        self._hr = 0
        self._level = 'sfc'

    @property
    def plot(self):
        return self._plot_cls

    @plot.setter
    def plot(self, newcls):
        try:
            GfsPlotter.plotvarmap[newcls]
        except KeyError:
            raise ValueError("Unsupported plotter supplied. Try a different plot")
        self._plot_cls = newcls

    @property
    def hour(self):
        return self._hr

    @hour.setter
    def hour(self, newhr):
        self._hr = newhr

    @property
    def plevel(self):
        return self._level

    @plevel.setter
    def plevel(self, newplev):
        if newplev != 'sfc' and not isinstance(newplev, int):
            raise ValueError("Require a pressure level or \'sfc\'")
        self._level = newplev

    def default_map(self):
        return mappers.LargeScaleMap(ccrs.PlateCarree())

    def make_plot(self, mapper=None, colortable=None):
        if mapper is None:
            mapper = self.default_map()

        lats = self._wrapped_data.dimension_values('lat')
        lons = self._wrapped_data.dimension_values('lon')

        kwargs = {'time': self._basetime + timedelta(hours=self.hour)}
        if self.plevel != 'sfc':
            kwargs['lev'] = self.plevel
        data = self._wrapped_data.variable(GfsPlotter.plotvarmap[self.plot])(**kwargs)
        plot_instance = self.plot(data, lons, lats)

        plot_instance.make_plot(mapper, colortable)
        return mapper


def _reindex_lons(lon):
    if 180 < lon <= 360:
        return -360 + lon
    return lon


class NcDatasetWrapper(object):
    def __init__(self, data):
        self._data = data
        dims = tuple(dim for dim in self._data.dimensions)
        self._dim_values = {dim: data.variables[dim][:] for dim in dims}

    def dimension_values(self, dim):
        return self._dim_values[dim]

    def _get_index_of(self, dim, value):
        try:
            if isinstance(value, datetime):
                time_units = self._data.variables[dim].units
                value = nc.date2num(value, time_units)
            dim_values = self._dim_values[dim]
            return np.where(dim_values == value)[0][0]
        except KeyError:
            raise DatasetAccessException("Invalid dimension: {}".format(dim))
        except IndexError:
            raise DatasetAccessException("Could not find value: {} for dimension: {}".format(value, dim))

    def variable(self, varname):
        vardata = self._data.variables[varname]
        dims_for_var = vardata.dimensions

        def get_val(**kwargs):
            arg_indices = []
            for dim in dims_for_var:
                if dim in kwargs:
                    index = self._get_index_of(dim, kwargs[dim])
                    arg_indices.append(index)
                else:
                    # take all values from that dimension if caller does not
                    # request specific value for that dimension.
                    arg_indices.append(slice(None))
            return vardata[arg_indices]

        return get_val


class NcepModelRequest(object):
    path_map = {
        'gfs': 'gfs_0p25'
    }

    def __init__(self, model):
        self._model = model.lower()

    def _get_nomads_url(self, basetime):
        return '{base_url}/{path}/{model}{basedate}/' \
               '{path}_{basehour}z'.format(base_url=config.NOMADS_OPENDAP,
                                           path=NcepModelRequest.path_map[self._model],
                                           model=self._model,
                                           basedate=basetime.strftime('%Y%m%d'),
                                           basehour=basetime.strftime('%H'))

    def __getitem__(self, item):
        if isinstance(item, datetime):
            return self._get_nomads_url(item)
        else:
            raise ValueError("Index must be a datetime instance")


if __name__ == '__main__':
    import matplotlib.pyplot as plt
    req = NcepModelRequest('GFS')
    basetime = datetime(2017, 4, 10, 0, 0)
    ds = req[basetime]
    plotter = GfsPlotter(nc.Dataset(ds), basetime)
    mapper = plotter.default_map()
    mapper.extent = (-130, -60, 20, 55)
    plotter.make_plot(mapper)
    mapper.draw_default()
    plt.show()
