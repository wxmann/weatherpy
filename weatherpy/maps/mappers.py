import warnings

import cartopy
from cartopy import crs as ccrs
from cartopy import feature as cfeat
from matplotlib import pyplot as plt

import config
from weatherpy import logger
from weatherpy.internal.pyhelpers import coalesce_kwargs
from weatherpy.maps import properties


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
        if extent_coord is None or len(extent_coord) != 4:
            raise ValueError("Extent must be of form (x0, x1, y0, y1)")
        logger.info('[MAP] Setting extent to (lon0, lon1, lat0, lat1): {}'.format(extent_coord))
        self._extent = tuple(extent_coord)
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
        return cartopy.io.shapereader.Reader('{0}/{1}/{1}.shp'.format(config.SHAPEFILE_DIR, filename))

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
        # high_res: 'c_11au16'
        # medium_res: 'cb_2015_us_county_5m'
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
