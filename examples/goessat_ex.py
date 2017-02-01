from datetime import date, time, datetime, timedelta

import matplotlib.pyplot as plt
from matplotlib import patheffects

from weatherpy import colortables
from weatherpy import goessat
from weatherpy import mapproj
from weatherpy import plotutils


def latest_east_coast_wv():
    colortable = colortables.wv_accuwx
    req = goessat.DataRequest('WV', 'EAST-CONUS_4km')

    mapper = mapproj.lambertconformal()
    mapper.extent = (-112.5, -70, 18.5, 52.5)
    mapper.draw_coastlines()
    mapper.draw_borders()
    mapper.draw_states()

    with req[-1] as plotter:
        plotter.make_plot(mapper=mapper, colortable=colortable)
        title_text = 'GOES-E {}\n{}'.format(plotter.sattype, plotter.timestamp.strftime('%Y %b %d\n%H:%M UTC'))
        plotutils.top_left_stamp(title_text, mapper,
                                 fontsize='medium',
                                 weight='bold',
                                 color='black',
                                 path_effects=[patheffects.withStroke(linewidth=1.5, foreground="white")])
        plt.show()


def save_bunch_of_images_1():
    colortable = colortables.wv_accuwx
    req_date = date(2017, 1, 23)
    req = goessat.DataRequest('WV', 'EAST-CONUS_4km', req_date)

    t0 = datetime.combine(req_date, time(hour=0, minute=45))

    for dhour in range(0, 12):
        with req[t0 + timedelta(hours=dhour)] as plotter:
            mapper = plotter.mapper
            mapper.extent = (-112.5, -70, 18.5, 52.5)
            mapper.draw_coastlines()
            mapper.draw_borders()
            mapper.draw_states()

            plotter.make_plot(mapper=mapper, colortable=colortable)
            title_text = 'GOES-E {}\n{}'.format(plotter.sattype, plotter.timestamp.strftime('%Y %b %d\n%H:%M UTC'))
            plotutils.top_left_stamp(title_text, mapper,
                                     fontsize='small',
                                     weight='normal',
                                     color='black',
                                     path_effects=[patheffects.withStroke(linewidth=1.5, foreground="white")])

            filename = 'wveast-{}.png'.format(plotter.timestamp.strftime('%Y%d%m%H%M'))
            directory = r'your/directory/here/'
            plotutils.save_image_no_border(mapper.ax,
                                           directory + filename,
                                           dpi=175)
            plt.clf()

if __name__ == '__main__':
    latest_east_coast_wv()
