import os
from datetime import datetime

from weatherpy import ctables
from weatherpy import plotextras
from weatherpy.radar import nexradl2


def save_reflectivity(savedir, station, start, end):
    ctable = ctables.reflectivity.radarscope
    text_color = '0.85'

    radars = nexradl2.selectfor(station).between(start, end)

    for radarplt in radars:
        with plotextras.figcontext(figsize=(12, 12)) as fig:
            with radarplt:
                radarmap, _ = radarplt.make_plot(colortable=ctable)
                radarplt.range_ring(radarmap, color=text_color)
                radarmap.draw_default()
                plotextras.colorbar_inset(radarmap.ax, ctable, color=text_color)
                title_text = '{} 0.5 deg Reflectivity, {}'.format(station,
                                                                  radarplt.timestamp.strftime('%Y %b %d %H:%M UTC'))
                plotextras.bottom_right_stamp(title_text, radarmap.ax, color=text_color, size=14)

                fileloc = os.path.sep.join((savedir,
                                            '{}-refl_{}.png'.format(station, radarplt.timestamp.strftime('%Y%m%d_%H%M')))
                                           )
                plotextras.save_image_no_border(fig, fileloc)

if __name__ == '__main__':
    station = 'KHGX'
    saveloc = r'/your/location/here' + '/{}'.format(station)
    start = datetime(2017, 8, 27, 2, 50)
    end = datetime(2017, 8, 27, 3, 10)
    save_reflectivity(saveloc, station, start, end)
