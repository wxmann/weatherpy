import warnings

import cartopy.crs as ccrs
import cartopy.feature as cfeat
import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap

basemap = 'basemap'
cartopy = 'cartopy'


class MapProjection(object):
    _basemap_res = {
        'low': 'c',
        'medium': 'l',
        'high': 'h'
    }

    _cartopy_res = {
        'low': '110m',
        'medium': '50m',
        'high': '10m'
    }

    lib_unavailable_msg = "{} library unavailable: must install it or try with a different library."

    _default_drawer = basemap

    def __init__(self, drawer=None):
        self.drawer = MapProjection._default_drawer if drawer is None else drawer

    def draw_map(self, res='medium', latlon_lines=True):
        if self.drawer == basemap:
            return self._draw_basemap(res, latlon_lines)
        elif self.drawer == cartopy:
            return self._draw_cartopy(res, latlon_lines)
        else:
            raise NotImplementedError("Unsupported drawer: {}".format(self.drawer))

    def _draw_basemap(self, res, latlon_lines):
        m = self._basemap_object(res)
        m.drawcoastlines()
        m.drawcountries()
        m.drawstates()
        if latlon_lines:
            pass
            # TODO: draw lat/lon grids
        return m

    def _basemap_object(self, res):
        raise NotImplementedError("Basemap object creation must be implemented in subclasses")

    def _draw_cartopy(self, res, latlon_lines):
        m = self._cartopy_object(res)
        res_str = MapProjection._cartopy_res[res]
        m.coastlines(resolution=res_str, color='black', linewidth='1')
        m.add_feature(cfeat.BORDERS, linewidth='1', edgecolor='black')
        states = cfeat.NaturalEarthFeature(category='cultural', name='admin_1_states_provinces_lakes',
                                           scale=res_str, facecolor='none')
        m.add_feature(states, linewidth='0.5')
        if latlon_lines:
            m.gridlines(linestyle='--', draw_labels=True)
        return m

    def _cartopy_object(self, res):
        raise NotImplementedError("Cartopy object creation must be implemented in subclasses")


class EquidistantCylindrical(MapProjection):
    def __init__(self, llcrnlon, llcrnlat, urcrnlon, urcrnlat, drawer=None):
        MapProjection.__init__(self, drawer)
        self.llcrnlon = llcrnlon
        self.llcrnlat = llcrnlat
        self.urcrnlon = urcrnlon
        self.urcrnlat = urcrnlat

    def _basemap_object(self, res):
        m = Basemap(projection='cyl',
                    llcrnrlat=self.llcrnlat, llcrnrlon=self.llcrnlon,
                    urcrnrlat=self.urcrnlat, urcrnrlon=self.urcrnlon,
                    resolution=MapProjection._basemap_res[res], area_thresh=1000)
        return m

    def _cartopy_object(self, res):
        crs = ccrs.PlateCarree()
        ax = plt.axes(projection=crs)
        ax.set_extent((self.llcrnlon, self.urcrnlon, self.llcrnlat, self.urcrnlat))
        return ax


class LambertConformal(MapProjection):
    def __init__(self, lat0, lon0, width, height, stdlat1=None, stdlat2=None, r_earth=6370997, drawer=None):
        MapProjection.__init__(self, drawer)
        self.lat0 = lat0
        self.lon0 = lon0
        self.stdlat1 = stdlat1
        self.stdlat2 = stdlat2
        self.r_earth = r_earth
        self.width = width
        self.height = height

    def _basemap_object(self, res):
        return Basemap(projection='lcc', rsphere=(self.r_earth, self.r_earth),
                       lat_0=self.lat0, lon_0=self.lon0,
                       lat_1=self.stdlat1, lat_2=self.stdlat2,
                       width=self.width, height=self.height,
                       resolution=MapProjection._basemap_res[res],
                       area_thresh=1000)

    def _cartopy_object(self, res):
        globe = ccrs.Globe(ellipse='sphere', semimajor_axis=self.r_earth,
                           semiminor_axis=self.r_earth)
        stdparas = [self.stdlat1] if self.stdlat1 is not None else None
        if stdparas is not None and self.stdlat2 is not None:
            stdparas.append(self.stdlat2)
        proj = ccrs.LambertConformal(central_latitude=self.lat0, central_longitude=self.lon0,
                                     standard_parallels=stdparas, globe=globe)
        return plt.axes(projection=proj)


# TODO: deprecate above code. We should opt for Cartopy instead of building an interface to plugin to both
# Cartopy and Basemap.

# STANDARD MAPS
# TODO: do we plan to use them anywhere?
# atlantic_basin = EquidistantCylindrical(llcrnlat=5.0, llcrnlon=-105.0, urcrnlat=60, urcrnlon=-5.0)
# north_america = LambertConformal(lat0=45, lon0=-100, width=11000000, height=8500000)

def coalesce_kwargs(kwargs, **fallback_values):
    result = {}
    for k in fallback_values:
        if k in kwargs:
            result[k] = kwargs[k]
        else:
            result[k] = fallback_values[k]
    return result


class CartopyMapProjection(object):
    def __init__(self, *args, **kwargs):
        self._crs = self._get_crs(*args, **kwargs)
        self._extent = None
        self._ax = None

    def _get_crs(self, *args, **kwargs):
        raise NotImplementedError("CRS implementations are delegated to subclasses.")

    @property
    def crs(self):
        return self._crs

    @property
    def extent(self):
        return self._extent

    @extent.setter
    def extent(self, extent_coord):
        if extent_coord is not None and len(extent_coord) != 4:
            raise ValueError("Must have four coordinates for extent box")
        self._extent = tuple(extent_coord)
        if self._ax is not None:
            self._ax.set_extent(self._extent)

    @property
    def axes(self):
        return self._ax

    def initialize_drawing(self):
        if not self._is_drawing_initialized():
            self._ax = plt.axes(projection=self.crs)
            if self._extent is not None:
                self._ax.set_extent(self._extent)

    def _is_drawing_initialized(self):
        return self._ax is not None

    def draw_coastlines(self, res='50m', **kwargs):
        self.initialize_drawing()
        self._ax.coastlines(**coalesce_kwargs(kwargs, resolution=res, color='black', linewidth='1'))

    def draw_borders(self, **kwargs):
        self.initialize_drawing()
        self._ax.add_feature(cfeat.BORDERS, **coalesce_kwargs(kwargs, linewidth='1', edgecolor='black'))

    def draw_states(self, res='50m', **kwargs):
        self.initialize_drawing()
        states = cfeat.NaturalEarthFeature(category='cultural', name='admin_1_states_provinces_lakes',
                                           scale=res, facecolor='none')
        self._ax.add_feature(states, **coalesce_kwargs(kwargs, linewidth='0.5'))

    def draw_gridlines(self, **kwargs):
        self.initialize_drawing()
        self._ax.gridlines(**coalesce_kwargs(kwargs, linestyle='--', draw_labels=True))

    def draw_default_map(self):
        self.draw_coastlines()
        self.draw_borders()
        self.draw_states()
        self.draw_gridlines()


class EquidistantCylindricalMapper(CartopyMapProjection):

    def _get_crs(self):
        return ccrs.PlateCarree()


class LambertConformalMapper(CartopyMapProjection):

    def __init__(self, lat0, lon0, stdlat1=None, stdlat2=None, r_earth=6370997):
        CartopyMapProjection.__init__(self, lat0, lon0, stdlat1, stdlat2, r_earth)
        self._param_metadata = {
            'lat0': lat0,
            'lon0': lon0,
            'stdlat1': stdlat1,
            'stdlat2': stdlat2,
            'r_earth': r_earth
        }

    def _get_crs(self, lat0, lon0, stdlat1, stdlat2, r_earth):
        globe = ccrs.Globe(ellipse='sphere', semimajor_axis=r_earth,
                           semiminor_axis=r_earth)
        stdparas = [stdlat1] if stdlat1 is not None else None
        if stdparas is not None and stdlat2 is not None:
            stdparas.append(stdlat2)
        return ccrs.LambertConformal(central_latitude=lat0, central_longitude=lon0,
                                     standard_parallels=stdparas, globe=globe)

    def draw_gridlines(self, **kwargs):
        warnings.warn('Gridline labels are not supported by Cartopy on Lambert Conformal projection')
        if 'draw_labels' in kwargs:
            kwargs['draw_labels'] = False
        self._ax.gridlines(**coalesce_kwargs(kwargs, linestyle='--', draw_labels=False))
