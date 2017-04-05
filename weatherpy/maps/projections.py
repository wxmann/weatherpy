import cartopy.crs as ccrs

# STANDARD MAPS
# TODO: create an extents module for this
# atlantic_basin = EquidistantCylindrical(llcrnlat=5.0, llcrnlon=-105.0, urcrnlat=60, urcrnlon=-5.0)
# north_america = LambertConformal(lat0=45, lon0=-100, width=11000000, height=8500000)


def platecarree(central_longitude=0.0):
    return ccrs.PlateCarree(central_longitude)


# default lat0/lon0 taken from the Cartopy LambertConformal CRS class.
def lambertconformal(lat0=39.0, lon0=-96.0, stdlat1=None, stdlat2=None, r_earth=6370997):
    globe = ccrs.Globe(ellipse='sphere', semimajor_axis=r_earth, semiminor_axis=r_earth)
    stdparas = [stdlat1] if stdlat1 is not None else None
    if stdparas is not None and stdlat2 is not None:
        stdparas.append(stdlat2)

    return ccrs.LambertConformal(central_latitude=lat0, central_longitude=lon0,
                                 standard_parallels=stdparas, globe=globe)


def goes_nearside():
    lat_0, lon_0 = 0.0, -75.0
    return ccrs.NearsidePerspective(central_latitude=lat_0, central_longitude=lon_0)