from weatherpy import colortables
from weatherpy import goessat

import matplotlib.pyplot as plt


def latest_east_conus_ir():
    req = goessat.DataRequest('IR', 'EAST-CONUS_4km')

    with req[-1] as plotter:
        plotter.setplot(colortable=colortables.ir_rainbow)
        plt.show()


if __name__ == '__main__':
    latest_east_conus_ir()
