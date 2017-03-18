from awips.dataaccess import DataAccessLayer
import cartopy.crs as ccrs
import matplotlib.pyplot as plt

import config
from weatherpy import colortables
from weatherpy.maps import mappers


class AwipsGoesPlotter(object):
    def __init__(self, sattype, grid):
        self._sattype = sattype
        self._data = grid.getRawData()
        self._lons, self._lats = grid.getLatLonCoords()
        self._extent = (self._lons.min(), self._lons.max(), self._lats.min(), self._lats.max())

    def default_map(self):
        mapper = mappers.LargeScaleMap(ccrs.PlateCarree())
        mapper.extent = self._extent
        return mapper

    def make_plot(self, mapper=None, colortable=None):
        bw = colortable is None or self._sattype == 'VIS'
        colortable_to_use = colortables.vis_depth if bw else colortable

        if mapper is None:
            mapper = self.default_map()
        mapper.initialize_drawing()
        mapper.ax.pcolormesh(self._lons, self._lats, self._data,
                             cmap=colortable_to_use.cmap, norm=colortable_to_use.norm)
        return mapper


class AwipsGoesRequest(object):
    product_map = {
        'IR': 'Imager 11 micron IR',
        'WV': 'Imager 6.7-6.5 micron IR (WV)',
        'VIS': 'Imager Visible'
    }

    def __init__(self, sattype, sector):
        self._sattype = sattype
        self._sector = sector
        self._request = self._init_data_access()

    def _init_data_access(self):
        DataAccessLayer.changeEDEXHost(config.AWIPS_EDEX_HOST)
        request = DataAccessLayer.newDataRequest()
        request.setDatatype('satellite')
        request.setLocationNames(self._sector)
        request.setParameters(AwipsGoesRequest.product_map[self._sattype])
        return request

    def __getitem__(self, item):
        times = DataAccessLayer.getAvailableTimes(self._request)
        response = DataAccessLayer.getGridData(self._request, self._convert_to_req_time(times, item))
        grid = response[0]
        return AwipsGoesPlotter(self._sattype, grid)

    def _convert_to_req_time(self, times, item):
        return [times[item]]


if __name__ == '__main__':
    plotter = AwipsGoesRequest('IR', 'Global')[-1]
    mapper = plotter.make_plot(colortable=colortables.ir_rainbow)
    mapper.draw_default()
    plt.show()
