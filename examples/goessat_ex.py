from weatherpy import colortables
from weatherpy import goessat

import matplotlib.pyplot as plt

from weatherpy import plotutils


def latest_east_conus_ir():
    colortable = colortables.ir_rainbow
    req = goessat.DataRequest('IR', 'EAST-CONUS_4km')

    with req[-1] as plotter:
        ax = plotter.setplot(colortable=colortable)
        plt.title('GOES East IR Satellite {}'.format(plotter.timestamp.strftime('%m/%d/%Y %H:%MZ')))
        plotutils.plot_legend(colortable)
        plt.show()


if __name__ == '__main__':
    latest_east_conus_ir()
