import cartopy.crs as ccrs
import matplotlib.pyplot as plt
import numpy as np

from weatherpy.calcs import pa2hPa, extrema
from weatherpy.maps.mappers import MapperBase


class BaseUAPlot(object):
    def __init__(self, data, lons, lats, mapper):
        self._lats = lats
        self._lons = lons
        self._data = data
        self._mapper = mapper

    @property
    def mapper(self):
        return self._mapper

    @mapper.setter
    def mapper(self, newmapper):
        if not isinstance(newmapper, MapperBase):
            raise ValueError("Provided argument is not a valid mapper")
        self._mapper = newmapper


def label_contours(contours, levels):
    labels = plt.clabel(contours, levels, fontsize=10, fmt='%1.0f',
                        inline_spacing=-8, inline=True)
    for label in labels:
        label.set_rotation(0)


class MSLP(BaseUAPlot):
    def __init__(self, data, lons, lats, mapper, unit='Pa'):
        super(MSLP, self).__init__(data, lons, lats, mapper)
        if unit == 'Pa':
            self._data = pa2hPa(data)
        elif unit == 'hPa':
            self._data = data
        else:
            raise ValueError("Unsupported MSLP unit: {}".format(unit))

    def contours(self, levels=None):
        if levels is None:
            levels = np.arange(900, 1100, 3)
        self._mapper.initialize_drawing()
        contour_lines = self._mapper.ax.contour(self._lons, self._lats, self._data,
                                                levels, colors='k', linewidths=1,
                                                transform=ccrs.PlateCarree())
        label_contours(contour_lines, levels)

    def high_low_centers(self):
        lon_mesh, lat_mesh = np.meshgrid(self._lons, self._lats)
        local_min, local_max = extrema(self._data, mode='wrap', window=50)
        latlows, lonlows = lat_mesh[local_min], lon_mesh[local_min]
        lathighs, lonhighs = lat_mesh[local_max], lon_mesh[local_max]
        lowvals = self._data[local_min]
        highvals = self._data[local_max]

        def _do_plot(lonvals, latvals, pvals, letter, color):
            latlonsplotted = []
            # don't plot if there is already a L or H within x degrees of each other
            label_offset_deg = 0.6
            min_dist_deg = label_offset_deg
            transform = ccrs.PlateCarree()

            for lon, lat, p in zip(lonvals, latvals, pvals):
                dist = [np.sqrt((lat - lat0) ** 2 + (lon - lon0) ** 2) for lat0, lon0 in latlonsplotted]
                if not dist or min(dist) > min_dist_deg:
                    pctrs = plt.text(lon, lat, letter, fontsize=18, fontweight='bold',
                                     ha='center', va='center', color=color, transform=transform)
                    plabels = plt.text(lon, lat - label_offset_deg, str(int(p)), fontsize=12,
                                       ha='center', va='top', color=color, transform=transform,
                                       bbox=dict(boxstyle="square", ec='None', fc=(1, 1, 1, 0.5)))

                    pctrs.set_clip_on(True)
                    plabels.set_clip_on(True)
                    latlonsplotted.append((lat, lon))

        _do_plot(lonlows, latlows, lowvals, 'L', 'red')
        _do_plot(lonhighs, lathighs, highvals, 'H', 'blue')


class GeopotentialHeight(BaseUAPlot):
    def __init__(self, data, lons, lats, mapper):
        super(GeopotentialHeight, self).__init__(data, lons, lats, mapper)
        self._data /= 10.0

    def contours(self, levels=None):
        if levels is None:
            levels = np.arange(420, 630, 6)
        self._mapper.initialize_drawing()
        contour_lines = self._mapper.ax.contour(self._lons, self._lats, self._data,
                                                levels, colors='k', linewidths=1,
                                                transform=ccrs.PlateCarree())
        label_contours(contour_lines, levels)