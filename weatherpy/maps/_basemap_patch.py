from mpl_toolkits.basemap import Basemap
import cartopy.crs as ccrs

from weatherpy import logger
from weatherpy.maps.mappers import MapperBase


class BasemapMapBase(MapperBase):
    def __init__(self, crs, bg_color=None):
        super(BasemapMapBase, self).__init__(crs, bg_color)
        self._bmap = None

    def _set_extent(self):
        if all((self._ax is not None, not self._extent_set, self._extent is not None,
                self._bmap is not None)):
            # self._bmap = BasemapMapBase._basemap_from_crs(self.crs, self._extent)
            # self._ax = self._bmap.ax
            x0, y0 = self._bmap(self._extent[0], self._extent[2])
            x1, y1 = self._bmap(self._extent[1], self._extent[3])
            self._ax.set_xlim(x0, x1)
            self._ax.set_ylim(y0, y1)
            self._ax.set_clip_on(True)
            self._extent_set = True

    @staticmethod
    def _basemap_from_crs(crs):
        proj_name = 'nsper'
        lon_0 = -75
        lat_0 = 0
        return Basemap(projection=proj_name, lon_0=lon_0, lat_0=lat_0)

    def initialize_drawing(self):
        if not self._is_drawing_initialized():
            self._bmap = BasemapMapBase._basemap_from_crs(self._crs)
            self._ax = self._bmap._check_ax()
            # TODO: set background color
        self._set_extent()

    def draw_coastlines(self):
        logger.info("[MAP] Begin drawing coastlines")
        self.initialize_drawing()
        self._bmap.drawcoastlines()

    def draw_borders(self):
        logger.info("[MAP] Begin drawing borders")
        self.initialize_drawing()
        self._bmap.drawcountries()

    def draw_states(self):
        logger.info("[MAP] Begin drawing states")
        self.initialize_drawing()
        self._bmap.drawstates()

    def draw_default(self):
        self.draw_coastlines()
        self.draw_borders()
        self.draw_states()


if __name__ == '__main__':
    import matplotlib.pyplot as plt
    map = BasemapMapBase(ccrs.NearsidePerspective())
    map.draw_default()
    map.extent = (-100, -65, 20, 60)
    plt.show()
