from datetime import date, datetime

import matplotlib.pyplot as plt

from weatherpy import colortables
from weatherpy import goessat
from weatherpy import mapproj
from weatherpy import plotutils


def latest_east_conus_ir():
    colortable = colortables.wv_accuwx
    req = goessat.DataRequest('WV', 'EAST-CONUS_4km', date(2017, 1, 20))

    with req[datetime(2017, 1, 20, 5, 45)] as plotter:
        mapper = mapproj.EquidistantCylindricalMapper()
        mapper.extent = (-110, -70, 20, 50)

        plotter.make_plot(mapper=mapper, colortable=colortable)
        title_text = 'GOES East {} Satellite {}'.format(plotter.sattype, plotter.timestamp.strftime('%m/%d/%Y %H:%MZ'))
        plt.title(title_text)
        plotutils.plot_legend(colortable)
        plt.show()


if __name__ == '__main__':
    latest_east_conus_ir()
