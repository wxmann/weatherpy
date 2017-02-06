from contextlib import contextmanager

from siphon.catalog import TDSCatalog

from weatherpy import colortables
from weatherpy import mapproj
from weatherpy.thredds import TimeBasedTDSRequest

import numpy as np
import netCDF4 as nc
import cartopy.crs as ccrs


@contextmanager
def radarplot(url):
    dataset = nc.Dataset(url)
    try:
        yield Level2RadarPlotter(dataset)
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

        # plotting variables
        (self._az_all_sweeps,
         self._rng,
         self._data_all_sweeps,
         self._radardata,
         self._x,
         self._y) = (None, None, None, None, None, None)

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
        self._calculate_for_sweep()

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
            raise ValueError("Invalid radar type {}".format(self._radartype))
        self._radartype = radartype
        self._hires = bool(hires)
        self._sweep = sweep
        self._fetch_data()

    def _fetch_data(self):
        self._az_all_sweeps = self.dataset.variables[self._varname('azimuth')][:]
        self._rng = self.dataset.variables[self._varname('distance')][:]

        radar_var = self.dataset.variables[self._varname(self._radartype)]
        self._data_all_sweeps = Level2RadarPlotter._transform_radar_pix(radar_var[:], radar_var)

        # self._data_all_sweeps = np.ma.array(self._data_all_sweeps, mask=np.isnan(self._data_all_sweeps))
        self._calculate_for_sweep()

    @staticmethod
    def _transform_radar_pix(radar_data, radar_var):
        # This code still needs some work...
        # Should follow form from, but haven't gotten it to work:
        # http://nbviewer.jupyter.org/gist/dopplershift/356f2e14832e9b676207
        return radar_data

    def _calculate_for_sweep(self):
        az = self._az_all_sweeps[self._sweep]
        az_rad = np.deg2rad(az)[:, None]
        self._radardata = self._data_all_sweeps[self._sweep]

        # sin <-> x and cos <-> y since azimuth is measure from 0 deg == North.
        self._x = self._rng * np.sin(az_rad)
        self._y = self._rng * np.cos(az_rad)

    def make_plot(self, mapper=None, colortable=None):
        if mapper is None:
            mapper = mapproj.lambertconformal(lon0=self._origin[0], lat0=self._origin[1])
            mapper.extent = self._extent
        elif isinstance(mapper.crs, ccrs.PlateCarree):
            raise ValueError("Radar images are not supported on the Plate Carree projection at this time.")
        if colortable is None:
            colortable = colortables.refl_avl

        mapper.initialize_drawing()
        mapper.ax.pcolormesh(self._x, self._y, self._radardata,
                             cmap=colortable.cmap, norm=colortable.norm, zorder=0)
        return mapper


class Nexrad2Request(TimeBasedTDSRequest):
    def __init__(self, station, request_date=None):
        self._station = station
        super(Nexrad2Request, self).__init__(request_date)

    def _initialize_thredds_catalog(self):
        request_date_str = self.request_date.strftime('%Y%m%d')
        url = 'http://thredds.ucar.edu/thredds/catalog/nexrad/level2/' \
              '{}/{}/catalog.xml'.format(self._station, request_date_str)
        # TODO: handle race condition around 0Z
        self._catalog = TDSCatalog(url)
        self._catalog_datasets = sorted(self._catalog.datasets.keys())

    def _open(self, dataset_name, protocol='OPENDAP'):
        if protocol != 'OPENDAP':
            raise NotImplementedError("Only OPENDAP protocol supported at this time!")
        dataset = self._catalog.datasets[dataset_name]
        url = dataset.access_urls[protocol]
        return radarplot(url)
