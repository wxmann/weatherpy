from weatherpy import colortables
from weatherpy import plotutils
from weatherpy.nexrad2 import Nexrad2Request
import matplotlib.pyplot as plt


def plot_latest_radar(station):
    with Nexrad2Request(station)[-1] as radarplot:
        radarmap = radarplot.make_plot()
        radarmap.draw_coastlines()
        radarmap.draw_borders()
        radarmap.draw_states()
        plotutils.plot_legend(colortables.refl_avl)
        plt.show()


if __name__ == '__main__':
    plot_latest_radar('KDAX')