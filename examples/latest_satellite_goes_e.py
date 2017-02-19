import matplotlib.pyplot as plt
from matplotlib import patheffects

from weatherpy import colortables
from weatherpy import goessat
from weatherpy import plotutils


def latest_east_coast_wv():
    colortable = colortables.wv_accuwx
    req = goessat.GoesDataRequest('WV', 'EAST-CONUS_4km')

    with req[-1] as plotter:
        mapper = plotter.default_map()
        mapper.draw_default()
        plotter.make_plot(mapper=mapper, colortable=colortable)
        title_text = 'GOES-E {}\n{}'.format(plotter.sattype, plotter.timestamp.strftime('%Y %b %d\n%H:%M UTC'))
        plotutils.top_left_stamp(title_text, mapper,
                                 fontsize='medium',
                                 weight='bold',
                                 color='black',
                                 path_effects=[patheffects.withStroke(linewidth=1.5, foreground="white")])
        plt.show()

if __name__ == '__main__':
    latest_east_coast_wv()