import cartopy.crs as ccrs
import matplotlib.pyplot as plt
import numpy as np

from weatherpy.calcs import pa2hPa, extrema


class MSLP(object):
    def __init__(self, data, lons, lats, unit='Pa', shifted_lons=True):
        self._lats = lats
        self._lons = lons - 180 * shifted_lons
        self._lons_shifted = shifted_lons
        if unit == 'Pa':
            self._data = pa2hPa(data)
        elif unit == 'hPa':
            self._data = data
        else:
            raise ValueError("Unsupported MSLP unit: {}".format(unit))

    def make_plot(self, mapper, colortable=None):
        contour_lvls = np.arange(900, 1100, 3)

        mapper.initialize_drawing()
        contour_lines = mapper.ax.contour(self._lons, self._lats, self._data,
                                          contour_lvls, colors='k', linewidths=1,
                                          transform=ccrs.PlateCarree(central_longitude=180 * self._lons_shifted))

        self._plot_highs_lows(mapper)
        self._label(contour_lines, contour_lvls)

    def _plot_highs_lows(self, mapper):
        lon_mesh, lat_mesh = np.meshgrid(self._lons, self._lats)

        local_min, local_max = extrema(self._data, mode='wrap', window=50)
        latlows, lonlows = lat_mesh[local_min], lon_mesh[local_min]
        lathighs, lonhighs = lat_mesh[local_max], lon_mesh[local_max]
        lowvals = self._data[local_min]
        highvals = self._data[local_max]

        def _do_plot(lonvals, latvals, pvals, letter, color):
            latlonsplotted = []
            # don't plot if there is already a L or H within x degrees of each other
            label_offset_deg = 1.0
            min_dist_deg = label_offset_deg
            map_extent = mapper.extent or (-180, 180, -90, 90)
            transform = ccrs.PlateCarree(central_longitude=180.0 * self._lons_shifted)

            for lon, lat, p in zip(lonvals, latvals, pvals):
                if map_extent[0] + min_dist_deg < lon < map_extent[1] - min_dist_deg \
                        and map_extent[2] + min_dist_deg < lat < map_extent[3] - min_dist_deg:
                    # good enough for local scales...
                    dist = [np.sqrt((lat - lat0) ** 2 + (lon - lon0) ** 2) for lat0, lon0 in latlonsplotted]
                    if not dist or min(dist) > min_dist_deg:
                        pctrs = plt.text(lon, lat, letter, fontsize=16, fontweight='bold',
                                         ha='center', va='center', color=color, transform=transform)
                        plabels = plt.text(lon, lat - label_offset_deg, str(int(p)), fontsize=9,
                                           ha='center', va='top', color=color, transform=transform,
                                           bbox=dict(boxstyle="square", ec='None', fc=(1, 1, 1, 0.5)))

                        pctrs.set_clip_on(True)
                        plabels.set_clip_on(True)
                        latlonsplotted.append((lat, lon))

        _do_plot(lonlows, latlows, lowvals, 'L', 'red')
        _do_plot(lonhighs, lathighs, highvals, 'H', 'blue')

    def _label(self, contour_lines, contour_lvls):
        # the inline spacing was carefully fine-tuned. Don't move it -10 <~ x <~ -5
        plt.clabel(contour_lines, contour_lvls, fontsize=7, fmt='%1.0f', inline_spacing=-8, inline=True)

