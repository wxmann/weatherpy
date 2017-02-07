from weatherpy import colortables
from weatherpy import plotutils
from weatherpy.nexrad2 import Nexrad2Request
import matplotlib.pyplot as plt


def plot_latest_radar(station):
    ctable = colortables.radarscope
    with Nexrad2Request(station)[-1] as radarplot:
        # radarplot.draw_hist(True)
        radarmap = radarplot.make_plot(colortable=ctable)
        radarmap.draw_coastlines()
        radarmap.draw_borders()
        radarmap.draw_states()
        # radarmap.draw_counties()
        plotutils.plot_legend(ctable)
        plt.show()


if __name__ == '__main__':
    plot_latest_radar('KLIX')