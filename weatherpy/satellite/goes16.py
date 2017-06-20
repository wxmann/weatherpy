from datetime import datetime

import cartopy.crs as ccrs
from siphon.catalog import TDSCatalog

from weatherpy import logger, ctables, maps
from weatherpy.maps import extents
from weatherpy.thredds import ThreddsDatasetPlotter, timestamp_from_dataset, dap_plotter, DatasetAccessException

try:
    import urlparse
except ImportError:
    import urllib.parse as urlparse

CATALOG_BASE_URL = 'http://thredds-jumbo.unidata.ucar.edu/thredds/catalog/satellite/goes16/GOES16/'


class Goes16Selection(object):
    def __init__(self, sector, channel):
        self.sector = sector
        self.channel = channel

        parent_catalog = TDSCatalog(urlparse.urljoin(CATALOG_BASE_URL, 'catalog.xml'))
        self._eligible_dates = sorted(parent_catalog.catalog_refs.keys())

        if not self._eligible_dates:
            raise DatasetAccessException("No Dates in TDS catalog: {}".format(parent_catalog.catalog_url))

        self._plotter = Goes16Plotter

    def latest(self):
        catalog = self._get_catalog(self._eligible_dates[-1])
        eligible_times = sorted(catalog.datasets.keys())
        return dap_plotter(catalog.datasets[eligible_times[-1]], self._plotter)

    def closest_to(self, when):
        datestr = when.strftime('%Y%m%d')
        if datestr not in self._eligible_dates:
            raise ValueError("Queried time out of range: {}. Range of dates is {} to {}"
                             .format(datestr, min(self._eligible_dates), max(self._eligible_dates)))

        catalog = self._get_catalog(datestr)
        eligible_times = sorted(catalog.datasets.keys())
        timestamps = [timestamp_from_dataset(k) for k in eligible_times]
        deltas = [abs(ts - when) for ts in timestamps]

        closest_time_index = deltas.index(min(deltas))
        return dap_plotter(catalog.datasets[eligible_times[closest_time_index]], self._plotter)

    def _get_catalog(self, datestr):
        path = '{date}/{sector}/{channel}/catalog.xml'.format(date=datestr,
                                                              sector=self.sector,
                                                              channel='Channel' + str(self.channel).zfill(2))
        return TDSCatalog(urlparse.urljoin(CATALOG_BASE_URL, path))


class Goes16Plotter(ThreddsDatasetPlotter):
    def __init__(self, dataset):
        super().__init__(dataset)
        # self._sattype = self.dataset.keywords_vocabulary
        # self._x = self.dataset.variables['x'][:]
        # self._y = self.dataset.variables['y'][:]

        # self._timestamp = self._get_timestamp()
        # self._pixels = self._get_pixels()
        # metadata
        self._channel = self.dataset.channel_id
        self._timestamp = datetime.strptime(self.dataset.start_date_time, '%Y%j%H%M%S')

        self._scmi = self.dataset.variables['Sectorized_CMI']

        # geographical projection data
        proj = self._scmi.grid_mapping
        geog = self.dataset.variables[proj]
        if proj == 'lambert_projection':
            globe = ccrs.Globe(ellipse='sphere', semimajor_axis=geog.semi_major,
                               semiminor_axis=geog.semi_minor)
            self._crs = ccrs.LambertConformal(central_latitude=geog.latitude_of_projection_origin,
                                              central_longitude=geog.longitude_of_central_meridian,
                                              standard_parallels=[geog.standard_parallel],
                                              false_easting=geog.false_easting,
                                              false_northing=geog.false_northing,
                                              globe=globe)
        else:
            raise NotImplementedError("Only Lambert Projection supported at this time")

        logger.info("[GOES SAT] Finish processing satellite metadata")

    @property
    def timestamp(self):
        return self._timestamp

    @property
    def sattype(self):
        if self._channel in (1, 2):
            return 'VIS'
        elif self._channel in (3, 4, 5, 6):
            return 'NEAR-IR'
        elif self._channel in (7, 11, 12, 13, 14, 15, 16):
            return 'IR'
        elif self._channel in (8, 9, 10):
            return 'WV'
        else:
            return 'Unrecognized'

    def default_map(self):
        return maps.LargeScaleMap(self._crs)

    def default_ctable(self):
        if self.sattype == 'VIS':
            return ctables.vis.default
        elif self.sattype in ('NEAR-IR', 'IR'):
            return ctables.ir.rainbow
        elif self.sattype == 'WV':
            return ctables.wv.accuwx
        else:
            return None

    def make_plot(self, mapper=None, colortable=None):
        # TODO: plot ir
        if colortable is None:
            cmap, norm = self.default_ctable()
        else:
            cmap, norm = colortable.cmap, colortable.norm

        if mapper is None:
            mapper = self.default_map()
            mapper.initialize_drawing()

        # x, y, data
        x = self.dataset.variables['x'][:]
        y = self.dataset.variables['y'][:]
        lim = (x.min(), x.max(), y.min(), y.max())
        plotdata = self._scmi[:] * norm.vmax

        logger.info("[GOES SAT] Finish processing satellite pixel data")

        mapper.ax.imshow(plotdata, extent=lim, origin='upper',
                         transform=self._crs,
                         cmap=cmap, norm=norm)
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


# sel = Goes16Selection('CONUS', 2)
# plotter = sel.closest_to(datetime(2017, 6, 18, 0, 0))
# mapper, _ = plotter.make_plot()
# mapper.extent = extents.southern_plains
# mapper.properties.strokecolor = 'yellow'
# mapper.draw_default()
# import matplotlib.pyplot as plt
# plt.show()