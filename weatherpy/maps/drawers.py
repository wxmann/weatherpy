import cartopy
from cartopy import feature as cfeat
from cartopy import crs as ccrs
from matplotlib import pyplot as plt

import config
from weatherpy._pyhelpers import coalesce_kwargs
from weatherpy.maps import properties


class BaseCartopyDrawer(object):
    def __init__(self, crs):
        self._crs = crs
        self._extent = None
        self._ax = None
        self._extent_set = False

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
        self._extent = tuple(extent_coord)
        self._extent_set = False
        self._set_extent()

    def _set_extent(self):
        if all((self._ax is not None, not self._extent_set, self._extent is not None)):
            self._ax.set_extent(self._extent)
            self._extent_set = True

    @property
    def ax(self):
        return self._ax

    def initialize_drawing(self):
        if not self._is_drawing_initialized():
            self._ax = plt.axes(projection=self.crs)
            self._set_extent()

    def _is_drawing_initialized(self):
        return self._ax is not None

    def draw_gridlines(self, **kwargs):
        self.initialize_drawing()
        self._ax.gridlines(**coalesce_kwargs(kwargs, linestyle='--', draw_labels=False))

    def draw_default(self):
        raise NotImplementedError("Default Maps need to be implemented in subclasses")


class LargeScaleMap(BaseCartopyDrawer):
    def __init__(self, crs):
        super(LargeScaleMap, self).__init__(crs)
        self._properties = properties.Properties(strokewidth=0.5, strokecolor='black', fill='none',
                                                 resolution='50m')

    @property
    def properties(self):
        return self._properties

    def draw_coastlines(self):
        self.initialize_drawing()
        self._ax.coastlines(resolution=self.properties.resolution, color=self.properties.strokecolor,
                            linewidth=self.properties.strokewidth)

    def draw_borders(self):
        self.initialize_drawing()
        self._ax.add_feature(cfeat.BORDERS, edgecolor=self.properties.strokecolor,
                             linewidth=self.properties.strokewidth)

    def draw_states(self):
        self.initialize_drawing()
        states = cfeat.NaturalEarthFeature(category='cultural', name='admin_1_states_provinces_lakes',
                                           scale=self.properties.resolution, facecolor=self.properties.fill)
        self._ax.add_feature(states, edgecolor=self.properties.strokecolor, linewidth=self.properties.strokewidth)

    def draw_default(self):
        self.draw_coastlines()
        self.draw_borders()
        self.draw_states()


class DetailedUSMap(BaseCartopyDrawer):
    def __init__(self, crs):
        super(DetailedUSMap, self).__init__(crs)
        self._borderprops = properties.Properties(strokewidth=0.6, strokecolor='black', fill='none')
        self._countyprops = properties.Properties(strokewidth=0.4, strokecolor='gray', fill='none')
        self._hwyprops = properties.Properties(strokewidth=0.3, strokecolor='blue', fill='none', alpha=0.7)

    @property
    def border_properties(self):
        return self._borderprops

    @property
    def county_properties(self):
        return self._countyprops

    @property
    def highway_properties(self):
        return self._hwyprops

    def _shpfile(self, filename):
        return cartopy.io.shapereader.Reader('{0}/{1}/{1}.shp'.format(config.SHAPEFILE_DIR, filename))

    def draw_borders(self):
        self.initialize_drawing()
        self._ax.add_geometries(self._shpfile('cb_2015_us_state_5m').geometries(), ccrs.PlateCarree(),
                                edgecolor=self.border_properties.strokecolor,
                                linewidth=self.border_properties.strokewidth,
                                facecolor=self.border_properties.fill)

    def draw_counties(self):
        self.initialize_drawing()
        self._ax.add_geometries(self._shpfile('cb_2015_us_county_5m').geometries(), ccrs.PlateCarree(),
                                edgecolor=self.county_properties.strokecolor,
                                linewidth=self.county_properties.strokewidth,
                                facecolor=self.county_properties.fill)

    def draw_highways(self):
        self.initialize_drawing()
        self._ax.add_geometries(self._shpfile('tl_2016_us_primaryroads').geometries(), ccrs.PlateCarree(),
                                edgecolor=self.highway_properties.strokecolor,
                                linewidth=self.highway_properties.strokewidth,
                                facecolor=self.highway_properties.fill,
                                alpha=self.highway_properties.alpha)

    def draw_default(self):
        self.draw_borders()
        self.draw_counties()
        self.draw_highways()
