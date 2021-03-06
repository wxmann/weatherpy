import matplotlib.pyplot as plt

from weatherpy import plotextras
from weatherpy.radar import nexradl2


def plot_latest_radar(station):
    text_color = '0.85'
    sel = nexradl2.selectfor(station)
    with sel.latest() as radarplot:
        refl_panel = radarplot.default_map()
        refl_panel.initialize_drawing(subplot=121)
        refl_panel.draw_default_detailed()

        radarplot.set_radar('Reflectivity')
        _, ctable = radarplot.make_plot(refl_panel)
        radarplot.range_ring(refl_panel, color=text_color)
        plotextras.colorbar_inset(refl_panel.ax, ctable, color=text_color)
        plotextras.bottom_right_stamp('Current Reflectivity', refl_panel.ax, color=text_color)

        vel_panel = radarplot.default_map()
        vel_panel.initialize_drawing(subplot=122)
        vel_panel.draw_default_detailed()

        radarplot.set_radar('RadialVelocity')
        _, ctable = radarplot.make_plot(vel_panel)
        radarplot.range_ring(vel_panel, color=text_color)
        plotextras.colorbar_inset(vel_panel.ax, ctable, color=text_color)
        plotextras.bottom_right_stamp('Current Velocity', vel_panel.ax, color=text_color)

        plt.gcf().subplots_adjust(wspace=0, hspace=0)
        plt.show()


if __name__ == '__main__':
    plot_latest_radar('KSGF')