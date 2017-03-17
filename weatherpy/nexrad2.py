import functools
from contextlib import contextmanager
from datetime import datetime, timedelta

import cartopy.crs as ccrs
import netCDF4 as nc
import numpy as np
from matplotlib import patches
from siphon.radarserver import RadarServer, get_radarserver_datasets

import config
from weatherpy import colortables
from weatherpy import logger
from weatherpy import plotextras
from weatherpy._pyhelpers import current_time_utc, index_time_slice_helper
from weatherpy.calcs import bbox_from_coord
from weatherpy.maps import mappers
from weatherpy.maps import projections
from weatherpy.thredds import DatasetAccessException

DEFAULT_RANGE_MI = 143.


@contextmanager
def radar2open(url, **kwargs):
    dataset = nc.Dataset(url)
    try:
        yield Level2RadarPlotter(dataset, **kwargs)
    finally:
        dataset.close()


class Level2RadarPlotter(object):
    suffix_mapper = {radartype: radartype[0] for radartype in (
        'CorrelationCoefficient',
        'DifferentialPhase',
        'DifferentialReflectivity',
        'Reflectivity',
        'SpectrumWidth'
    )}
    suffix_mapper['RadialVelocity'] = 'V'

    def __init__(self, dataset, radartype=None, hires=True, sweep=0):
        self.dataset = dataset

        # metadata
        self._radartype = radartype
        self._hires = hires
        self._sweep = sweep
        self._timestamp = None
        self._station = dataset.Station

        self.set_radar(radartype or 'Reflectivity', hires, sweep)

        self._extent = (
            self.dataset.geospatial_lon_min,
            self.dataset.geospatial_lon_max,
            self.dataset.geospatial_lat_min,
            self.dataset.geospatial_lat_max
        )

        self._origin = (
            self.dataset.StationLongitude,
            self.dataset.StationLatitude
        )

        self._mapper_used = None
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

    @sweep.setter
    def sweep(self, sweepval):
        # TODO: validation on sweep in range
        self._sweep = sweepval
        self._fetch_data_for_sweep()

    @property
    def station(self):
        return self._station

    @property
    def timestamp(self):
        return self._timestamp

    @property
    def units(self):
        return self._radarvar.units

    @property
    def origin(self):
        return self._origin

    def _varname(self, prefix):
        if prefix == self._radartype:
            varname = prefix
        else:
            varname = prefix + Level2RadarPlotter.suffix_mapper[self._radartype]
        if self._hires:
            varname += '_HI'
        return varname

    def set_radar(self, radartype='Reflectivity', hires=True, sweep=0):
        logger.info(
            '[PROCESS LEVEL 2] Setting radar to type: {}, hi-res: {}, sweep: {}'.format(radartype, hires, sweep))
        if radartype not in Level2RadarPlotter.suffix_mapper:
            raise ValueError("Invalid radar type {}".format(radartype))
        self._radartype = radartype
        self._hires = hires
        self._sweep = sweep
        self._fetch_data_for_sweep()

    def _fetch_data_for_sweep(self):
        self._calculate_radar_pix()
        self._calculate_xy()
        self._calculate_timestamp()
        logger.info('[PROCESS LEVEL 2] Finish parsing radar information for radar station: {}, timestamp: {}'.format(
            self.station, self.timestamp))

    def _calculate_radar_pix(self):
        self._radarvar = self.dataset.variables[self._varname(self._radartype)]
        self._radarraw = self._radarvar[self._sweep]
        self._radardata = Level2RadarPlotter._transform_radar_pix(self._radarvar, self._radarraw)
        if self._radartype == 'RadialVelocity':
            self._radardata *= 1.94384

    def _calculate_xy(self):
        self._az = self.dataset.variables[self._varname('azimuth')][self._sweep]
        self._rng = self.dataset.variables[self._varname('distance')][:]
        az_rad = np.deg2rad(self._az)[:, None]

        # sin <-> x and cos <-> y since azimuth is measure from 0 deg == North.
        self._x = self._rng * np.sin(az_rad)
        self._y = self._rng * np.cos(az_rad)

    def _calculate_timestamp(self):
        timevar = self.dataset.variables[self._varname('time')]
        raw_time = timevar[self._sweep]
        time_units = timevar.units.replace('msecs', 'milliseconds')
        self._timestamp = nc.num2date(min(raw_time), time_units)

    @staticmethod
    def _transform_radar_pix(radar_var, raw_radar):
        offset = radar_var.add_offset
        scaling_factor = radar_var.scale_factor
        convert = np.vectorize(functools.partial(_convert_pix, offset=offset, scale=scaling_factor),
                               otypes=[np.float32])
        processed_data = convert(raw_radar)
        return processed_data

    def default_map(self):
        crs = projections.lambertconformal(lon0=self._origin[0], lat0=self._origin[1])
        mapper = mappers.DetailedUSMap(crs, bg_color='black')
        mapper.extent = self._extent
        return mapper

    def make_plot(self, mapper=None, colortable=None):
        if mapper is not None and isinstance(mapper.crs, ccrs.PlateCarree):
            raise ValueError("Radar images are not supported on the Plate Carree projection at this time.")
        mapper = self._saved_mapper(mapper)
        if colortable is None:
            colortable = colortables.refl_avl

        mapper.initialize_drawing()
        self._mesh = mapper.ax.pcolormesh(self._x, self._y, self._radardata,
                                          cmap=colortable.cmap, norm=colortable.norm, zorder=0)
        return mapper

    def range_ring(self, mi=None, draw_ring=True, color=None, limit=True, fit_to_ring=True):
        if self._mesh is None or self._mapper_used is None:
            raise ValueError("Must make radar plot first before drawing the range ring")
        if mi is None:
            mi = DEFAULT_RANGE_MI
        mapper = self._saved_mapper()
        ring = plotextras.ring_path(mi, self._origin)
        if draw_ring:
            patch = patches.PathPatch(ring, edgecolor=color, facecolor='none', transform=ccrs.PlateCarree())
            mapper.ax.add_patch(patch)
        if limit:
            self._mesh.set_clip_path(ring, transform=ccrs.PlateCarree()._as_mpl_transform(mapper.ax))
        if fit_to_ring:
            mapper.extent = bbox_from_coord(ring.vertices)
        return mapper

    def _saved_mapper(self, mapper=None):
        if self._mapper_used is None:
            self._mapper_used = mapper if mapper is not None else self.default_map()
        return self._mapper_used

    # only for debugging purposes. Not for public API consumption.
    def draw_hist(self, convert=False):
        import matplotlib.pyplot as plt
        if not convert:
            data = self._radarraw
        else:
            data = self._radardata
        data = data.flatten()
        plt.hist(data, 128)
        plt.yscale('log', nonposy='clip')


def _convert_pix(pix, offset, scale):
    # inspired by http://nbviewer.jupyter.org/gist/dopplershift/356f2e14832e9b676207
    # convert to unsigned by adding 256 but scaled by scale argument.
    if pix <= offset:
        return pix + 256. * scale
    return pix


def get_radar_server(host, dataset):
    full_datasets = get_radarserver_datasets(host)
    if dataset not in full_datasets:
        raise ValueError("Invalid dataset: {} for host: {}".format(dataset, host))
    url = full_datasets[dataset].follow().catalog_url
    return RadarServer(url)


class Nexrad2Request(object):
    def __init__(self, station, server=None, protocol='OPENDAP'):
        self._station = station
        self._radarserver = server or get_radar_server(config.LEVEL_2_RADAR_CATALOG.host,
                                                       config.LEVEL_2_RADAR_CATALOG.dataset)
        self._check_station(station)
        self._protocol = protocol
        self._get_datasets = functools.partial(_sorted_datasets, radarserver=self._radarserver)

    def _check_station(self, st):
        if not _valid_station(st, self._radarserver):
            raise DatasetAccessException("Invalid station: {}".format(st))

    def __getitem__(self, item):
        if isinstance(item, int):
            return self._get_from_index(item)
        elif isinstance(item, datetime):
            return self._get_from_timestamp(item)
        elif isinstance(item, slice):
            return self._get_from_slice(item)
        else:
            raise ValueError("Indexed dataset must be an integer or timestamp.")

    def _get_from_index(self, index):
        query = self._radarserver.query()
        query.stations(self._station).all_times()
        try:
            found_ds = self._get_datasets(query)[index]
            if isinstance(found_ds, list):
                return (self._open(ds) for ds in found_ds)
            return self._open(found_ds)
        except IndexError:
            raise DatasetAccessException("No dataset found for index: {}".format(index))

    def _get_from_timestamp(self, timestamp):
        query = self._radarserver.query()
        query.stations(self._station).time(timestamp)
        try:
            ds = self._get_datasets(query)[0]
            return self._open(ds)
        except IndexError:
            raise DatasetAccessException("No dataset found for timestasmp: {}".format(timestamp))

    def _get_from_slice(self, sliceobj):
        def ts_slice(sliceobj):
            start = sliceobj.start
            stop = sliceobj.stop
            step = sliceobj.step
            if stop is None:
                stop = current_time_utc()
            if start is None:
                raise ValueError("Must provide a start time for slice")

            query = self._radarserver.query()
            query.stations(self._station)
            if step is None:
                query.time_range(start, stop)
                found_ds = self._get_datasets(query)
                return (ds.access_urls[self._protocol] for ds in found_ds)
            elif isinstance(step, (timedelta, int)):
                return self._iter_for_stepped_timestamp_slice(query, start, step, stop)
            else:
                raise ValueError("Invalid type of step. Require int or timedelta")

        return index_time_slice_helper(self._get_from_index, ts_slice)(sliceobj)

    def _iter_for_stepped_timestamp_slice(self, query, start, step, stop):
        if isinstance(step, timedelta):
            timeslot = start
            # this (<=) is inconsistent with the GOES implementation (<) but consistent with the non-step
            # implementation handled via thredds.
            # meh?
            while timeslot <= stop:
                query.time(timeslot)
                try:
                    found_ds = self._get_datasets(query)[0]
                except IndexError:
                    # if no dataset for the time, exit out of the loop; we're done
                    return
                yield self._open(found_ds)
                timeslot += step
        elif isinstance(step, int):
            query.time_range(start, stop)
            for i, found_ds in enumerate(self._get_datasets(query)):
                if i % step == 0:
                    yield self._open(found_ds)

    def _open(self, ds):
        if self._protocol != 'OPENDAP':
            raise ValueError("Only support OPENDAP at this time")
        return ds.access_urls[self._protocol]


def _valid_station(st, radarserver):
    return radarserver.validate_query(radarserver.query().stations(st).all_times())


def _sorted_datasets(query, radarserver):
    catalog = radarserver.get_catalog(query)
    return sorted(catalog.datasets.values(), key=lambda ds: ds.name)
