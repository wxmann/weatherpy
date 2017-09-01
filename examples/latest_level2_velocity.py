import matplotlib.pyplot as plt

from weatherpy import plotextras
from weatherpy.radar import nexradl2


def plot_latest_radar(station):
    text_color = '0.85'
    sel = nexradl2.selectfor(station)
    with sel.latest() as radarplot:
        radarplot.set_radar('RadialVelocity')
        radarmap, ctable = radarplot.make_plot()
        radarplot.range_ring(radarmap, color=text_color)
        radarmap.draw_default()
        plotextras.top_right_inset(radarmap.ax, ctable, color=text_color)

        title_text = '{} 0.5 deg Velocity, {}'.format(station,
                                                      radarplot.timestamp.strftime('%Y %b %d %H:%M UTC'))
        plotextras.bottom_right_stamp(title_text, radarmap.ax, color=text_color)
        plt.show()


if __name__ == '__main__':
    # plot_latest_radar('KLBB')
    plot_latest_radar('KSGF')
