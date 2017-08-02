import netCDF4 as nc
import numpy as np
import requests
from cartopy import crs as ccrs
from matplotlib import patches
from siphon.radarserver import get_radarserver_datasets, RadarServer

import config
from weatherpy import maps, ctables, plotextras
from weatherpy.internal import pyhelpers, logger, bbox_from_coord
from weatherpy.thredds import DatasetAccessException, dap_plotter, DatasetContextManager


def get_radar_server(host, dataset):
    full_datasets = get_radarserver_datasets(host)
    if dataset not in full_datasets:
        raise ValueError("Invalid dataset: {} for host: {}".format(dataset, host))
    url = full_datasets[dataset].follow().catalog_url
    return RadarServer(url)


class Nexrad2Selection(object):
    @staticmethod
    def _default_action(ds):
        return dap_plotter(ds, Nexrad2Plotter)

    def __init__(self, station, server=None):
        self._radarserver = server or get_radar_server(config.LEVEL_2_RADAR_CATALOG.host,
                                                       config.LEVEL_2_RADAR_CATALOG.dataset)

        self._q = self._init_query(station)

    def _init_query(self, st):
        st_q = self._radarserver.query().stations(st)
        if not self._radarserver.validate_query(st_q):
            raise DatasetAccessException("Invalid station: {}".format(st))
        return st_q

    def latest(self, action=None):
        if action is None:
            action = Nexrad2Selection._default_action
        query = self._q.all_times()
        all_ds = self._get_datasets(query, 'desc')
        try:
            latest_ds = next(all_ds)
        except StopIteration:
            raise DatasetAccessException("No radar datasets found")
        return action(latest_ds)

    def around(self, when, action=None):
        if action is None:
            action = Nexrad2Selection._default_action
        query = self._q.time(when)
        ds = self._get_datasets(query, 'asc')

        try:
            ds_around = next(ds)
        except StopIteration:
            raise DatasetAccessException("No dataset found around {}".format(when))
        return action(ds_around)

    def between(self, t1, t2, action=None, sort='asc'):
        if sort not in ('asc', 'desc'):
            raise ValueError("Sort must be `asc` or `desc`")
        if t1 >= t2:
            raise ValueError("t1 must be less than t2")
        if action is None:
            action = Nexrad2Selection._default_action
        query = self._q.time_range(t1, t2)

        return (action(ds) for ds in self._get_datasets(query, sort))

    def since(self, when, action=None, sort='asc'):
        return self.between(when, pyhelpers.current_time_utc(), action, sort)

    def _get_datasets(self, query, sort):
        try:
            catalog = self._radarserver.get_catalog(query)
        except requests.exceptions.HTTPError:
            # Catalog does not exist, thus datasets are empty
            return ()
        reverse = sort == 'desc'
        dataset_keys = sorted(catalog.datasets.keys(), reverse=reverse)
        return (catalog.datasets[ds_key] for ds_key in dataset_keys)


DEFAULT_RANGE_MI = 143.


class Nexrad2Plotter(DatasetContextManager):
    suffix_mapper = {radartype: radartype[0] for radartype in (
        'CorrelationCoefficient',
        'DifferentialPhase',
        'DifferentialReflectivity',
        'Reflectivity',
        'SpectrumWidth'
    )}
    suffix_mapper['RadialVelocity'] = 'V'

    ctable_mapper = {
        'CorrelationCoefficient': None, #TODO: implement
        'DifferentialPhase': None, #TODO: implement
        'DifferentialReflectivity': ctables.diff_reflectivity.default,
        'Reflectivity': ctables.reflectivity.nws_default,
        'RadialVelocity': ctables.velocity.default,
        'SpectrumWidth': None # TODO: implement
    }

    def __init__(self, dataset, radartype=None, hires=True, sweep=0):
        super(Nexrad2Plotter, self).__init__(dataset)

        # declare radar-specific attributes
        self._radartype = None
        self._hires = None
        self._sweep = None
        self._radarvar = None
        self._timestamp = None
        self._radarunits = None
        self.set_radar(radartype, hires, sweep)

        self._extent = (
            self.dataset.geospatial_lon_min,
            self.dataset.geospatial_lon_max,
            self.dataset.geospatial_lat_min,
            self.dataset.geospatial_lat_max
        )

        self._stn_coordinates = (
            self.dataset.StationLongitude,
            self.dataset.StationLatitude
        )

        self._mesh = None

    @property
    def radartype(self):
        return self._radartype

    @property
    def hires(self):
        return self._hires

    @property
    def sweep(self):
        return self._sweep

    @property
    def station(self):
        return self.dataset.Station

    @property
    def timestamp(self):
        return self._timestamp

    def set_radar(self, radartype=None, hires=True, sweep=0):
        self._radartype = radartype or 'Reflectivity'
        if self._radartype not in Nexrad2Plotter.suffix_mapper:
            raise ValueError("Invalid radar type {}".format(self._radartype))

        self._hires = hires
        # TODO: validation of hires

        self._sweep = sweep
        self._radarvar = self.dataset.variables[self._getncvar(self._radartype)]

        timevar = self.dataset.variables[self._getncvar('time')]
        raw_time = timevar[self._sweep]
        time_units = timevar.units.replace('msecs', 'milliseconds')
        self._timestamp = nc.num2date(min(raw_time), time_units)

        self._radarunits = self._radarvar.units

    def default_map(self):
        crs = maps.projections.lambertconformal(lon0=self._stn_coordinates[0], lat0=self._stn_coordinates[1])
        mapper = maps.DetailedUSMap(crs, bg_color='black')
        mapper.extent = self._extent
        return mapper

    def default_ctable(self):
        return Nexrad2Plotter.ctable_mapper.get(self.radartype, None)

    def make_plot(self, mapper=None, colortable=None):
        if mapper is not None and isinstance(mapper.crs, ccrs.PlateCarree):
            raise ValueError("Radar images are not supported on the Plate Carree projection at this time.")
        if mapper is None:
            mapper = self.default_map()
        if colortable is None:
            colortable = self.default_ctable()
        if not mapper.initialized():
            mapper.initialize_drawing()

        x, y = self._calculate_xy()
        radardata = self._data_for_sweep()

        if self._radarunits != colortable.unit:
            colortable = colortable.convert(self._radarunits)
        self._mesh = mapper.ax.pcolormesh(x, y, radardata,
                                          cmap=colortable.cmap, norm=colortable.norm, zorder=0)
        return mapper, colortable

    def range_ring(self, mapper, mi=DEFAULT_RANGE_MI, draw_ring=True,
                   color=None, limit=True, fit_to_ring=True):
        ring = plotextras.ring_path(mi, self._stn_coordinates)
        if draw_ring:
            patch = patches.PathPatch(ring, edgecolor=color, facecolor='none', transform=ccrs.PlateCarree())
            mapper.ax.add_patch(patch)
        if limit and self._mesh is not None:
            self._mesh.set_clip_path(ring, transform=ccrs.PlateCarree()._as_mpl_transform(mapper.ax))
        if fit_to_ring:
            mapper.extent = bbox_from_coord(ring.vertices)
        return mapper

    def _calculate_xy(self):
        az = self.dataset.variables[self._getncvar('azimuth')][self._sweep]
        rng = self.dataset.variables[self._getncvar('distance')][:]
        az_rad = np.deg2rad(az)[:, None]

        # sin <-> x and cos <-> y since azimuth is measure from 0 deg == North.
        x = rng * np.sin(az_rad)
        y = rng * np.cos(az_rad)
        return x, y

    def _data_for_sweep(self):
        logger.info('[PROCESS LEVEL 2] Finish parsing radar information for '
                    'radar station: {}, timestamp: {}'.format(self.station, self.timestamp))

        # If flag is there, the data needs to be converted to 8-bit unsigned integer
        if '_Unsigned' in self._radarvar.ncattrs() and self._radarvar._Unsigned == 'true':
            self._radarvar.set_auto_maskandscale(False)
            data = self._radarvar[self._sweep]
            data = data.view('uint8')
            masked_data = np.ma.array(data, mask=data == 0)
            return masked_data * self._radarvar.scale_factor + self._radarvar.add_offset
        else:
            data = self._radarvar[self._sweep]
            return np.ma.array(data, mask=data == 0)

    def _getncvar(self, prefix):
        if prefix in Nexrad2Plotter.suffix_mapper:
            varname = prefix
        else:
            varname = prefix + Nexrad2Plotter.suffix_mapper[self._radartype]
        if self._hires:
            varname += '_HI'
        return varname