import matplotlib.pyplot as plt

from weatherpy import ctables
from weatherpy import plotextras
from weatherpy.radar import radar2open
from weatherpy.radar import Nexrad2Request


def plot_latest_radar(station):
    text_color = '0.85'
    with radar2open(Nexrad2Request(station)[-1]) as radarplot:
        ctable = ctables.reflectivity.radarscope
        radarmap, _ = radarplot.make_plot(colortable=ctable)
        radarplot.range_ring(radarmap, color=text_color)
        radarmap.draw_default()
        plotextras.top_right_inset(radarmap.ax, ctable, color=text_color)

        title_text = '{} 0.5 deg Reflectivity, {}'.format(station,
                                                          radarplot.timestamp().strftime('%Y %b %d %H:%M UTC'))
        plotextras.bottom_right_stamp(title_text, radarmap.ax, color=text_color)
        plt.show()


if __name__ == '__main__':
    plot_latest_radar('KSGF')
