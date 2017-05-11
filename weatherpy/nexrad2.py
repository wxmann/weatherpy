import functools
from contextlib import contextmanager
from datetime import datetime, timedelta

import cartopy.crs as ccrs
import netCDF4 as nc
import numpy as np
from matplotlib import patches
from siphon.radarserver import RadarServer, get_radarserver_datasets

import config
from weatherpy import ctables
from weatherpy import maps
from weatherpy import plotextras
from weatherpy.internal import bbox_from_coord, current_time_utc, index_time_slice_helper, logger
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
        self._dataset = dataset

        self._radartype = radartype or 'Reflectivity'
        self._hires = hires
        self._sweep = sweep
        self._radarvar = self.get_radar_variable(self._radartype)

        self._extent = (
            self._dataset.geospatial_lon_min,
            self._dataset.geospatial_lon_max,
            self._dataset.geospatial_lat_min,
            self._dataset.geospatial_lat_max
        )

        self._stn_coordinates = (
            self._dataset.StationLongitude,
            self._dataset.StationLatitude
        )

        self._x, self._y = self._calculate_xy()
        self._mesh = None

    @property
    def radartype(self):
        return self._radartype

    @radartype.setter
    def radartype(self, new_radar_type):
        if new_radar_type not in Level2RadarPlotter.suffix_mapper:
            raise ValueError("Invalid radar type {}".format(new_radar_type))
        self._radartype = new_radar_type
        self._radarvar = self.get_radar_variable(self._radartype)

    @property
    def hires(self):
        return self._hires

    @hires.setter
    def hires(self, set_hires):
        self._hires = set_hires

    @property
    def sweep(self):
        return self._sweep

    @sweep.setter
    def sweep(self, sweepval):
        # TODO: validation on sweep in range
        self._sweep = sweepval

    @property
    def station(self):
        return self._dataset.Station

    def timestamp(self):
        timevar = self._dataset.variables[self._getncvar('time')]
        raw_time = timevar[self._sweep]
        time_units = timevar.units.replace('msecs', 'milliseconds')
        return nc.num2date(min(raw_time), time_units)

    def units(self, radartype=None):
        if radartype is None:
            radarvar = self._radarvar
        else:
            radarvar = self.get_radar_variable(radartype, validate=False)
        return radarvar.units

    def get_radar_variable(self, radartype, validate=True):
        var = self._dataset.variables[self._getncvar(radartype)]
        var.set_auto_maskandscale(False)
        if validate:
            Level2RadarPlotter._validate(var)
        return var

    def data_for_sweep(self, sweep):
        logger.info('[PROCESS LEVEL 2] Finish parsing radar information for radar station: {}, timestamp: {}'.format(
            self.station, self.timestamp()))
        raw_data = self._radarvar[sweep]
        transformed_data = Level2RadarPlotter._transform_radar_pix(self._radarvar, raw_data)
        return self._convert_units(transformed_data)

    def default_map(self):
        crs = maps.projections.lambertconformal(lon0=self._stn_coordinates[0], lat0=self._stn_coordinates[1])
        mapper = maps.DetailedUSMap(crs, bg_color='black')
        mapper.extent = self._extent
        return mapper

    def default_ctable(self):
        if self.radartype == 'Reflectivity':
            return ctables.reflectivity.nws_default
        elif self.radartype == 'RadialVelocity':
            return ctables.velocity.default
        else:
            return None

    def make_plot(self, mapper=None, colortable=None):
        if mapper is not None and isinstance(mapper.crs, ccrs.PlateCarree):
            raise ValueError("Radar images are not supported on the Plate Carree projection at this time.")
        if mapper is None:
            mapper = self.default_map()
            mapper.initialize_drawing()
        if colortable is None:
            colortable = self.default_ctable()

        radardata = self.data_for_sweep(self._sweep)
        self._mesh = mapper.ax.pcolormesh(self._x, self._y, radardata,
                                          cmap=colortable.cmap, norm=colortable.norm, zorder=0)
        return mapper, colortable

    def range_ring(self, mapper, mi=None, draw_ring=True, color=None, limit=True, fit_to_ring=True):
        if mi is None:
            mi = DEFAULT_RANGE_MI
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
        az = self._dataset.variables[self._getncvar('azimuth')][self._sweep]
        rng = self._dataset.variables[self._getncvar('distance')][:]
        az_rad = np.deg2rad(az)[:, None]

        # sin <-> x and cos <-> y since azimuth is measure from 0 deg == North.
        x = rng * np.sin(az_rad)
        y = rng * np.cos(az_rad)
        return x, y

    def _getncvar(self, prefix):
        if prefix in Level2RadarPlotter.suffix_mapper:
            varname = prefix
        else:
            varname = prefix + Level2RadarPlotter.suffix_mapper[self._radartype]
        if self._hires:
            varname += '_HI'
        return varname

    @staticmethod
    def _validate(var):
        return

    @staticmethod
    def _transform_radar_pix(radar_var, raw_radar_data):
        # inspired by http://nbviewer.jupyter.org/gist/dopplershift/356f2e14832e9b676207
        if '_Unsigned' in radar_var.ncattrs() and radar_var._Unsigned == 'true':
            raw_radar_data = raw_radar_data.view('uint8')
        masked_data = np.ma.array(raw_radar_data, mask=raw_radar_data == 0)
        return masked_data * radar_var.scale_factor + radar_var.add_offset

    def _convert_units(self, data):
        if self._radartype == 'RadialVelocity' and self.units('RadialVelocity') == 'm/s':
            return data * 1.94384
        return data


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
        # if self._protocol != 'OPENDAP':
        #     raise ValueError("Only support OPENDAP at this time")
        return ds.access_urls[self._protocol]


def _valid_station(st, radarserver):
    return radarserver.validate_query(radarserver.query().stations(st).all_times())


def _sorted_datasets(query, radarserver):
    catalog = radarserver.get_catalog(query)
    return sorted(catalog.datasets.values(), key=lambda ds: ds.name)
