import warnings

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
        if extent_coord is None:
            self._extent = None
            if self._ax is not None:
                self._ax.set_global()
        else:
            if len(extent_coord) != 4:
                raise ValueError("Must have four coordinates for extent box")
            self._extent = tuple(extent_coord)
            if self._ax is not None:
                self._ax.set_extent(self._extent)

    @property
    def ax(self):
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
        self._ax.gridlines(**coalesce_kwargs(kwargs, linestyle='--', draw_labels=False))

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
