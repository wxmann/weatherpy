import os
from datetime import datetime

from matplotlib import patheffects

from weatherpy import maps
from weatherpy import plotextras
from weatherpy.maps import projections
from weatherpy.satellite import goeslegacy
from weatherpy.thredds import timestamp_from_dataset


def save_wv(saveloc):
    sattype = 'vis'
    req = goeslegacy.GoesDataRequest(sattype, 'EAST-CONUS_1km')
    text_color = 'black'

    init_time = datetime(2017, 4, 2, 23, 15)
    end_time = datetime(2017, 4, 3, 0, 45)
    for sat in (sat for sat in req[init_time: end_time] if timestamp_from_dataset(sat).minute % 15 == 0):
        with goeslegacy.goesopen(sat) as plotter:
            with plotextras.figcontext(figsize=(16, 16)) as fig:
                mapper = maps.LargeScaleMap(projections.goes_east_nearside())
                # mapper.extent = (-105, -65, 20, 53)
                mapper.extent = (-104, -83, 24, 41)
                mapper.initialize_drawing()
                mapper.draw_default()
                plotter.make_plot(mapper=mapper)
                title_text = 'GOES-E {} {}'.format(
                    plotter.sattype, plotter.timestamp.strftime('%Y %b %d %H:%M UTC'))
                plotextras.bottom_right_stamp(title_text, mapper.ax, fontsize=16, color=text_color, weight='bold',
                                              path_effects=[patheffects.withStroke(linewidth=2, foreground="white")])
                fileloc = os.path.sep.join((saveloc,
                                            'eastus_{}_{}.png'.format(sattype, plotter.timestamp.strftime('%Y%m%d_%H%M')))
                                           )
                plotextras.save_image_no_border(fig, fileloc)

if __name__ == '__main__':
    saveloc = r'your/location/here'
    save_wv(saveloc)
