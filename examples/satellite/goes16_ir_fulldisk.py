import matplotlib.pyplot as plt

from weatherpy import maps
from weatherpy.satellite import goes16

if __name__ == '__main__':
    sel = goes16.fulldisk(channel=14)
    with sel.latest() as plotter:
        mapper = maps.LargeScaleMap(plotter.default_map().crs)
        plotter.make_plot(mapper=mapper)
        mapper.draw_default()
        plt.show()