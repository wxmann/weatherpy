import matplotlib.pyplot as plt
import cartopy.crs as ccrs

from weatherpy import maps
from weatherpy.maps import extents
from weatherpy.satellite import goes16

if __name__ == '__main__':
    sel = goes16.conus(channel=14)

    with sel.latest() as plotter:
        bg_map = maps.GSHHSMap(crs=ccrs.LambertConformal())
        plotter.make_plot(mapper=bg_map, extent=extents.conus)
        bg_map.draw_default()
        plt.show()