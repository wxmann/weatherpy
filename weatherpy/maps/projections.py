import warnings

import cartopy.crs as ccrs


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


def goes_east_nearside():
    lat_0, lon_0 = 0.0, -75.0
    return ccrs.NearsidePerspective(central_latitude=lat_0, central_longitude=lon_0)


def goes_west_nearside():
    lat_0, lon_0 = 0.0, -135.0
    return ccrs.NearsidePerspective(central_latitude=lat_0, central_longitude=lon_0)


def from_cf_var(cf_var):
    grid_mapping = cf_var.grid_mapping_name

    if grid_mapping == 'lambert_conformal_conic':
        lat0 = cf_var.latitude_of_projection_origin
        lon0 = cf_var.longitude_of_central_meridian

        std_parallels = cf_var.standard_parallel
        if hasattr(std_parallels, '__iter__'):
            std_parallels = list(std_parallels)
        else:
            std_parallels = [std_parallels]

        globe = get_globe(cf_var)

        if all([
            'false_northing' in cf_var.ncattrs(),
            'false_easting' in cf_var.ncattrs()
        ]):
            false_easting = cf_var.false_easting
            false_northing = cf_var.false_northing
            return ccrs.LambertConformal(central_latitude=lat0,
                                         central_longitude=lon0,
                                         globe=globe,
                                         standard_parallels=std_parallels,
                                         false_easting=false_easting,
                                         false_northing=false_northing)
        else:
            return ccrs.LambertConformal(central_latitude=lat0,
                                         central_longitude=lon0,
                                         globe=globe,
                                         standard_parallels=std_parallels)

    else:
        raise ValueError("Other projections besides Lambert Conformal not supported")


def get_globe(cf_var):
    attrs = cf_var.ncattrs()

    if 'earth_radius' in attrs:
        r_earth = cf_var.earth_radius
        return ccrs.Globe(ellipse='sphere', semimajor_axis=r_earth, semiminor_axis=r_earth)
    elif 'semi_major_axis' in attrs:
        a = cf_var.semi_major_axis
        if 'inverse_flattening' in attrs:
            f = cf_var.inverse_flattening
            b = a * (1 - f)
        elif 'semi_minor_axis' in attrs:
            b = cf_var.semi_minor_axis
        else:
            warnings.warn('CF variable does not supply a minor axis length, defaulting to sphere.')
            b = a
        return ccrs.Globe(semimajor_axis=a, semiminor_axis=b)
    else:
        # This will be handled as a default globe in Cartopy.
        return None

