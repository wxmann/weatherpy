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
        uaplots.MSLP: 'prmslmsl',
        uaplots.GeopotentialHeight: 'hgtprs'
    }

    # TODO: get the basetime from the dataset somehow
    def __init__(self, dataset, basetime):
        self.dataset = dataset
        self._wrapped_data = NcDatasetWrapper(dataset)
        self._basetime = basetime

        self._lats = self._wrapped_data.dimension_values('lat')
        self._lons = self._wrapped_data.dimension_values('lon')
        self._hr = 0

    @property
    def hour(self):
        return self._hr

    @hour.setter
    def hour(self, newhr):
        self._hr = newhr

    def default_map(self):
        return mappers.LargeScaleMap(ccrs.PlateCarree())

    def plotter(self, plots, plevel='sfc', mapper=None):
        if mapper is None:
            mapper = self.default_map()

        if plevel != 'sfc' and not isinstance(plevel, int):
            raise ValueError("Invalid plevel argument: require a pressure level or \'sfc\'")

        lats = self._wrapped_data.dimension_values('lat')
        lons = self._wrapped_data.dimension_values('lon')

        kwargs = {'time': self._basetime + timedelta(hours=self.hour)}
        if plevel != 'sfc':
            kwargs['lev'] = plevel

        plotter_objs = []
        if not hasattr(plots, '__iter__'):
            plots = [plots]

        for plot in plots:
            data = self._wrapped_data.variable(GfsPlotter.plotvarmap[plot])(**kwargs)
            plotter_obj = plot(data, lons, lats, mapper)
            plotter_objs.append(plotter_obj)

        return tuple(plotter_objs) if len(plotter_objs) != 1 else plotter_objs[0]


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
    basetime = datetime(2017, 4, 11, 0, 0)
    ds = req[basetime]
    gfs = GfsPlotter(nc.Dataset(ds), basetime)

    mapper = gfs.default_map()
    mapper.extent = (-130, -60, 20, 55)
    mapper.draw_default()

    plotter = gfs.plotter(uaplots.GeopotentialHeight, 500, mapper)
    plotter.contours()

    plt.show()
