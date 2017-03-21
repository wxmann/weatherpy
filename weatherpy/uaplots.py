import cartopy.crs as ccrs
import numpy as np

from weatherpy.calcs import pa2hPa, extrema
from weatherpy.maps import mappers


class MSLP(object):
    def __init__(self, data, lats, lons, unit='Pa'):
        self._lats = lats
        self._lons = lons
        if unit == 'Pa':
            self._data = pa2hPa(data)
        elif unit == 'hPa':
            self._data = data
        else:
            raise ValueError("Unsupported MSLP unit: {}".format(unit))

    # def default_map(self):
    #     mapper = mappers.LargeScaleMap(ccrs.PlateCarree(central_longitude=180.0))
    #     min_lon, max_lon = self._lons.min(), self._lons.max()
    #     min_lat, max_lat = self._lats.min(), self._lats.max()
    #     mapper.extent = min_lon, max_lon, min_lat, max_lat
    #     return mapper

    def make_plot(self, mapper, colortable=None):
        # if mapper is None:
        #     mapper = mappers.LargeScaleMap(ccrs.PlateCarree())

        local_min, local_max = extrema(self._data, mode='wrap', window=50)
        contour_lvls = np.arange(900, 1100, 5)

        mapper.initialize_drawing()
        mapper.ax.contour(self._lons, self._lats, self._data,
                          contour_lvls, colors='k', linewidths=1)

