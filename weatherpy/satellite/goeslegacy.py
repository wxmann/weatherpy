import re
from datetime import datetime, timedelta

import netCDF4 as nc
import numpy as np
from siphon.catalog import TDSCatalog

from weatherpy import ctables, units
from weatherpy import maps
from weatherpy.internal import logger
from weatherpy.satellite._common import ThreddsSatelliteSelection
from weatherpy.thredds import dap_plotter, DatasetContextManager


def conus_west(sattype):
    if sattype.upper() == 'VIS':
        sector = 'WEST-CONUS_1km'
    elif sattype.upper() in ('IR' ,'WV'):
        sector = 'WEST-CONUS_4km'
    else:
        raise ValueError("Sattype: {} not supported".format(sattype))

    return GoesLegacySelection(sattype, sector)


def conus_east(sattype):
    if sattype.upper() == 'VIS':
        sector = 'EAST-CONUS_1km'
    elif sattype.upper() in ('IR' ,'WV'):
        sector = 'EAST-CONUS_4km'
    else:
        raise ValueError("Sattype: {} not supported".format(sattype))

    return GoesLegacySelection(sattype, sector)


class GoesLegacySelection(ThreddsSatelliteSelection):
    @staticmethod
    def _default_action(ds):
        return dap_plotter(ds, GoesLegacyPlotter)

    def __init__(self, sattype, sector):
        self.sector = sector
        self.sattype = sattype.upper()

    def latest(self, within=None, action=None):
        if within is None:
            within = timedelta(minutes=40)
        if action is None:
            action = GoesLegacySelection._default_action

        return self._latest_impl(within, action)

    def around(self, when, within=None, action=None):
        if within is None:
            within = timedelta(minutes=40)
        if action is None:
            action = GoesLegacySelection._default_action

        return self._around_impl(when, within, action)

    def between(self, t1, t2, action=None, sort='asc'):
        if action is None:
            action = GoesLegacySelection._default_action

        return self._between_impl(t1, t2, action, sort)

    def since(self, when, action=None, sort='asc'):
        if action is None:
            action = GoesLegacySelection._default_action

        return self._since_impl(when, action, sort)

    def _get_catalog(self, query_date):
        time_path = 'current' if query_date is None else query_date.strftime('%Y%m%d')
        catalog_url = 'http://thredds.ucar.edu/thredds/catalog/satellite/' \
                      '{}/{}/{}/catalog.xml'.format(self.sattype,
                                                    self.sector,
                                                    time_path)
        return TDSCatalog(catalog_url)

    def _timestamp_from_dataset(self, dataset_name):
        match = re.search(r'\d{8}_\d{4}', dataset_name)
        matched_str = match.group(0)
        if not matched_str:
            raise ValueError("Invalid dataset name: " + str(dataset_name))
        return datetime.strptime(matched_str, '%Y%m%d_%H%M')


class GoesLegacyPlotter(DatasetContextManager):

    def __init__(self, dataset):
        super().__init__(dataset)

        self._sattype = self.dataset.keywords_vocabulary

        self._timestamp = self._get_timestamp()
        self._geog = self.dataset.variables['LambertConformal']

        self._crs = maps.projections.lambertconformal(lat0=self._geog.latitude_of_projection_origin,
                                                      lon0=self._geog.longitude_of_central_meridian,
                                                      stdlat1=self._geog.standard_parallel,
                                                      r_earth=self._geog.earth_radius)
        logger.info("[GOES SAT] Finish reading satellite metadata")

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
        return maps.GSHHSMap(self._crs)

    def default_ctable(self):
        if self._sattype == 'VIS':
            return ctables.vis.default
        elif self._sattype == 'IR':
            return ctables.ir.alpha
        elif self._sattype == 'WV':
            return ctables.wv.accuwx
        else:
            return None

    def make_plot(self, mapper=None, colortable=None, extent=None):
        if colortable is None:
            colortable = self.default_ctable()

        if mapper is None:
            mapper = self.default_map()

        if extent is not None:
            mapper.extent = extent

        if not mapper.initialized():
            mapper.initialize_drawing()

        x = self.dataset.variables['x'][:]
        y = self.dataset.variables['y'][:]

        lim = tuple(units.METER.convert(val, units.KILOMETER)
                    for val in (x.min(), x.max(), y.min(), y.max()))
        pix = self._get_pixels()
        mapper.ax.imshow(pix, extent=lim, origin='upper',
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
