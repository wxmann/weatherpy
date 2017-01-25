import cartopy.crs as ccrs
import cartopy.feature as cfeat
import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap

basemap = 'basemap'
cartopy = 'cartopy'


class MapProjection(object):
    _basemap_res = {
        'low': 'c',
        'medium': 'l',
        'high': 'h'
    }

    _cartopy_res = {
        'low': '110m',
        'medium': '50m',
        'high': '10m'
    }

    lib_unavailable_msg = "{} library unavailable: must install it or try with a different library."

    _default_drawer = basemap

    def __init__(self, drawer=None):
        self.drawer = MapProjection._default_drawer if drawer is None else drawer

    def draw_map(self, res='medium'):
        if self.drawer == basemap:
            return self._draw_basemap(res)
        elif self.drawer == cartopy:
            return self._draw_cartopy(res)
        else:
            raise NotImplementedError("Unsupported drawer: {}".format(self.drawer))

    def _draw_basemap(self, res):
        m = self._basemap_object(res)
        m.drawcoastlines()
        m.drawcountries()
        m.drawstates()
        # TODO: draw lat/lon grids
        return m

    def _basemap_object(self, res):
        raise NotImplementedError("Basemap object creation must be implemented in subclasses")

    def _draw_cartopy(self, res):
        m = self._cartopy_object(res)
        res_str = MapProjection._cartopy_res[res]
        m.coastlines(resolution=res_str, color='black', linewidth='1')
        m.add_feature(cfeat.BORDERS, linewidth='1', edgecolor='black')
        states = cfeat.NaturalEarthFeature(category='cultural', name='admin_1_states_provinces_lakes',
                                           scale=res_str, facecolor='none')
        m.add_feature(states, linewidth='0.5')
        # TODO: draw lat/lon grids
        return m

    def _cartopy_object(self, res):
        raise NotImplementedError("Cartopy object creation must be implemented in subclasses")


class EquidistantCylindrical(MapProjection):
    def __init__(self, llcrnlon, llcrnlat, urcrnlon, urcrnlat, drawer=None):
        MapProjection.__init__(self, drawer)
        self.llcrnlon = llcrnlon
        self.llcrnlat = llcrnlat
        self.urcrnlon = urcrnlon
        self.urcrnlat = urcrnlat

    def _basemap_object(self, res):
        m = Basemap(projection='cyl',
                    llcrnrlat=self.llcrnlat, llcrnrlon=self.llcrnlon,
                    urcrnrlat=self.urcrnlat, urcrnrlon=self.urcrnlon,
                    resolution=MapProjection._basemap_res[res], area_thresh=1000)
        return m

    def _cartopy_object(self, res):
        crs = ccrs.PlateCarree()
        ax = plt.axes(projection=crs)
        ax.set_extent((self.llcrnlon, self.urcrnlon, self.llcrnlat, self.urcrnlat))
        return ax


class LambertConformal(MapProjection):
    def __init__(self, lat0, lon0, width, height, stdlat1=None, stdlat2=None, r_earth=6370997, drawer=None):
        MapProjection.__init__(self, drawer)
        self.lat0 = lat0
        self.lon0 = lon0
        self.stdlat1 = stdlat1
        self.stdlat2 = stdlat2
        self.r_earth = r_earth
        self.width = width
        self.height = height

    def _basemap_object(self, res):
        return Basemap(projection='lcc', rsphere=(self.r_earth, self.r_earth),
                       lat_0=self.lat0, lon_0=self.lon0,
                       lat_1=self.stdlat1, lat_2=self.stdlat2,
                       width=self.width, height=self.height,
                       resolution=MapProjection._basemap_res[res],
                       area_thresh=1000)

    def _cartopy_object(self, res):
        globe = ccrs.Globe(ellipse='sphere', semimajor_axis=self.r_earth,
                           semiminor_axis=self.r_earth)
        stdparas = [self.stdlat1] if self.stdlat1 is not None else None
        if stdparas is not None and self.stdlat2 is not None:
            stdparas.append(self.stdlat2)
        proj = ccrs.LambertConformal(central_latitude=self.lat0, central_longitude=self.lon0,
                                     standard_parallels=stdparas, globe=globe)
        return plt.axes(projection=proj)


# STANDARD MAPS

atlantic_basin = EquidistantCylindrical(llcrnlat=5.0, llcrnlon=-105.0, urcrnlat=60, urcrnlon=-5.0)
north_america = LambertConformal(lat0=45, lon0=-100, width=11000000, height=8500000)