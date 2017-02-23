import matplotlib.pyplot as plt

from weatherpy import colortables
from weatherpy import plotutils
from weatherpy.nexrad2 import Nexrad2Request, radaropen


def plot_latest_radar(station):
    ctable = colortables.radarscope
    with radaropen(Nexrad2Request(station)[-1]) as radarplot:
        radarmap = radarplot.make_plot(colortable=ctable)
        radarmap.draw_default()
        plotutils.plot_offright_inset(radarmap.ax, ctable, title=radarplot.units)
        plt.show()


if __name__ == '__main__':
    plot_latest_radar('KMLB')