import re
from datetime import datetime, timedelta, date

import cartopy.crs as ccrs
from siphon.catalog import TDSCatalog

from weatherpy import ctables, maps, units
from weatherpy.internal import mask_outside_extent, logger
from weatherpy.satellite.shared import ThreddsSatelliteSelection, satpos
from weatherpy.thredds import DatasetContextManager, dap_plotter
from weatherpy.units import Scale, UnitsException, arrayconvert

CATALOG_BASE_URL = 'http://thredds-jumbo.unidata.ucar.edu/thredds/catalog/satellite/goes16/GOES16/'


def conus(channel):
    return Goes16Selection('CONUS', channel)


def sector1(channel):
    return Goes16Selection('Mesoscale-1', channel)


def sector2(channel):
    return Goes16Selection('Mesoscale-2', channel)


def fulldisk(channel):
    return Goes16Selection('FullDisk', channel)


def puertorico(channel):
    return Goes16Selection('PRREGI', channel)


class Goes16Selection(ThreddsSatelliteSelection):

    @staticmethod
    def _default_action(ds):
        return dap_plotter(ds, Goes16Plotter)

    def __init__(self, sector, channel):
        self.sector = sector
        self.channel = channel

    def latest(self, within=None, action=None):
        if within is None:
            within = timedelta(minutes=40)
        if action is None:
            action = Goes16Selection._default_action

        return self._latest_impl(within, action)

    def around(self, when, within=None, action=None):
        if within is None:
            within = timedelta(minutes=40)
        if action is None:
            action = Goes16Selection._default_action

        return self._around_impl(when, within, action)

    def between(self, t1, t2, action=None, sort='asc'):
        if action is None:
            action = Goes16Selection._default_action

        return self._between_impl(t1, t2, action, sort)

    def since(self, when, action=None, sort='asc'):
        if action is None:
            action = Goes16Selection._default_action

        return self._since_impl(when, action, sort)

    def _get_catalog(self, query_date):
        # temp workaround since Unidata just changed their catalog structure
        if query_date < date(2017, 6, 21):
            templ = '{date}/{sector}/{channel}/catalog.xml'
        else:
            templ = '{sector}/{channel}/{date}/catalog.xml'
        path = templ.format(date=query_date.strftime('%Y%m%d'), sector=self.sector,
                            channel='Channel' + str(self.channel).zfill(2))
        return TDSCatalog(CATALOG_BASE_URL + path)

    def _timestamp_from_dataset(self, dataset_name):
        match = re.search(r'\d{8}_\d{6}', dataset_name)
        matched_str = match.group(0)
        if not matched_str:
            raise ValueError("Invalid dataset name: " + str(dataset_name))
        return datetime.strptime(matched_str, '%Y%m%d_%H%M%S')


class Goes16Plotter(DatasetContextManager):
    def __init__(self, dataset):
        super().__init__(dataset)

        self._channel = self.dataset.channel_id
        self._timestamp = datetime.strptime(self.dataset.start_date_time, '%Y%j%H%M%S')
        self._position = satpos(latitude=self.dataset.satellite_latitude,
                                longitude=self.dataset.satellite_longitude,
                                altitude=self.dataset.satellite_altitude)

        self._scmi = self.dataset.variables['Sectorized_CMI']

        # geographical projection data
        proj = self._scmi.grid_mapping
        geog = self.dataset.variables[proj]
        if proj == 'lambert_projection':
            globe = ccrs.Globe(ellipse='sphere',
                               semimajor_axis=geog.semi_major,
                               semiminor_axis=geog.semi_minor)
            self._crs = ccrs.LambertConformal(central_latitude=geog.latitude_of_projection_origin,
                                              central_longitude=geog.longitude_of_central_meridian,
                                              standard_parallels=[geog.standard_parallel],
                                              false_easting=geog.false_easting,
                                              false_northing=geog.false_northing,
                                              globe=globe)
        elif proj == 'fixedgrid_projection':
            globe = ccrs.Globe(semimajor_axis=geog.semi_major,
                               semiminor_axis=geog.semi_minor)
            self._crs = ccrs.NearsidePerspective(central_latitude=geog.latitude_of_projection_origin,
                                                 central_longitude=geog.longitude_of_projection_origin,
                                                 satellite_height=geog.perspective_point_height,
                                                 globe=globe)
        elif proj == 'mercator_projection':
            globe = ccrs.Globe(ellipse='sphere',
                               semimajor_axis=geog.semi_major,
                               semiminor_axis=geog.semi_minor)
            self._crs = ccrs.Mercator(central_longitude=geog.longitude_of_projection_origin,
                                      latitude_true_scale=geog.standard_parallel,
                                      globe=globe)
        else:
            raise NotImplementedError("Projection: {} not supported at this time".format(proj))

        logger.info("[GOES SAT] Finish processing satellite metadata")

    @property
    def timestamp(self):
        return self._timestamp

    @property
    def sattype(self):
        try:
            return channel_sattype_map[self._channel]
        except KeyError:
            raise ValueError("Invalid satellite type")
        
    @property
    def position(self):
        return self._position

    def default_map(self, **kwargs):
        if 'crs' in kwargs:
            kwargs.pop('crs')
        return maps.LargeScaleMap(self._crs, **kwargs)

    def default_ctable(self):
        if self.sattype in ('NEAR_IR', 'VIS'):
            return ctables.vis.optimized
        elif self.sattype == 'IR':
            return ctables.ir.alpha
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

        xvar = self.dataset.variables['x']
        yvar = self.dataset.variables['y']
        x = xvar[:]
        y = yvar[:]

        # for full disk, x and y coordinates are in microradians.
        # Use the satellite height to convert to meters.
        if xvar.units == 'microradian':
            x *= self._position.altitude / 1E6
        if yvar.units == 'microradian':
            y *= self._position.altitude / 1E6

        plot_limited = mapper.extent is not None and strict
        use_pcolormesh = plot_limited

        if plot_limited:
            xmask, ymask, data_extnt = mask_outside_extent(mapper.extent, mapper.crs, x, y, self._crs)
            xmasked = x[xmask]
            ymasked = y[ymask]

            if not xmasked.size or not ymasked.size:
                # we are out of bounds of the satellite data, fake an empty plot area
                # as we can't plot-limit with an empty coordinate array
                import numpy as np
                plotdata = np.empty(self._scmi.shape)
                use_pcolormesh = False
            else:
                x = xmasked
                y = ymasked
                plotdata = self._scmi[ymask, xmask]
                use_pcolormesh = not data_extnt.is_outside(mapper.extent)
        else:
            plotdata = self._scmi[:]

        try:
            data_units = units.get(self._scmi.units)
            ctable_units = colortable.unit

            # workaround: for legacy WV colortables expressed in brightness units, have to do some magic
            if isinstance(ctable_units, Scale) and not isinstance(data_units, Scale):
                if not scale:
                    if self.sattype != 'WV' or data_units != units.KELVIN:
                        raise ValueError("Must provide explicit scale for this dataset.")
                    lobound = units.KELVIN.convert(-130, units.CELSIUS)
                    hibound = units.KELVIN.convert(10, units.CELSIUS)
                    scale = Scale(lobound, hibound)
                elif isinstance(scale, tuple):
                    scale = Scale(*scale)

                plotdata = arrayconvert(scale, ctable_units.reverse())(plotdata)
            else:
                plotdata = arrayconvert(data_units, ctable_units)(plotdata)

        except UnitsException:
            raise ValueError("Unsupported plotting units: " + str(self._scmi.units))

        logger.info("[GOES SAT] Finish processing satellite pixel data")

        if use_pcolormesh:
            mapper.ax.pcolormesh(x, y, plotdata,
                                 transform=self._crs,
                                 cmap=colortable.cmap, norm=colortable.norm)
        else:
            lim = (x.min(), x.max(), y.min(), y.max())
            mapper.ax.imshow(plotdata, extent=lim, origin='upper',
                             transform=self._crs,
                             cmap=colortable.cmap, norm=colortable.norm)
        return mapper, colortable


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
