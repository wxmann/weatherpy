import math

from scipy.ndimage import minimum_filter, maximum_filter
import numpy as np


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


def extrema(mat, mode='wrap', window=10):
    """find the indices of local extrema (min and max)
    in the input array."""
    mn = minimum_filter(mat, size=window, mode=mode)
    mx = maximum_filter(mat, size=window, mode=mode)
    # (mat == mx) true if pixel is equal to the local max
    # (mat == mn) true if pixel is equal to the local in
    # Return the indices of the maxima, minima
    return np.nonzero(mat == mn), np.nonzero(mat == mx)


def pa2hPa(pa):
    return pa * 0.01
