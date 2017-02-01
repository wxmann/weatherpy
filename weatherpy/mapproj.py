import warnings
from functools import wraps

import cartopy.crs as ccrs
import cartopy.feature as cfeat
import matplotlib.pyplot as plt
import weatherpy._mapproj_legacy as _legacy

from weatherpy._pyhelpers import coalesce_kwargs

# STANDARD MAPS
# TODO: do we plan to use them anywhere?
# atlantic_basin = EquidistantCylindrical(llcrnlat=5.0, llcrnlon=-105.0, urcrnlat=60, urcrnlon=-5.0)
# north_america = LambertConformal(lat0=45, lon0=-100, width=11000000, height=8500000)

EquidistantCylindrical = _legacy.EquidistantCylindrical
LambertConformal = _legacy.LambertConformal


def to_mapper(func):
    @wraps(func)
    def func_wrapper(*args, **kwargs):
        crs = func(*args, **kwargs)
        return CartopyMapper(crs)
    return func_wrapper


class CartopyMapper(object):
    DEFAULT_LINE_WIDTH = 0.5
    DEFAULT_LINE_COLOR = 'black'
    DEFAULT_RESOLUTION = '50m'

    def __init__(self, crs):
        self._crs = crs
        self._extent = None
        self._ax = None
        self.line_properties = {
            'color': CartopyMapper.DEFAULT_LINE_COLOR,
            'width': CartopyMapper.DEFAULT_LINE_WIDTH,
            'resolution': CartopyMapper.DEFAULT_RESOLUTION
        }
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
        if all((
            self._ax is not None,
            not self._extent_set,
            self._extent is not None
        )):
            self._ax.set_extent(self._extent)
            self._extent_set = True

    @property
    def ax(self):
        return self._ax

    def set_line_property(self, prop, val):
        if prop in self.line_properties:
            self.line_properties[prop] = val
        else:
            warnings.warn("There is no line property: {}. Nothing has been set.".format(prop))

    def initialize_drawing(self):
        if not self._is_drawing_initialized():
            self._ax = plt.axes(projection=self.crs)
            self._set_extent()

    def _is_drawing_initialized(self):
        return self._ax is not None

    def draw_coastlines(self, **kwargs):
        self.initialize_drawing()
        self._ax.coastlines(**coalesce_kwargs(kwargs, resolution=self.line_properties['resolution'],
                                              color=self.line_properties['color'],
                                              linewidth=self.line_properties['width']))

    def draw_borders(self, **kwargs):
        self.initialize_drawing()
        self._ax.add_feature(cfeat.BORDERS, **coalesce_kwargs(kwargs, edgecolor=self.line_properties['color'],
                                                              linewidth=self.line_properties['width']))

    def draw_states(self, **kwargs):
        self.initialize_drawing()
        states = cfeat.NaturalEarthFeature(category='cultural', name='admin_1_states_provinces_lakes',
                                           scale=self.line_properties['resolution'], facecolor='none')
        self._ax.add_feature(states, **coalesce_kwargs(kwargs, edgecolor=self.line_properties['color'],
                                                       linewidth=self.line_properties['width']))

    def draw_gridlines(self, **kwargs):
        self.initialize_drawing()
        self._ax.gridlines(**coalesce_kwargs(kwargs, linestyle='--', draw_labels=False))

    def draw_default_map(self):
        self.draw_coastlines()
        self.draw_borders()
        self.draw_states()
        self.draw_gridlines()


@to_mapper
def platecarree(central_longitude=0.0):
    return ccrs.PlateCarree(central_longitude)


# default lat0/lon0 taken from the Cartopy LambertConformal CRS class.
@to_mapper
def lambertconformal(lat0=39.0, lon0=-96.0, stdlat1=None, stdlat2=None, r_earth=6370997):
    globe = ccrs.Globe(ellipse='sphere', semimajor_axis=r_earth, semiminor_axis=r_earth)
    stdparas = [stdlat1] if stdlat1 is not None else None
    if stdparas is not None and stdlat2 is not None:
        stdparas.append(stdlat2)

    return ccrs.LambertConformal(central_latitude=lat0, central_longitude=lon0,
                                 standard_parallels=stdparas, globe=globe)
