from datetime import date, datetime

from weatherpy import colortables
from weatherpy import goessat

import matplotlib.pyplot as plt

from weatherpy import plotutils


def latest_east_conus_ir():
    colortable = colortables.wv_accuwx
    req = goessat.DataRequest('WV', 'EAST-CONUS_4km', date(2017, 1, 22))

    with req[datetime(2017, 1, 22, 18, 30)] as plotter:
        ax = plotter.make_plot(colortable=colortable)
        plt.title('GOES East {} Satellite {}'.format(plotter.sattype, plotter.timestamp.strftime('%m/%d/%Y %H:%MZ')))
        plotutils.plot_legend(colortable)
        plt.show()


if __name__ == '__main__':
    latest_east_conus_ir()
