import matplotlib.pyplot as plt
from matplotlib import patheffects

from weatherpy import ctables
from weatherpy import plotextras
from weatherpy.maps import LargeScaleMap
from weatherpy.maps import projections
from weatherpy.satellite import goeslegacy


def latest_east_coast_wv():
    sel = goeslegacy.conus_east('WV')
    text_color = 'black'

    mapper = LargeScaleMap(projections.goes_east_nearside())
    mapper.extent = (-100, -65, 20, 60)
    mapper.initialize_drawing()

    with sel.latest() as plotter:
        colortable = ctables.wv.accuwx
        plotter.make_plot(mapper=mapper, colortable=colortable)
        plotextras.colorbar_inset(mapper.ax, colortable, color=text_color)
        title_text = 'GOES-E {} {}'.format(plotter.sattype, plotter.timestamp.strftime('%Y %b %d %H:%M UTC'))
        plotextras.bottom_right_stamp(title_text, mapper.ax, fontsize=16, color=text_color, weight='bold',
                                      path_effects=[patheffects.withStroke(linewidth=2, foreground="white")])
        mapper.draw_default()
        plt.show()

if __name__ == '__main__':
    latest_east_coast_wv()