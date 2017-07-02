import matplotlib.pyplot as plt

from weatherpy.maps import extents
from weatherpy.satellite import goes16

if __name__ == '__main__':
    sel = goes16.conus(channel=14)
    plotter = sel.latest()
    mapper, _ = plotter.make_plot(extent=extents.conus)
    mapper.properties.strokecolor = 'yellow'
    mapper.draw_default()
    plt.show()