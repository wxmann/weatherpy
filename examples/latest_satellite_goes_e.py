import matplotlib.pyplot as plt
from matplotlib import patheffects

from weatherpy import colortables
from weatherpy import goessat
from weatherpy import plotextras
from weatherpy.maps import projections
from weatherpy.maps.mappers import LargeScaleMap


def latest_east_coast_wv():
    colortable = colortables.wv_accuwx
    req = goessat.GoesDataRequest('WV', 'EAST-CONUS_4km')
    text_color = 'black'

    mapper = LargeScaleMap(projections.goes_nearside())
    mapper.extent = (-100, -65, 20, 60)

    with goessat.goesopen(req[-1]) as plotter:
        plotter.make_plot(mapper=mapper, colortable=colortable)
        plotextras.top_right_inset(mapper.ax, colortable, color=text_color)
        title_text = 'GOES-E {} {}'.format(plotter.sattype, plotter.timestamp.strftime('%Y %b %d %H:%M UTC'))
        plotextras.bottom_right_stamp(title_text, mapper.ax, fontsize=16, color=text_color, weight='bold',
                                      path_effects=[patheffects.withStroke(linewidth=2, foreground="white")])
        mapper.draw_default()
        plt.show()

if __name__ == '__main__':
    latest_east_coast_wv()