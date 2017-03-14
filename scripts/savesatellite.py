import os
from datetime import datetime

from matplotlib import patheffects

from weatherpy import colortables
from weatherpy import goessat
from weatherpy import plotextras


def save_wv(saveloc):
    colortable = colortables.wv_accuwx
    req = goessat.GoesDataRequest('WV', 'EAST-CONUS_4km')
    text_color = 'black'

    init_time = datetime(2017, 3, 14, 5, 15)
    for sat in req[init_time:]:
        with goessat.goesopen(sat) as plotter:
            with plotextras.figcontext(figsize=(12, 12)) as fig:
                mapper = plotter.default_map()
                mapper.extent = (-105, -65, 20, 53)
                mapper.draw_default()
                plotter.make_plot(mapper=mapper, colortable=colortable)
                plotextras.top_right_inset(mapper.ax, colortable, color=text_color)
                title_text = 'GOES-E {} {}\nCreated by Jim Tang (@wxmann)'.format(
                    plotter.sattype, plotter.timestamp.strftime('%Y %b %d %H:%M UTC'))
                plotextras.bottom_right_stamp(title_text, mapper.ax, fontsize=16, color=text_color, weight='bold',
                                              path_effects=[patheffects.withStroke(linewidth=2, foreground="white")])
                fileloc = os.path.sep.join((saveloc,
                                            'eastus_wv_{}.png'.format(plotter.timestamp.strftime('%Y%m%d_%H%M')))
                                           )
                plotextras.save_image_no_border(fig, fileloc)

if __name__ == '__main__':
    saveloc = r'/your/location/here'
    save_wv(saveloc)
