import math
import os

import cartopy
import numpy as np
import shapely.geometry as sgeom
from cartopy import crs as ccrs
from cartopy import feature as cfeat
from matplotlib import pyplot as plt

import config
from weatherpy.internal import logger, haversine_distance
from weatherpy.maps import properties


class Mapper(object):
    def __init__(self, crs, extent=None, backend=None, bg=None):
        self.crs = crs
        self.bg = bg
        self._extent = extent

        if backend is None:
            borders = properties.Stroke(width=1.0, color='gray', alpha=1.0)
            counties = properties.Stroke(width=0.5, color='gray', alpha=1.0)
            roads = properties.Stroke(width=0.65, color='brown', alpha=0.8)

            self.backend = GSHHSCartopy(borders, counties, roads)
        elif not isinstance(backend, MappingBackend):
            raise ValueError("Backend must be an instance of `MappingBackend`")
        else:
            self.backend = backend

    @property
    def extent(self):
        return self._extent

    @extent.setter
    def extent(self, extent):
        logger.info('[MAP] Setting extent to: {}'.format(extent))
        self._extent = extent

    def _backend_draw(self, layer, ax):
        try:
            method = getattr(self.backend, 'draw_' + str(layer))
            return method(ax)
        except AttributeError:
            raise ValueError("Invalid layer: {}".format(layer))

    def get_ax(self, subplot=None, fig=None):
        if subplot is not None:
            if fig is None:
                fig = plt.gcf()
            ax = fig.add_subplot(subplot, projection=self.crs)
        elif fig is not None:
            ax = fig.gca(projection=self.crs)
        else:
            ax = plt.axes(projection=self.crs)

        if self._extent is not None:
            ax.set_extent(self._extent)
        return ax

    def draw(self, ax=None, layers=None, detailed=False, subplot=None, fig=None):
        if ax is None:
            ax = self.get_ax(subplot, fig)

        if layers is None:
            layers = ['coastlines', 'borders', 'states', 'lakes']
            if detailed:
                layers += ['counties', 'roads']

        for layer in set(layers):
            self._backend_draw(layer, ax)

        if self.bg is not None:
            ax.background_patch.set_facecolor(self.bg)

        return ax


class MappingBackend(object):
    def draw_coastlines(self, ax):
        raise NotImplementedError

    def draw_borders(self, ax):
        raise NotImplementedError

    def draw_states(self, ax):
        raise NotImplementedError

    def draw_counties(self, ax):
        raise NotImplementedError

    def draw_lakes(self, ax):
        raise NotImplementedError

    def draw_roads(self, ax):
        raise NotImplementedError

    def draw_cities(self, ax):
        raise NotImplementedError

    def draw_gridlines(self, ax):
        raise NotImplementedError


class GSHHSCartopy(MappingBackend):
    def __init__(self, borderparams, countyparams, roadparams):
        self.scale = 'i'
        self.borderparams = borderparams
        self.countyparams = countyparams
        self.roadparams = roadparams

    def draw_coastlines(self, ax):
        logger.info("[MAP] Begin drawing coastlines")

        coastlines = cfeat.GSHHSFeature(self.scale, levels=[1])
        ax.add_feature(coastlines, edgecolor=self.borderparams.color,
                       linewidth=self.borderparams.width,
                       facecolor='none',
                       alpha=self.borderparams.alpha)

    def draw_lakes(self, ax, threshold=300):
        logger.info("[MAP] Begin drawing lakes")

        lakes = (rec.geometry for rec in self._ghssh_shp(self.scale, level=2).records()
                 if _size(rec) > threshold)
        ax.add_geometries(lakes, ccrs.PlateCarree(),
                          edgecolor=self.borderparams.color,
                          linewidth=self.borderparams.width,
                          facecolor='none',
                          alpha=self.borderparams.alpha)

    def draw_borders(self, ax):
        logger.info("[MAP] Begin drawing borders")

        borders = (read_line_geometries(rec) for rec in self._wdbii_shp(self.scale, level=1).records())
        ax.add_geometries(borders, ccrs.PlateCarree(),
                          edgecolor=self.borderparams.color,
                          facecolor='none',
                          linewidth=self.borderparams.width,
                          alpha=self.borderparams.alpha)

    def draw_states(self, ax):
        logger.info("[MAP] Begin drawing states")

        states = (read_line_geometries(rec) for rec in self._wdbii_shp(self.scale, level=2).records())
        ax.add_geometries(states, ccrs.PlateCarree(),
                          edgecolor=self.borderparams.color,
                          facecolor='none',
                          linewidth=self.borderparams.width,
                          alpha=self.borderparams.alpha)

    def draw_counties(self, ax):
        logger.info("[MAP] Begin drawing counties")
        counties = self._generic_shp('UScounties').geometries()
        ax.add_geometries(counties, ccrs.PlateCarree(),
                          edgecolor=self.countyparams.color,
                          linewidth=self.countyparams.width,
                          facecolor='none',
                          alpha=self.countyparams.alpha)

    def draw_roads(self, ax):
        logger.info("[MAP] Begin drawing highways")
        hwys = self._generic_shp('hways').geometries()
        ax.add_geometries(hwys, ccrs.PlateCarree(),
                          edgecolor=self.roadparams.color,
                          linewidth=self.roadparams.width,
                          facecolor='none',
                          alpha=self.roadparams.alpha)

    def draw_cities(self, ax):
        raise NotImplementedError("This backend does not support cities")

    def draw_gridlines(self, ax):
        ax.gridlines(linestyle='--', draw_labels=False)

    def _generic_shp(self, filename):
        shpfile_dir = filename
        filename = filename + '.shp'
        file = os.path.join(config.SHAPEFILE_DIR, shpfile_dir, filename)
        return cartopy.io.shapereader.Reader(file)

    def _ghssh_shp(self, scale, level):
        file = os.path.join(config.SHAPEFILE_DIR, 'gshhs', 'GSHHS_{}_L{}.shp'.format(scale, level))
        return cartopy.io.shapereader.Reader(file)

    def _wdbii_shp(self, scale, level, type='border'):
        file = os.path.join(config.SHAPEFILE_DIR, 'gshhs', 'WDBII_{}_{}_L{}.prj'.format(type, scale, level))
        return cartopy.io.shapereader.Reader(file)


def read_line_geometries(shprec, threshold=100):
    size = _size(shprec)
    geom = shprec.geometry

    if size < threshold:
        return geom

    if len(geom) != 1:
        # the GSHHS shapefile only has one geometry per record,
        # so we punt here when in the case it's not
        return geom

    only_geom_in_group = geom[0]
    geom_coords = only_geom_in_group.coords
    result_geometry = []
    for i, current_coord in enumerate(geom_coords):
        if i == len(geom_coords) - 1:
            result_geometry.append(current_coord)
        else:
            next_coord = geom_coords[i + 1]
            lon0, lat0 = current_coord
            lon1, lat1 = next_coord
            dist = haversine_distance(lon0, lat0, lon1, lat1)

            if dist < threshold:
                result_geometry.append(current_coord)
            else:
                n = int(math.ceil(dist / threshold)) + 1
                inset_xs = np.linspace(lon0, lon1, n)
                inset_ys = np.linspace(lat0, lat1, n)

                for inset_x, inset_y in zip(inset_xs, inset_ys):
                    result_geometry.append((inset_x, inset_y))

    line = sgeom.LineString(result_geometry)
    return sgeom.MultiLineString([line])


def _size(shprec):
    lon0, lat0, lon1, lat1 = shprec.bounds
    return haversine_distance(lon0, lat0, lon1, lat1)
