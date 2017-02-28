import matplotlib.pyplot as plt

from weatherpy import colortables
from weatherpy import plotutils
from weatherpy.nexrad2 import Nexrad2Request, radaropen


def plot_latest_radar(station):
    ctable = colortables.radarscope
    text_color = '0.75'
    with radaropen(Nexrad2Request(station)[-1]) as radarplot:
        radarmap = radarplot.make_plot(colortable=ctable)
        radarmap.draw_default()
        plotutils.plot_topright_inset(radarmap.ax, ctable,
                                      title=radarplot.units, color=text_color)

        title_text = 'KLIX 0.5 deg Reflectivity, {}'.format(radarplot.timestamp.strftime('%Y %b %d %H:%M UTC'))
        plotutils.bottom_right_stamp(title_text, radarmap.ax, color=text_color)
        plt.show()


if __name__ == '__main__':
    plot_latest_radar('KLIX')