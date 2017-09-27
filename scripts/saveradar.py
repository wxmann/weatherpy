import os
from datetime import datetime

from weatherpy import ctables
from weatherpy import plotextras
from weatherpy.radar import nexradl2


def save_reflectivity(savedir, station, start, end):
    ctable = ctables.reflectivity.radarscope
    text_color = '0.85'

    # TODO: proactively set radartype in selection
    radars = nexradl2.selectfor(station).between(start, end)

    for radarplt in radars:
        with plotextras.figcontext(figsize=(12, 12)) as fig:
            with radarplt:
                try:
                    radarmap, _ = radarplt.make_plot(colortable=ctable)
                    radarmap.border_properties.strokecolor = 'white'
                    radarmap.border_properties.alpha = 0.7
                    radarmap.county_properties.strokecolor = 'white'
                    radarmap.county_properties.alpha = 0.3
                    radarplt.range_ring(radarmap, color=text_color)
                    radarmap.draw_default_detailed()
                    plotextras.colorbar_inset(radarmap.ax, ctable, color=text_color)
                    title_text = '{} 0.5 deg Reflectivity, {}'.format(station,
                                                                      radarplt.timestamp.strftime('%Y %b %d %H:%M UTC'))
                    plotextras.bottom_right_stamp(title_text, radarmap.ax, color=text_color, size=14)

                    fileloc = os.path.sep.join((savedir,
                                                '{}-refl_{}.png'.format(station, radarplt.timestamp.strftime('%Y%m%d_%H%M')))
                                               )
                    plotextras.save_image_no_border(fig, fileloc)
                except:
                    pass

if __name__ == '__main__':
    station = 'KBYX'
    saveloc = r'/Users/jitang/Dropbox/Hurricane_Irma/Radar_KeyWest'
    start = datetime(2017, 9, 10, 14, 41)
    end = datetime(2017, 9, 10, 18, 0)
    save_reflectivity(saveloc, station, start, end)
