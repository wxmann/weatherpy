from datetime import datetime, timedelta

from weatherpy import colortables
from weatherpy import plotutils
from weatherpy.nexrad2 import Nexrad2Request, radaropen
import matplotlib.pyplot as plt


def plot_latest_radar(station):
    ctable = colortables.nws
    with radaropen(Nexrad2Request(station)[-1]) as radarplot:
        radarmap = radarplot.make_plot(colortable=ctable)
        radarmap.draw_default_map()
        plotutils.plot_offright_inset(radarmap.ax, ctable, title=radarplot.units)
        plt.show()


def save_lix():
    ctable = colortables.nws
    radarurls = Nexrad2Request('KLIX')[datetime(2017, 2, 7, 15, 0): datetime(2017, 2, 7, 16, 0): timedelta(minutes=5)]
    for radarurl in radarurls:
        with radaropen(radarurl) as radar:
            radarmap = radar.make_plot(colortable=ctable)
            radarmap.draw_detailed_us_map()
            plt.title('LIX Reflectivity Tilt 1 {}'.format(radar.timestamp.strftime('%Y-%m-%dT%H:%M:%SZ')))
            plotutils.plot_legend(ctable)
            plotutils.save_image_no_border(radarmap.ax,
                                           r"/your/location/here".format(
                                               radar.timestamp.strftime('%Y%d%m%H%M')), 175)
            plt.close()


if __name__ == '__main__':
    plot_latest_radar('KLIX')
    # save_lix()
