import matplotlib.pyplot as plt

from weatherpy.maps import extents
from weatherpy.satellite import goes16

if __name__ == '__main__':
    sel = goes16.conus(channel=2)
    plotter = sel.latest()
    mapper, _ = plotter.make_plot()
    mapper.extent = extents.southern_plains
    mapper.properties.strokecolor = 'yellow'
    mapper.draw_default()
    plt.show()