from datetime import date, datetime

import matplotlib.pyplot as plt
from matplotlib import patheffects

from weatherpy import colortables
from weatherpy import goessat
from weatherpy import plotutils


def latest_east_conus_ir():
    colortable = colortables.wv_accuwx
    req = goessat.DataRequest('WV', 'EAST-CONUS_4km', date(2017, 1, 20))

    with req[datetime(2017, 1, 20, 5, 45)] as plotter:
        mapper = plotter.mapper
        mapper.extent = (-112.5, -70, 17.5, 52.5)
        mapper.draw_coastlines()
        mapper.draw_borders()
        mapper.draw_states()

        plotter.make_plot(mapper=mapper, colortable=colortable)
        title_text = 'GOES {}\n{}'.format(plotter.sattype, plotter.timestamp.strftime('%Y %b %d\n%H:%M UTC'))
        plotutils.top_left_stamp(title_text, mapper,
                                 fontsize='medium',
                                 weight='bold',
                                 color='black',
                                 path_effects=[patheffects.withStroke(linewidth=3, foreground="white")])
        plt.show()


if __name__ == '__main__':
    latest_east_conus_ir()
