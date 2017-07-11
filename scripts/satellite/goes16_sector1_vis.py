import os
from datetime import datetime

from matplotlib import patheffects

from weatherpy import plotextras, maps
from weatherpy.maps import extents
from weatherpy.satellite import goes16


def save_to(saveloc):
    channel = 2
    init_time = datetime(2017, 6, 12, 21, 0)
    end_time = datetime(2017, 6, 12, 21, 30)

    for plotter in goes16.conus(channel).between(init_time, end_time):
        with plotter:
            if plotter.timestamp.minute % 5 == 0:
                with plotextras.figcontext(figsize=(14, 14)) as fig:
                    mapper = maps.DetailedUSMap(plotter.default_map().crs)
                    _set_map_bdy_props(mapper)
                    plotter.make_plot(mapper, extent=extents.zoom((41.87, -103.67), 350))
                    mapper.draw_default()

                    title_text = 'GOES-16 {} {}\n** prelim, non-operational data'.format(
                        plotter.sattype, plotter.timestamp.strftime('%Y %b %d %H:%M UTC'))
                    plotextras.bottom_right_stamp(title_text, mapper.ax, fontsize=16, color='white', weight='bold',
                                                  path_effects=[patheffects.withStroke(linewidth=1.5,
                                                                                       foreground="black")])
                    fileloc = os.path.sep.join((saveloc,
                                                'CO-WY-NE_{}_{}.png'.format(plotter.sattype,
                                                                      plotter.timestamp.strftime('%Y%m%d_%H%M')))
                                               )
                    plotextras.save_image_no_border(fig, fileloc)


def _set_map_bdy_props(mapper):
    mapper.border_properties.strokecolor = 'yellow'
    mapper.border_properties.alpha = 0.15
    mapper.county_properties.strokecolor = 'yellow'
    mapper.county_properties.alpha = 0.15
    mapper.highway_properties.alpha = 0.2


if __name__ == '__main__':
    saveloc = r'/your/location/here'
    save_to(saveloc)