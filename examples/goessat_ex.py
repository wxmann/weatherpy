from datetime import date, time, datetime, timedelta

import matplotlib.pyplot as plt
from matplotlib import patheffects

from weatherpy import colortables
from weatherpy import goessat
from weatherpy import mapproj
from weatherpy import plotutils
from weatherpy.thredds import timestamp_from_dataset


def latest_east_coast_wv():
    colortable = colortables.wv_accuwx
    req = goessat.GoesDataRequest('WV', 'EAST-CONUS_4km')

    with req[-1] as plotter:
        mapper = plotter.default_map()
        mapper.draw_coastlines()
        mapper.draw_borders()
        mapper.draw_states()
        plotter.make_plot(mapper=mapper, colortable=colortable)
        title_text = 'GOES-E {}\n{}'.format(plotter.sattype, plotter.timestamp.strftime('%Y %b %d\n%H:%M UTC'))
        plotutils.top_left_stamp(title_text, mapper,
                                 fontsize='medium',
                                 weight='bold',
                                 color='black',
                                 path_effects=[patheffects.withStroke(linewidth=1.5, foreground="white")])
        plt.show()


# def save_batch_wv_by_dt():
#     colortable = colortables.wv_accuwx
#     req_date = date(2017, 1, 23)
#     req = goessat.GoesDataRequest('WV', 'EAST-CONUS_4km', req_date)
#
#     t0 = datetime.combine(req_date, time(hour=0, minute=45))
#
#     for dhour in range(0, 12):
#         with req[t0 + timedelta(hours=dhour)] as plotter:
#             mapper = plotter.default_map()
#             mapper.extent = (-112.5, -70, 18.5, 52.5)
#             mapper.draw_coastlines()
#             mapper.draw_borders()
#             mapper.draw_states()
#
#             plotter.make_plot(mapper=mapper, colortable=colortable)
#             title_text = 'GOES-E {}\n{}'.format(plotter.sattype, plotter.timestamp.strftime('%Y %b %d\n%H:%M UTC'))
#             plotutils.top_left_stamp(title_text, mapper,
#                                      fontsize='small',
#                                      weight='normal',
#                                      color='black',
#                                      path_effects=[patheffects.withStroke(linewidth=1.5, foreground="white")])
#
#             filename = 'wveast-{}.png'.format(plotter.timestamp.strftime('%Y%d%m%H%M'))
#             directory = r'your/directory/here/'
#             plotutils.save_image_no_border(mapper.ax,
#                                            directory + filename,
#                                            dpi=175)
#             plt.clf()
#
#
# def save_batch_ir_by_timestamp():
#     colortable = colortables.ir_rainbow
#     req_date = date(2017, 1, 21)
#     req = goessat.GoesDataRequest('IR', 'EAST-CONUS_4km', req_date)
#
#     min_time = datetime.combine(req_date, time(hour=21, minute=0))
#     max_time = datetime.combine(req_date, time(hour=23, minute=59))
#
#     for dataset_name in (dataset for dataset in req if
#                          min_time <= timestamp_from_dataset(dataset) <= max_time
#                          and timestamp_from_dataset(dataset).minute % 15 == 0):
#         with req(dataset_name) as plotter:
#             mapper = plotter.default_map()
#             mapper.extent = (-98, -78, 27, 37)
#             mapper.draw_coastlines()
#             mapper.draw_borders()
#             mapper.draw_states()
#
#             plotter.make_plot(mapper=mapper, colortable=colortable)
#             title_text = 'GOES-E {}\n{}'.format(plotter.sattype, plotter.timestamp.strftime('%Y %b %d\n%H:%M UTC'))
#             plotutils.top_left_stamp(title_text, mapper,
#                                      fontsize='small',
#                                      weight='bold',
#                                      color='black',
#                                      path_effects=[patheffects.withStroke(linewidth=1, foreground="white")])
#
#             filename = 'ir-{}.png'.format(plotter.timestamp.strftime('%Y%d%m%H%M'))
#             directory = r'your/directory/here/'
#             plotutils.save_image_no_border(mapper.ax,
#                                            directory + filename,
#                                            dpi=175)
#             plt.clf()
#
#
# def save_batch_vis():
#     req_date = date(2017, 1, 22)
#     req = goessat.GoesDataRequest('VIS', 'EAST-CONUS_1km', req_date)
#
#     min_time = datetime.combine(req_date, time(hour=19, minute=0))
#     max_time = datetime.combine(req_date, time(hour=23, minute=0))
#
#     for dataset_name in (dataset for dataset in req if
#                          min_time <= timestamp_from_dataset(dataset) < max_time
#                          and timestamp_from_dataset(dataset).minute % 15 == 0):
#         with req(dataset_name) as plotter:
#             mapper = plotter.default_map()
#             mapper.extent = (-92.5, -77.5, 25, 37.5)
#             mapper.draw_coastlines()
#             mapper.draw_borders()
#             mapper.draw_states()
#
#             plotter.make_plot(mapper=mapper)
#             title_text = 'GOES-E {}\n{}'.format(plotter.sattype, plotter.timestamp.strftime('%Y %b %d\n%H:%M UTC'))
#             plotutils.top_left_stamp(title_text, mapper,
#                                      fontsize='small',
#                                      weight='bold',
#                                      color='black',
#                                      path_effects=[patheffects.withStroke(linewidth=1, foreground="white")])
#
#             filename = 'vis-{}.png'.format(plotter.timestamp.strftime('%Y%d%m%H%M'))
#             directory = r'your/directory/here/'
#             plotutils.save_image_no_border(mapper.ax,
#                                            directory + filename,
#                                            dpi=175)
#
#             plt.clf()

if __name__ == '__main__':
    latest_east_coast_wv()
    # save_batch_vis()
