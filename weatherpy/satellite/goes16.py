import re
from datetime import datetime, timedelta, date

import cartopy.crs as ccrs
import numpy as np
import requests
from siphon.catalog import TDSCatalog

from weatherpy import logger, ctables, maps, units
from weatherpy.internal import pyhelpers, mask_outside_extent
from weatherpy.thredds import ThreddsDatasetPlotter, dap_plotter, DatasetAccessException
from weatherpy.units import Scale, UnitsException

CATALOG_BASE_URL = 'http://thredds-jumbo.unidata.ucar.edu/thredds/catalog/satellite/goes16/GOES16/'


def conus(channel):
    return Goes16Selection('CONUS', channel)


def sector1(channel):
    return Goes16Selection('Mesoscale-1', channel)


def sector2(channel):
    return Goes16Selection('Mesoscale-2', channel)


class Goes16Selection(object):
    @staticmethod
    def _default_action(ds):
        return dap_plotter(ds, Goes16Plotter)

    def __init__(self, sector, channel):
        self.sector = sector
        self.channel = channel

    def latest(self, within=None, action=None):
        if within is None:
            within = timedelta(minutes=15)
        if action is None:
            action = Goes16Selection._default_action

        right_now = pyhelpers.current_time_utc()
        datasets = self._datasets_between(right_now - within, right_now, 'desc')

        try:
            _, ds = next(datasets)
            return action(ds)
        except StopIteration:
            raise DatasetAccessException("No datasets found within {} of right now.".format(within))

    def around(self, when, within=None, action=None):
        if within is None:
            within = timedelta(minutes=15)
        if action is None:
            action = Goes16Selection._default_action

        dataset_by_deltas = {abs((ts - when).total_seconds()): ds for ts, ds in
                             self._datasets_between(when - within, when + within, 'desc')}
        if not dataset_by_deltas:
            raise DatasetAccessException("No datasets found around: {} +/- {}".format(when, within))
        smallest_delta = min(dataset_by_deltas.keys())
        return action(dataset_by_deltas[smallest_delta])

    def between(self, t1, t2, action=None, sort='asc'):
        if t1 >= t2:
            raise ValueError("t1 must be less than than t2")
        if action is None:
            action = Goes16Selection._default_action
        if sort not in ('asc', 'desc'):
            raise ValueError("Sort must be `asc` or `desc`")

        return (action(ds) for _, ds in self._datasets_between(t1, t2, sort))

    def since(self, when, action=None, sort='asc'):
        return self.between(when, pyhelpers.current_time_utc(), action, sort)

    def _datasets_between(self, t1, t2, sort):
        date1 = t1.date()
        date2 = t2.date()

        if sort == 'asc':
            date_on = date1
            while date_on <= date2:
                for ts, ds in self._datasets_on(date_on, sort):
                    if t1 <= ts < t2:
                        yield ts, ds
                date_on += timedelta(days=1)
        elif sort == 'desc':
            date_on = date2
            while date_on >= date1:
                for ts, ds in self._datasets_on(date_on, sort):
                    if t1 <= ts < t2:
                        yield ts, ds
                date_on -= timedelta(days=1)
        else:
            raise ValueError("Sort must be `asc` or `desc`")

    def _datasets_on(self, query_date, sort):
        try:
            catalog = self._get_catalog(query_date)
        except requests.exceptions.HTTPError:
            # Catalog does not exist, thus datasets are empty
            return ()
        reverse = sort == 'desc'
        dataset_keys = sorted(catalog.datasets.keys(), reverse=reverse)
        for ds_key in dataset_keys:
            yield timestamp_from_dataset(ds_key), catalog.datasets[ds_key]

    def _get_catalog(self, query_date):
        # temp workaround since Unidata just changed their catalog structure
        if query_date < date(2017, 6, 21):
            templ = '{date}/{sector}/{channel}/catalog.xml'
        else:
            templ = '{sector}/{channel}/{date}/catalog.xml'
        path = templ.format(date=query_date.strftime('%Y%m%d'), sector=self.sector,
                            channel='Channel' + str(self.channel).zfill(2))
        return TDSCatalog(CATALOG_BASE_URL + path)


def timestamp_from_dataset(dataset_name):
    match = re.search(r'\d{8}_\d{6}', dataset_name)
    matched_str = match.group(0)
    if not matched_str:
        raise ValueError("Invalid dataset name: " + str(dataset_name))
    return datetime.strptime(matched_str, '%Y%m%d_%H%M%S')


class Goes16Plotter(ThreddsDatasetPlotter):
    def __init__(self, dataset):
        super().__init__(dataset)

        self._channel = self.dataset.channel_id
        self._timestamp = datetime.strptime(self.dataset.start_date_time, '%Y%j%H%M%S')

        self._scmi = self.dataset.variables['Sectorized_CMI']

        # geographical projection data
        proj = self._scmi.grid_mapping
        geog = self.dataset.variables[proj]
        if proj == 'lambert_projection':
            globe = ccrs.Globe(semimajor_axis=geog.semi_major,
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
        return channel_sattype_map.get(self._channel, 'Unrecognized')

    def default_map(self):
        return maps.LargeScaleMap(self._crs)

    def default_ctable(self):
        if self.sattype == 'VIS':
            return ctables.vis.optimized
        elif self.sattype in ('NEAR-IR', 'IR'):
            return ctables.ir.cimms
        elif self.sattype == 'WV':
            return ctables.wv.accuwx
        else:
            return None

    def make_plot(self, mapper=None, colortable=None, scale=(), strict=True, extent=None):
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

        apply_extent = mapper.extent is not None and strict

        if apply_extent:
            xmask, ymask = mask_outside_extent(mapper.extent, self._crs, x, y)
            x = x[xmask]
            y = y[ymask]
            plotdata = self._scmi[ymask, xmask]
        else:
            plotdata = self._scmi[:]

        try:
            data_units = units.get(self._scmi.units)
            ctable_units = colortable.unit

            # workaround: for WV colortables, have to do some magic
            if isinstance(ctable_units, Scale) and not isinstance(data_units, Scale):
                if not scale:
                    if self.sattype != 'WV' or data_units != units.KELVIN:
                        raise ValueError("Must provide explicit scale for this dataset.")
                    lobound = units.CELSIUS.convert(-130, units.KELVIN)
                    hibound = units.CELSIUS.convert(10, units.KELVIN)
                    scale = Scale(lobound, hibound)
                elif isinstance(scale, tuple):
                    scale = Scale(*scale)

                plotdata = vectorize_unit_conversion(scale, ctable_units.reverse())(plotdata)
            else:
                plotdata = vectorize_unit_conversion(data_units, ctable_units)(plotdata)

        except UnitsException:
            raise ValueError("Unsupported plotting units: " + str(self._scmi.units))

        logger.info("[GOES SAT] Finish processing satellite pixel data")

        if apply_extent:
            mapper.ax.pcolormesh(x, y, plotdata,
                                 cmap=colortable.cmap, norm=colortable.norm)
        else:
            lim = (x.min(), x.max(), y.min(), y.max())
            mapper.ax.imshow(plotdata, extent=lim, origin='upper',
                             transform=self._crs,
                             cmap=colortable.cmap, norm=colortable.norm)
        return mapper, colortable


def vectorize_unit_conversion(unit1, unit2):
    def convert(x):
        return unit1.convert(x, unit2)

    return np.vectorize(convert)


channel_sattype_map = {}
for channel in range(1, 3):
    channel_sattype_map[channel] = 'VIS'
for channel in range(3, 7):
    channel_sattype_map[channel] = 'NEAR_IR'
channel_sattype_map[7] = 'IR'
for channel in range(8, 11):
    channel_sattype_map[channel] = 'WV'
for channel in range(11, 16):
    channel_sattype_map[channel] = 'IR'
