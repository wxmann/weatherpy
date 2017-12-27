import re
from datetime import datetime, timedelta, date

import cartopy.crs as ccrs
import numpy as np
from siphon.catalog import TDSCatalog

from weatherpy import ctables, maps, units
from weatherpy.internal import mask_outside_extent, logger
from weatherpy.maps import extents
from weatherpy.netcdf import netcdf_open
from weatherpy.structures import position_3d
from weatherpy.thredds import ThreddsSatelliteSelection
from weatherpy.units import Scale, UnitsException, arrayconvert

CATALOG_BASE_URL = 'http://thredds-jumbo.unidata.ucar.edu/thredds/catalog/satellite/goes16/GOES16/'


def conus(channel):
    return Goes16Selection('CONUS', channel)


def meso1(channel):
    return Goes16Selection('Mesoscale-1', channel)


def meso2(channel):
    return Goes16Selection('Mesoscale-2', channel)


def fulldisk(channel):
    return Goes16Selection('FullDisk', channel)


def puertorico(channel):
    return Goes16Selection('PRREGI', channel)


class Goes16Selection(ThreddsSatelliteSelection):
    @staticmethod
    def _default_action(catalog_ds):
        dap_url = catalog_ds.access_urls['OPENDAP']
        return load_unidata(dap_url)

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


def load_unidata(data_loc):
    with netcdf_open(data_loc) as dataset:
        channel = dataset.channel_id
        timestamp = datetime.strptime(dataset.start_date_time, '%Y%j%H%M%S')
        satellite_position = position_3d(latitude=dataset.satellite_latitude,
                                         longitude=dataset.satellite_longitude,
                                         altitude=dataset.satellite_altitude)

        product_center = position_3d(latitude=dataset.product_center_latitude,
                                     longitude=dataset.product_center_longitude,
                                     altitude=None)
        meso_sector = 'MESO' in dataset.product_name

        scmi = dataset.variables['Sectorized_CMI']

        # geographical projection data
        proj = scmi.grid_mapping
        geog = dataset.variables[proj]
        if proj == 'lambert_projection':
            globe = ccrs.Globe(ellipse='sphere',
                               semimajor_axis=geog.semi_major,
                               semiminor_axis=geog.semi_minor)
            transform_crs = ccrs.LambertConformal(central_latitude=geog.latitude_of_projection_origin,
                                                  central_longitude=geog.longitude_of_central_meridian,
                                                  standard_parallels=[geog.standard_parallel],
                                                  false_easting=geog.false_easting,
                                                  false_northing=geog.false_northing,
                                                  globe=globe)
        elif proj == 'fixedgrid_projection':
            globe = ccrs.Globe(semimajor_axis=geog.semi_major,
                               semiminor_axis=geog.semi_minor)
            transform_crs = ccrs.NearsidePerspective(central_latitude=geog.latitude_of_projection_origin,
                                                     central_longitude=geog.longitude_of_projection_origin,
                                                     satellite_height=geog.perspective_point_height,
                                                     globe=globe)
        elif proj == 'mercator_projection':
            globe = ccrs.Globe(ellipse='sphere',
                               semimajor_axis=geog.semi_major,
                               semiminor_axis=geog.semi_minor)
            transform_crs = ccrs.Mercator(central_longitude=geog.longitude_of_projection_origin,
                                          latitude_true_scale=geog.standard_parallel,
                                          globe=globe)
        else:
            raise NotImplementedError("Projection: {} not supported at this time".format(proj))

        logger.info("[GOES SAT] Finish processing satellite metadata")

        return Goes16Scan(dataset_src=data_loc,
                          channel=channel,
                          timestamp=timestamp,
                          satellite_position=satellite_position,
                          product_center=product_center,
                          meso_sector=meso_sector,
                          data_coordinate_transform=transform_crs)


class Goes16Scan(object):
    def __init__(self, dataset_src, channel, timestamp,
                 satellite_position, product_center, meso_sector,
                 dataset_open=netcdf_open,
                 data_coordinate_transform=None):
        self.dataset_src = dataset_src
        self.dataset_open = dataset_open
        self.channel = channel
        self.timestamp = timestamp
        self.satellite_position = satellite_position
        self.product_center = product_center
        self.meso_sector = meso_sector
        self.transform = data_coordinate_transform

    @property
    def sattype(self):
        try:
            return channel_sattype_map[self.channel]
        except KeyError:
            raise ValueError("Invalid satellite type")

    def default_map(self):
        crs = ccrs.NearsidePerspective(self.satellite_position.longitude,
                                       self.satellite_position.latitude)

        default_map = maps.Mapper(crs)

        if self.meso_sector:
            default_map.extent = extents.zoom((self.product_center.latitude,
                                               self.product_center.longitude),
                                              km=600)

        default_map.backend.borderparams.color = 'black'
        default_map.backend.borderparams.alpha = 0.75
        default_map.backend.countyparams.strokecolor = 'black'
        default_map.backend.countyparams.alpha = 0.4
        default_map.backend.roadparams.strokecolor = 'red'
        default_map.backend.roadparams.alpha = 0.3

        return default_map

    def default_ctable(self):
        if self.sattype in ('NEAR_IR', 'VIS'):
            return ctables.vis.optimized
        elif self.sattype == 'IR':
            return ctables.ir.alpha
        elif self.sattype == 'WV':
            return ctables.wv.accuwx
        else:
            return None

    def make_plot(self, mapper=None, colortable=None, scale=(), strict=True, extent=None,
                  fix_clipped=True, map_kw=None, draw_map=True):
        if colortable is None:
            colortable = self.default_ctable()

        if mapper is None:
            mapper = self.default_map()

        if extent is not None:
            mapper.extent = extent

        if map_kw is None:
            map_kw = dict()

        with self.dataset_open(self.dataset_src) as dataset:
            xvar = dataset.variables['x']
            yvar = dataset.variables['y']
            x = xvar[:]
            y = yvar[:]
            scmi = dataset.variables['Sectorized_CMI']

            # for full disk, x and y coordinates are in microradians.
            # Use the satellite height to convert to meters.
            if xvar.units == 'microradian':
                x *= self.satellite_position.altitude / 1E6
            if yvar.units == 'microradian':
                y *= self.satellite_position.altitude / 1E6

            plot_limited = mapper.extent is not None and strict
            use_pcolormesh = plot_limited

            if plot_limited:
                xmask, ymask, data_extnt = mask_outside_extent(mapper.extent, mapper.crs, x, y, self.transform)
                xmasked = x[xmask]
                ymasked = y[ymask]

                if not xmasked.size or not ymasked.size:
                    # we are out of bounds of the satellite data, fake an empty plot area
                    # as we can't plot-limit with an empty coordinate array
                    plotdata = np.empty(scmi.shape)
                    use_pcolormesh = False
                else:
                    x = xmasked
                    y = ymasked
                    plotdata = scmi[ymask, xmask]
                    use_pcolormesh = not data_extnt.is_outside(mapper.extent)
            else:
                plotdata = scmi[:]

            # apply gamma correction?
            # plotdata = np.sqrt(plotdata)

            if self.sattype == 'VIS' and fix_clipped:
                # hack for fixing clipping highlights that default to fill value of 0
                plotdata[plotdata == scmi._FillValue] = 1.0

            try:
                data_units = units.get(scmi.units)
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
                raise ValueError("Unsupported plotting units: " + str(scmi.units))

            logger.info("[GOES SAT] Finish processing satellite pixel data")

            if draw_map:
                ax = mapper.draw(**map_kw)
            else:
                ax = mapper.get_ax()

            if use_pcolormesh:
                logger.debug('Using pcolormesh')
                ax.pcolormesh(x, y, plotdata,
                              transform=self.transform,
                              cmap=colortable.cmap, norm=colortable.norm)
            else:
                logger.debug('Using imshow')
                interp = 'bilinear' if self.sattype == 'VIS' else 'none'
                lim = (x.min(), x.max(), y.min(), y.max())
                ax.imshow(plotdata, extent=lim, origin='upper',
                          transform=self.transform,
                          interpolation=interp,
                          cmap=colortable.cmap, norm=colortable.norm)

            return mapper, colortable


channel_sattype_map = {}
for ch in range(1, 3):
    channel_sattype_map[ch] = 'VIS'
for ch in range(3, 7):
    channel_sattype_map[ch] = 'NEAR_IR'
channel_sattype_map[7] = 'IR'
for ch in range(8, 11):
    channel_sattype_map[ch] = 'WV'
for ch in range(11, 16):
    channel_sattype_map[ch] = 'IR'
