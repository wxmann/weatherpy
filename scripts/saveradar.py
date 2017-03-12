import os
from datetime import timedelta, datetime

import matplotlib.pyplot as plt

from weatherpy import colortables
from weatherpy import plotutils
from weatherpy.nexrad2 import Nexrad2Request, radaropen


def save_reflectivity(savedir, station, start, end, interval_min=5):
    ctable = colortables.radarscope
    text_color = '0.85'
    for i, radar_url in enumerate(
            Nexrad2Request(station)[start: end: timedelta(minutes=interval_min)]):

        fig = plt.figure(i, figsize=(12, 12))

        with radaropen(radar_url) as radarplt:
            radarmap = radarplt.make_plot(colortable=ctable)
            radarplt.range_ring(color=text_color)
            radarmap.draw_default()
            plotutils.plot_topright_inset(radarmap.ax, ctable, color=text_color)
            title_text = '{} 0.5 deg Reflectivity, {}'.format(station,
                                                              radarplt.timestamp.strftime('%Y %b %d %H:%M UTC'))
            plotutils.bottom_right_stamp(title_text, radarmap.ax, color=text_color, size=14)

            fileloc = os.path.sep.join((savedir,
                                        '{}-refl_{}.png'.format(station, radarplt.timestamp.strftime('%Y%m%d_%H%M')))
                                       )
            plotutils.save_image_no_border(fig, fileloc)


if __name__ == '__main__':
    station = 'KPAH'
    saveloc = r'/your/location/here' + '/{}'.format(station)
    start = datetime(2017, 2, 28, 23, 0)
    end = datetime(2017, 3, 1, 0, 0)
    save_reflectivity(saveloc, station, start, end)
