import math

from weatherpy import units


def destination_point(lon, lat, distance, bearing, R_earth=6378.1,
                      dist_unit=None, bearing_unit=None):

    if bearing_unit is None:
        bearing_unit = units.DEGREE

    if dist_unit is None:
        dist_unit = units.KILOMETER

    lat_rad = units.RADIAN.convert(lat, bearing_unit)
    lon_rad = units.RADIAN.convert(lon, bearing_unit)
    bearing_rad = units.RADIAN.convert(bearing, bearing_unit)

    if dist_unit != units.KILOMETER:
        distance = units.KILOMETER.convert(distance, dist_unit)

    lat_result_rad = math.asin(math.sin(lat_rad) * math.cos(distance / R_earth) +
                               math.cos(lat_rad) * math.sin(distance / R_earth) * math.cos(bearing_rad))
    lon_result_rad = lon_rad + math.atan2(math.sin(bearing_rad) * math.sin(distance / R_earth) * math.cos(lat_rad),
                                          math.cos(distance / R_earth) - math.sin(lat_rad) * math.sin(lat_result_rad))

    return math.degrees(lon_result_rad), math.degrees(lat_result_rad)


def bbox_from_coord(coord_mat):
    lons = coord_mat[:,0]
    lats = coord_mat[:,1]
    return min(lons), max(lons), min(lats), max(lats)


def bbox_from_ctr_and_range(ctr, dist, dist_unit=units.KILOMETER):
    if len(ctr) != 2:
        raise ValueError("Center point must be a (lat, lon) pair")
    ctr_lat, ctr_lon = ctr
    lon0, _ = destination_point(ctr_lon, ctr_lat, dist, 270, dist_unit=dist_unit)
    lon1, _ = destination_point(ctr_lon, ctr_lat, dist, 90, dist_unit=dist_unit)
    _, lat0 = destination_point(ctr_lon, ctr_lat, dist, 180, dist_unit=dist_unit)
    _, lat1 = destination_point(ctr_lon, ctr_lat, dist, 0, dist_unit=dist_unit)
    return lon0, lon1, lat0, lat1


def relative_percentage(val, minval, maxval):
    return (val - minval) / (maxval - minval)


def mask_outside_extent(extent, target_crs, x, y, coordinate_crs=None):
    target_extnt = extent.transform_to(target_crs)
    if coordinate_crs is not None:
        target_extnt = target_extnt.transform_to(coordinate_crs)

    xmask = (x <= target_extnt.east) & (x >= target_extnt.west)
    ymask = (y <= target_extnt.north) & (y >= target_extnt.south)
    return xmask, ymask