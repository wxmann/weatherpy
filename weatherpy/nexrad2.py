import functools
from contextlib import contextmanager
from datetime import datetime, timedelta

import cartopy.crs as ccrs
import netCDF4 as nc
import numpy as np
from siphon.radarserver import RadarServer, get_radarserver_datasets

from weatherpy import colortables
from weatherpy._pyhelpers import current_time_utc
from weatherpy.maps import drawers
from weatherpy.maps import projections
from weatherpy.thredds import DatasetAccessException


@contextmanager
def radaropen(url, **kwargs):
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
    def timestamp(self):
        return self._timestamp

    @property
    def units(self):
        return self._radarvar.units

    def _varname(self, prefix):
        if prefix == self._radartype:
            varname = prefix
        else:
            varname = prefix + Level2RadarPlotter.suffix_mapper[self._radartype]
        if self._hires:
            varname += '_HI'
        return varname

    def set_radar(self, radartype='Reflectivity', hires=True, sweep=0):
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

    def _calculate_radar_pix(self):
        self._radarvar = self.dataset.variables[self._varname(self._radartype)]
        self._radarraw = self._radarvar[self._sweep]
        self._radardata = Level2RadarPlotter._transform_radar_pix(self._radarvar, self._radarraw)

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
        mapper = drawers.DetailedUSMap(crs, bg_color='black')
        mapper.extent = self._extent
        return mapper

    def make_plot(self, mapper=None, colortable=None):
        if mapper is None:
            mapper = self.default_map()
        elif isinstance(mapper.crs, ccrs.PlateCarree):
            raise ValueError("Radar images are not supported on the Plate Carree projection at this time.")
        if colortable is None:
            colortable = colortables.refl_avl

        mapper.initialize_drawing()
        mapper.ax.pcolormesh(self._x, self._y, self._radardata,
                             cmap=colortable.cmap, norm=colortable.norm, zorder=0)
        return mapper

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


class Nexrad2Request(object):
    def __init__(self, station, protocol='OPENDAP'):
        self._station = station
        self._radarserver = _get_radar_server(host='http://thredds.ucar.edu/thredds/',
                                              dataset='NEXRAD Level II Radar from IDD')
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
        found_ds = self._get_datasets(query)[index]
        if isinstance(found_ds, list):
            return [ds.access_urls[self._protocol] for ds in found_ds]
        return found_ds.access_urls[self._protocol]

    def _get_from_timestamp(self, timestamp):
        query = self._radarserver.query()
        query.stations(self._station).time(timestamp)
        ds = self._get_datasets(query)[0]
        return ds.access_urls[self._protocol]

    def _get_from_slice(self, sliceobj):
        start = sliceobj.start
        stop = sliceobj.stop
        step = sliceobj.step

        use_index = any([
            isinstance(start, int) or isinstance(stop, int),
            start is None and stop is None
        ])
        use_timestamp = isinstance(start, datetime) or isinstance(stop, datetime)
        invalid = any([
            use_index and use_timestamp,
            not isinstance(start, (int, datetime)) and start is not None,
            not isinstance(stop, (int, datetime)) and stop is not None
        ])
        if use_index:
            return self._get_from_index(sliceobj)
        elif use_timestamp:
            if stop is None:
                stop = current_time_utc()
            if start is None:
                # provide all data for last 90 days,
                # if the radar server has data back to that point.
                start = current_time_utc() - timedelta(days=90)

            query = self._radarserver.query()
            query.stations(self._station)
            if step is None:
                query.time_range(start, stop)
                found_ds = self._get_datasets(query)
                return tuple(ds.access_urls[self._protocol] for ds in found_ds)
            else:
                timeslot = start
                return_urls = []
                while timeslot <= stop:
                    query.time(timeslot)
                    found_ds = self._get_datasets(query)[0]
                    return_urls.append(found_ds.access_urls[self._protocol])
                    timeslot += step
                return tuple(return_urls)
        elif invalid:
            raise ValueError("Invalid slice, check your values")
        else:
            raise ValueError("Invalid slice, check your values")


def _get_radar_server(host, dataset):
    full_datasets = get_radarserver_datasets(host)
    url = full_datasets[dataset].follow().catalog_url
    return RadarServer(url)


def _valid_station(st, radarserver):
    return radarserver.validate_query(radarserver.query().stations(st).all_times())


def _sorted_datasets(query, radarserver):
    catalog = radarserver.get_catalog(query)
    return sorted(catalog.datasets.values(), key=lambda ds: ds.name)
