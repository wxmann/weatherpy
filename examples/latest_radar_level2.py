import matplotlib.pyplot as plt

from weatherpy import colortables
from weatherpy import plotextras
from weatherpy.nexrad2 import Nexrad2Request, radar2open


def plot_latest_radar(station):
    ctable = colortables.radarscope
    text_color = '0.85'
    with radar2open(Nexrad2Request(station)[-1]) as radarplot:
        radarmap = radarplot.make_plot(colortable=ctable)
        radarplot.range_ring(color=text_color)
        radarmap.draw_default()
        plotextras.top_right_inset(radarmap.ax, ctable, color=text_color)

        title_text = '{} 0.5 deg Reflectivity, {}'.format(station,
                                                          radarplot.timestamp.strftime('%Y %b %d %H:%M UTC'))
        plotextras.bottom_right_stamp(title_text, radarmap.ax, color=text_color)
        plt.show()


if __name__ == '__main__':
    plot_latest_radar('KMUX')
