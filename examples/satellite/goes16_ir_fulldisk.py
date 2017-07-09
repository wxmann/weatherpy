import matplotlib.pyplot as plt

from weatherpy.satellite import goes16

if __name__ == '__main__':
    sel = goes16.fulldisk(channel=14)
    plotter = sel.latest()
    mapper, _ = plotter.make_plot()
    mapper.properties.strokecolor = 'yellow'
    mapper.draw_default()
    plt.show()