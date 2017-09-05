import os
import warnings

import cartopy
import math
from cartopy import crs as ccrs
from cartopy import feature as cfeat
from matplotlib import pyplot as plt
import numpy as np
import shapely.geometry as sgeom

import config
from weatherpy.internal import logger, haversine_distance
from weatherpy.internal.pyhelpers import coalesce_kwargs
from weatherpy.maps import properties
from weatherpy.maps.extents import geobbox


class MapperBase(object):
    def __init__(self, crs, bg_color=None):
        self._crs = crs
        self._extent = None
        self._ax = None
        self._extent_set = False
        self._bg_color = bg_color

    @property
    def crs(self):
        return self._crs

    @property
    def extent(self):
        return self._extent

    @extent.setter
    def extent(self, extent_coord):
        logger.info('[MAP] Setting extent to: {}'.format(extent_coord))

        if isinstance(extent_coord, geobbox):
            self._extent = extent_coord
        else:
            if extent_coord is None or len(extent_coord) != 4:
                raise ValueError("Extent must be of form (x0, x1, y0, y1)")
            self._extent = geobbox(*extent_coord)

        self._extent_set = False
        self._set_extent()

    def _set_extent(self):
        if all((self._ax is not None, not self._extent_set, self._extent is not None)):
            self._ax.set_extent(self._extent)
            self._extent_set = True

    @property
    def ax(self):
        if self._ax is None:
            # TODO: raise a better exception?
            raise ValueError("Map is uninitialized!")
        return self._ax

    def initialized(self):
        return self._ax is not None

    def initialize_drawing(self, subplot=None, fig=None, reinit=False):
        if not reinit and self._ax is not None:
            warnings.warn('Plot is already initialized. Further calls to this method will have no effect.')
            return

        if subplot is not None:
            if fig is None:
                fig = plt.gcf()
            self._ax = fig.add_subplot(subplot, projection=self.crs)
        else:
            self._ax = plt.axes(projection=self.crs)

        if self._bg_color is not None:
            self._ax.background_patch.set_facecolor(self._bg_color)
        self._set_extent()

    def draw_gridlines(self, **kwargs):
        self.ax.gridlines(**coalesce_kwargs(kwargs, linestyle='--', draw_labels=False))

    def draw_default(self):
        raise NotImplementedError("Default Maps need to be implemented in subclasses")


class LargeScaleMap(MapperBase):
    def __init__(self, crs, bg_color=None):
        super(LargeScaleMap, self).__init__(crs, bg_color)
        self._properties = properties.Properties(strokewidth=0.5, strokecolor='black', fill='none',
                                                 resolution='50m')

    @property
    def properties(self):
        return self._properties

    def draw_coastlines(self):
        logger.info("[MAP] Begin drawing coastlines")
        self.ax.coastlines(resolution=self.properties.resolution, color=self.properties.strokecolor,
                           linewidth=self.properties.strokewidth)

    def draw_borders(self):
        logger.info("[MAP] Begin drawing borders")
        self.ax.add_feature(cfeat.BORDERS, edgecolor=self.properties.strokecolor,
                            linewidth=self.properties.strokewidth)

    def draw_states(self):
        logger.info("[MAP] Begin drawing states")
        states = cfeat.NaturalEarthFeature(category='cultural', name='admin_1_states_provinces_lakes',
                                           scale=self.properties.resolution, facecolor=self.properties.fill)
        self.ax.add_feature(states, edgecolor=self.properties.strokecolor, linewidth=self.properties.strokewidth)

    def draw_default(self):
        self.draw_coastlines()
        self.draw_borders()
        self.draw_states()


class DetailedUSMap(MapperBase):
    def __init__(self, crs, bg_color=None):
        super(DetailedUSMap, self).__init__(crs, bg_color)
        self._borderprops = properties.Properties(strokewidth=1.0, strokecolor='gray', fill='none', alpha=1.0)
        self._countyprops = properties.Properties(strokewidth=0.5, strokecolor='gray', fill='none', alpha=1.0)
        self._hwyprops = properties.Properties(strokewidth=0.65, strokecolor='brown', fill='none', alpha=0.8)

    @property
    def border_properties(self):
        return self._borderprops

    @property
    def county_properties(self):
        return self._countyprops

    @property
    def highway_properties(self):
        return self._hwyprops

    def _add_shp_geoms(self, filename, crs=None, **kwargs):
        if crs is None:
            crs = ccrs.PlateCarree()
        self.ax.add_geometries(self._shpfile(filename).geometries(), crs, **kwargs)

    def _shpfile(self, filename):
        shpfile_dir = filename
        filename = filename + '.shp'
        file = os.path.join(config.SHAPEFILE_DIR, shpfile_dir, filename)
        return cartopy.io.shapereader.Reader(file)

    def draw_borders(self):
        logger.info("[MAP] Begin drawing borders")
        self._add_shp_geoms('cb_2015_us_nation_5m', edgecolor=self.border_properties.strokecolor,
                            linewidth=self.border_properties.strokewidth,
                            facecolor=self.border_properties.fill,
                            alpha=self.border_properties.alpha)
        self._add_shp_geoms('cb_2015_us_state_5m', edgecolor=self.border_properties.strokecolor,
                            linewidth=self.border_properties.strokewidth,
                            facecolor=self.border_properties.fill,
                            alpha=self.border_properties.alpha)

    def draw_counties(self):
        logger.info("[MAP] Begin drawing counties")
        self._add_shp_geoms('cb_2015_us_county_5m', edgecolor=self.county_properties.strokecolor,
                            linewidth=self.county_properties.strokewidth,
                            facecolor=self.county_properties.fill,
                            alpha=self.county_properties.alpha)

    def draw_highways(self):
        logger.info("[MAP] Begin drawing highways")
        self._add_shp_geoms('tl_2016_us_primaryroads', edgecolor=self.highway_properties.strokecolor,
                            linewidth=self.highway_properties.strokewidth,
                            facecolor=self.highway_properties.fill,
                            alpha=self.highway_properties.alpha)

    def draw_default(self):
        self.draw_borders()
        self.draw_counties()
        self.draw_highways()


class GSHHSMap(MapperBase):
    def __init__(self, crs, bg_color=None):
        super(GSHHSMap, self).__init__(crs, bg_color)
        self._scaleprops = properties.Properties(scale='i')
        self._borderprops = properties.Properties(strokewidth=1.0, strokecolor='gray', fill='none', alpha=1.0)
        self._countyprops = properties.Properties(strokewidth=0.5, strokecolor='gray', fill='none', alpha=1.0)
        self._hwyprops = properties.Properties(strokewidth=0.65, strokecolor='brown', fill='none', alpha=0.8)

    @property
    def scale_properties(self):
        return self._scaleprops

    @property
    def border_properties(self):
        return self._borderprops

    @property
    def county_properties(self):
        return self._countyprops

    @property
    def highway_properties(self):
        return self._hwyprops

    def draw_default(self):
        self._draw_default_with_lake_threshold(300)

    def draw_default_detailed(self):
        self._draw_default_with_lake_threshold(80)
        self.draw_counties()
        self.draw_highways()

    def _draw_default_with_lake_threshold(self, threshold):
        self.draw_coastlines()
        self.draw_lakes(threshold)
        self.draw_borders()
        self.draw_states()

    def draw_coastlines(self):
        logger.info("[MAP] Begin drawing coastlines")
        scale = self.scale_properties.scale

        coastlines = cfeat.GSHHSFeature(scale, levels=[1])
        self.ax.add_feature(coastlines, edgecolor=self.border_properties.strokecolor,
                            linewidth=self.border_properties.strokewidth,
                            facecolor='none',
                            alpha=self.border_properties.alpha)

    def draw_lakes(self, threshold=300):
        logger.info("[MAP] Begin drawing lakes")
        scale = self.scale_properties.scale

        lakes = (rec.geometry for rec in self._ghssh_shp(scale, level=2).records()
                 if _size(rec) > threshold)
        self.ax.add_geometries(lakes, ccrs.PlateCarree(),
                               edgecolor=self.border_properties.strokecolor,
                               linewidth=self.border_properties.strokewidth,
                               facecolor='none',
                               alpha=self.border_properties.alpha)

    def draw_borders(self):
        logger.info("[MAP] Begin drawing borders")
        scale = self.scale_properties.scale

        borders = (read_line_geometries(rec) for rec in self._wdbii_shp(scale, level=1).records())
        self.ax.add_geometries(borders, ccrs.PlateCarree(),
                               edgecolor=self.border_properties.strokecolor,
                               facecolor='none',
                               linewidth=self.border_properties.strokewidth,
                               alpha=self.border_properties.alpha)

    def draw_states(self):
        logger.info("[MAP] Begin drawing states")
        scale = self.scale_properties.scale

        states = (read_line_geometries(rec) for rec in self._wdbii_shp(scale, level=2).records())
        self.ax.add_geometries(states, ccrs.PlateCarree(),
                               edgecolor=self.border_properties.strokecolor,
                               facecolor='none',
                               linewidth=self.border_properties.strokewidth,
                               alpha=self.border_properties.alpha)

    def draw_counties(self):
        logger.info("[MAP] Begin drawing counties")
        counties = self._generic_shp('UScounties').geometries()
        self.ax.add_geometries(counties, ccrs.PlateCarree(),
                               edgecolor=self.county_properties.strokecolor,
                               linewidth=self.county_properties.strokewidth,
                               facecolor='none',
                               alpha=self.county_properties.alpha)

    def draw_highways(self):
        logger.info("[MAP] Begin drawing highways")
        hwys = self._generic_shp('hways').geometries()
        self.ax.add_geometries(hwys, ccrs.PlateCarree(),
                               edgecolor=self.highway_properties.strokecolor,
                               linewidth=self.highway_properties.strokewidth,
                               facecolor='none',
                               alpha=self.highway_properties.alpha)

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
