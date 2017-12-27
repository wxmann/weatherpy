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


class MapArtist(object):
    def __init__(self, crs, extent=None, backend=None):
        self._crs = crs
        self._extent = extent

        if backend is None:
            scale = properties.Properties(scale='i')
            borders = properties.Properties(strokewidth=1.0, strokecolor='gray', fill='none', alpha=1.0)
            counties = properties.Properties(strokewidth=0.5, strokecolor='gray', fill='none', alpha=1.0)
            roads = properties.Properties(strokewidth=0.65, strokecolor='brown', fill='none', alpha=0.8)

            self.backend = GSHHSCartopy(scale, borders, counties, roads)
        elif not isinstance(backend, MappingBackend):
            raise ValueError("Backend must be an instance of `MappingBackend`")
        else:
            self.backend = backend

    @property
    def crs(self):
        return self._crs

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

    def draw(self, layers=None, subplot=None, fig=None, detailed=False, bg=None):
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

        if layers is None:
            layers = ['coastlines', 'borders', 'states', 'lakes']
            if detailed:
                layers += ['counties', 'roads']

        for layer in layers:
            self._backend_draw(layer, ax)

        if bg is not None:
            ax.background_patch.set_facecolor(bg)

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
    def __init__(self, scale_properties, border_properties, county_properties, highway_properties):
        self.scale_properties = scale_properties
        self.border_properties = border_properties
        self.county_properties = county_properties
        self.highway_properties = highway_properties

    def draw_coastlines(self, ax):
        logger.info("[MAP] Begin drawing coastlines")
        scale = self.scale_properties.scale

        coastlines = cfeat.GSHHSFeature(scale, levels=[1])
        ax.add_feature(coastlines, edgecolor=self.border_properties.strokecolor,
                       linewidth=self.border_properties.strokewidth,
                       facecolor='none',
                       alpha=self.border_properties.alpha)

    def draw_lakes(self, ax, threshold=300):
        logger.info("[MAP] Begin drawing lakes")
        scale = self.scale_properties.scale

        lakes = (rec.geometry for rec in self._ghssh_shp(scale, level=2).records()
                 if _size(rec) > threshold)
        ax.add_geometries(lakes, ccrs.PlateCarree(),
                          edgecolor=self.border_properties.strokecolor,
                          linewidth=self.border_properties.strokewidth,
                          facecolor='none',
                          alpha=self.border_properties.alpha)

    def draw_borders(self, ax):
        logger.info("[MAP] Begin drawing borders")
        scale = self.scale_properties.scale

        borders = (read_line_geometries(rec) for rec in self._wdbii_shp(scale, level=1).records())
        ax.add_geometries(borders, ccrs.PlateCarree(),
                          edgecolor=self.border_properties.strokecolor,
                          facecolor='none',
                          linewidth=self.border_properties.strokewidth,
                          alpha=self.border_properties.alpha)

    def draw_states(self, ax):
        logger.info("[MAP] Begin drawing states")
        scale = self.scale_properties.scale

        states = (read_line_geometries(rec) for rec in self._wdbii_shp(scale, level=2).records())
        ax.add_geometries(states, ccrs.PlateCarree(),
                          edgecolor=self.border_properties.strokecolor,
                          facecolor='none',
                          linewidth=self.border_properties.strokewidth,
                          alpha=self.border_properties.alpha)

    def draw_counties(self, ax):
        logger.info("[MAP] Begin drawing counties")
        counties = self._generic_shp('UScounties').geometries()
        ax.add_geometries(counties, ccrs.PlateCarree(),
                          edgecolor=self.county_properties.strokecolor,
                          linewidth=self.county_properties.strokewidth,
                          facecolor='none',
                          alpha=self.county_properties.alpha)

    def draw_roads(self, ax):
        logger.info("[MAP] Begin drawing highways")
        hwys = self._generic_shp('hways').geometries()
        ax.add_geometries(hwys, ccrs.PlateCarree(),
                          edgecolor=self.highway_properties.strokecolor,
                          linewidth=self.highway_properties.strokewidth,
                          facecolor='none',
                          alpha=self.highway_properties.alpha)

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
