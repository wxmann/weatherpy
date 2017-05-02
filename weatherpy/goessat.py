from collections import OrderedDict
from contextlib import contextmanager
from datetime import datetime, timedelta

import netCDF4 as nc
import numpy as np
from siphon.catalog import TDSCatalog

from weatherpy import ctables
from weatherpy import logger
from weatherpy import maps
from weatherpy.internal import index_time_slice_helper, current_time_utc
from weatherpy.thredds import DatasetAccessException, timestamp_from_dataset


@contextmanager
def goesopen(url):
    dataset = nc.Dataset(url)
    try:
        yield GINIPlotter(dataset)
    finally:
        dataset.close()


class GINIPlotter(object):
    _KM_TO_M_MULTIPLIER = 1000

    def __init__(self, dataset):
        self.dataset = dataset
        self._sattype = self.dataset.keywords_vocabulary
        self._x = self.dataset.variables['x'][:]
        self._y = self.dataset.variables['y'][:]

        self._timestamp = self._get_timestamp()
        self._pixels = self._get_pixels()
        self._geog = self.dataset.variables['LambertConformal']

        self._lim = tuple(val * GINIPlotter._KM_TO_M_MULTIPLIER
                          for val in [min(self._x), max(self._x), min(self._y), max(self._y)])

        self._crs = maps.projections.lambertconformal(lat0=self._geog.latitude_of_projection_origin,
                                                      lon0=self._geog.longitude_of_central_meridian,
                                                      stdlat1=self._geog.standard_parallel,
                                                      r_earth=self._geog.earth_radius)
        logger.info("[GOES SAT] Finish processing satellite data")

    def _get_timestamp(self):
        timevar = self.dataset.variables['time']
        if len(timevar) != 1:
            raise ValueError("Invalid dataset! Contains no or more than one timestamps.")
        timeval = timevar[:][0]
        # Note: we do this funky thing since for some reason, the GINI time unit
        # format is incompatible with num2date function. Ay de mi! But we know it's
        # milliseconds since the Epoch, at least for now, so we'll just hardcode that.
        try:
            return nc.num2date(timeval, timevar.units)
        except ValueError:
            return nc.num2date(timeval, 'milliseconds since 1970-01-01T00:00:00Z')

    @property
    def timestamp(self):
        return self._timestamp

    @property
    def sattype(self):
        if self._sattype == 'IR_WV':
            return 'WV'
        return self._sattype

    def _get_pixels(self):
        plotvar = self.dataset.variables[self._sattype]
        if len(plotvar) != 1:
            raise ValueError("Invalid dataset! Contains no or more than one set of plot data.")

        pix = plotvar[0] & 0xff
        if self._sattype == 'IR':
            conversion = np.vectorize(pixel_to_temp, otypes=[np.float])
            return conversion(pix)
            # only need this snippet if using a colortable with K as units.
            # elif self.sattype == 'WV':
            # conversion = np.vectorize(functools.partial(pixel_to_temp, unit='K'), otypes=[np.float])
            # return conversion(pix)
        else:
            return pix

    def default_map(self):
        return maps.LargeScaleMap(self._crs)

    def default_ctable(self):
        if self._sattype == 'VIS':
            return ctables.vis.default
        elif self._sattype == 'IR':
            return ctables.ir.rainbow
        elif self._sattype == 'WV':
            return ctables.wv.accuwx
        else:
            return None

    def make_plot(self, mapper=None, colortable=None):
        if colortable is None:
            colortable = self.default_ctable()
        if mapper is None:
            mapper = self.default_map()
            mapper.initialize_drawing()

        mapper.ax.imshow(self._pixels, extent=self._lim, origin='upper',
                         transform=self._crs,
                         cmap=colortable.cmap, norm=colortable.norm)
        return mapper, colortable


def pixel_to_temp(pixel, unit='C'):
    r"""
    Converts pixel value to brightness temperature, according to the formula
    provided by http://www.goes.noaa.gov/enhanced.html.

    :param pixel: pixel brightness
    :param unit: unit of output temperature (C for Celsius, F for Fahrenheit, K for Kelvin)
    (default: Celsius)
    :return: brightness temperature
    """
    if pixel >= 176:
        tempK = 418 - pixel
    else:
        tempK = 330 - (pixel / 2)

    if unit == 'C':
        return tempK - 273.15
    elif unit == 'F':
        return (tempK - 273.15) * 1.8 + 32
    else:
        return tempK


class GoesDataRequest(object):
    def __init__(self, sattype, sector, protocol='OPENDAP'):
        self.sector = sector
        self.sattype = sattype.upper()
        self._protocol = protocol

    def _get_catalog_datasets(self, request_date=None):
        time_path = 'current' if request_date is None else request_date.strftime('%Y%m%d')
        catalog_url = 'http://thredds.ucar.edu/thredds/catalog/satellite/' \
                      '{}/{}/{}/catalog.xml'.format(self.sattype,
                                                    self.sector,
                                                    time_path)
        self._catalog = TDSCatalog(catalog_url)
        return OrderedDict((timestamp_from_dataset(k), k) for k in sorted(self._catalog.datasets.keys()))

    def __getitem__(self, item):
        if isinstance(item, int):
            return self._index_to_dataset(item)
        elif isinstance(item, datetime):
            return self._timestamp_to_dataset(item)
        elif isinstance(item, slice):
            return self._slice_to_dataset(item)
        else:
            raise DatasetAccessException("Can only access dataset through an index or timestamp")

    def _index_to_dataset(self, index, dataset_catalog=None):
        if dataset_catalog is None:
            dataset_catalog = self._get_catalog_datasets()
        try:
            found_datasets = list(dataset_catalog.values())[index]
            if isinstance(found_datasets, str):
                return self._open(found_datasets)
            return (self._open(ds) for ds in found_datasets)
        except IndexError:
            raise DatasetAccessException("Index: {} out of bounds of breadth of datasets".format(index))

    def _timestamp_to_dataset(self, ts, dataset_catalog=None):
        if dataset_catalog is None:
            dataset_catalog = self._get_catalog_datasets(ts.date())
        try:
            matching_dataset = dataset_catalog[ts]
            return self._open(matching_dataset)
        except KeyError:
            raise DatasetAccessException("Dataset for timestamp: {} not found".format(ts))

    def _slice_to_dataset(self, sliceobj):
        def ts_slice(slicearg):
            if slicearg.start is None:
                raise ValueError("Must provide a start timestamp for timestamp indexing")
            return self._iterable_for_ts_slice(slicearg)

        return index_time_slice_helper(self._index_to_dataset, ts_slice)(sliceobj)

    def _iterable_for_ts_slice(self, sliceobj):
        start = sliceobj.start
        stop = sliceobj.stop
        if stop is None:
            stop = current_time_utc()
        request_date = start.date()
        end_date = stop.date()
        while request_date <= end_date:
            cat = self._get_catalog_datasets(request_date)
            for k, v in cat.items():
                if start <= k < stop:
                    yield self._open(v)
            request_date += timedelta(days=1)

    def _open(self, dataset_name):
        if self._protocol != 'OPENDAP':
            raise NotImplementedError("Only OPENDAP protocol supported at this time!")
        dataset = self._catalog.datasets[dataset_name]
        return dataset.access_urls[self._protocol]
