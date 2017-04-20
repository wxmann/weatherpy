import math


def destination_point(lon, lat, distance, bearing, R_earth=6378.1):
    lat_rad = math.radians(lat)
    lon_rad = math.radians(lon)
    bearing_rad = math.radians(bearing)

    lat_result_rad = math.asin(math.sin(lat_rad) * math.cos(distance / R_earth) +
                               math.cos(lat_rad) * math.sin(distance / R_earth) * math.cos(bearing_rad))
    lon_result_rad = lon_rad + math.atan2(math.sin(bearing_rad) * math.sin(distance / R_earth) * math.cos(lat_rad),
                                          math.cos(distance / R_earth) - math.sin(lat_rad) * math.sin(lat_result_rad))

    return math.degrees(lon_result_rad), math.degrees(lat_result_rad)


def miles2km(mi):
    return mi * 1.60934


def bbox_from_coord(coord_mat):
    lons = coord_mat[:,0]
    lats = coord_mat[:,1]
    return min(lons), max(lons), min(lats), max(lats)


def relative_percentage(val, minval, maxval):
    return (val - minval) / (maxval - minval)