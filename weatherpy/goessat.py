from contextlib import contextmanager

import netCDF4 as nc
import numpy as np
from siphon.catalog import TDSCatalog

from weatherpy import colortables
from weatherpy import mapproj
from weatherpy.thredds import TimeBasedTDSRequest


@contextmanager
def plotter(url, sattype):
    dataset = nc.Dataset(url)
    try:
        yield GINIPlotter(dataset, sattype)
    finally:
        dataset.close()


class GINIPlotter(object):
    _KM_TO_M_MULTIPLIER = 1000

    def __init__(self, dataset, sattype):
        self.dataset = dataset
        self.sattype = sattype.upper()
        self._x = self.dataset.variables['x'][:]
        self._y = self.dataset.variables['y'][:]

        self._timestamp = self._get_timestamp()
        self._pixels = self._get_pixels()
        self._geog = self.dataset.variables['LambertConformal']

        self._map = self.default_map()

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

    def _get_pixels(self):
        var = 'IR_WV' if self.sattype == 'WV' else self.sattype
        plotvar = self.dataset.variables[var]
        if len(plotvar) != 1:
            raise ValueError("Invalid dataset! Contains no or more than one set of plot data.")

        pix = plotvar[0] & 0xff
        if self.sattype == 'IR':
            conversion = np.vectorize(pixel_to_temp, otypes=[np.float])
            return conversion(pix)
            # only need this snippet if using a colortable with K as units.
            # elif self.sattype == 'WV':
            # conversion = np.vectorize(functools.partial(pixel_to_temp, unit='K'), otypes=[np.float])
            # return conversion(pix)
        else:
            return pix

    @property
    def pixels(self):
        return self._pixels

    @property
    def lim(self):
        return tuple(val * GINIPlotter._KM_TO_M_MULTIPLIER
                     for val in [min(self._x), max(self._x), min(self._y), max(self._y)])

    def default_map(self):
        return mapproj.lambertconformal(lat0=self._geog.latitude_of_projection_origin,
                                        lon0=self._geog.longitude_of_central_meridian,
                                        stdlat1=self._geog.standard_parallel,
                                        r_earth=self._geog.earth_radius)

    def make_plot(self, mapper=None, colortable=None):
        bw = colortable is None or self.sattype == 'VIS'
        colortable_to_use = colortables.vis_depth if bw else colortable

        if mapper is None:
            mapper = self.default_map()
        mapper.initialize_drawing()
        mapper.ax.imshow(self.pixels, extent=self.lim, origin='upper',
                         transform=self._map.crs,
                         cmap=colortable_to_use.cmap, norm=colortable_to_use.norm)
        return mapper


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


class GoesDataRequest(TimeBasedTDSRequest):
    def __init__(self, sattype, sector, request_date=None):
        self.sector = sector
        self.sattype = sattype.upper()
        super(GoesDataRequest, self).__init__(request_date)

    def _initialize_thredds_catalog(self):
        catalog_url = 'http://thredds.ucar.edu/thredds/catalog/satellite/' \
                      '{}/{}/{}/catalog.xml'.format(self.sattype,
                                                    self.sector,
                                                    GoesDataRequest._str_from_timestamp(self._user_request_date))
        self._catalog = TDSCatalog(catalog_url)
        self._catalog_datasets = sorted(self._catalog.datasets.keys())

    @staticmethod
    def _str_from_timestamp(timestamp):
        if timestamp is None:
            return 'current'
        else:
            return timestamp.strftime('%Y%m%d')

    def _open(self, dataset_name, protocol='OPENDAP'):
        if protocol != 'OPENDAP':
            raise NotImplementedError("Only OPENDAP protocol supported at this time!")
        dataset = self._catalog.datasets[dataset_name]
        url = dataset.access_urls[protocol]
        return plotter(url, self.sattype)
