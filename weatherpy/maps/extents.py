from collections import namedtuple

from weatherpy.internal import calcs

geobbox = namedtuple('geobbox', 'west east south north')

conus = geobbox(-127.5, -65.5, 20.5, 52)

us_southeast = geobbox(-98, -74, 23, 40)

us_southctrl = geobbox(-110, -88, 24.5, 41)

us_southwest = geobbox(-128, -103, 28.5, 42.5)

us_northwest = geobbox(-130, -105, 39, 52)

us_northctrl = geobbox(-110, -85.5, 38, 52)

us_northeast = geobbox(-90, -65, 36, 52)

southern_plains = geobbox(-107.5, -91, 27.5, 39.5)

central_plains = geobbox(-107.5, -91, 33.5, 44)

northern_plains = geobbox(-108.5, -90, 41, 51.5)

dixie = geobbox(-97, -79, 28, 37.5)

midwest = geobbox(-98, -79, 36, 50)

gulf_of_mexico = geobbox(-100, -79, 17.5, 33)

florida = geobbox(-90, -77.5, 23, 32.5)

carolinas = geobbox(-86, -73, 31, 38)

northeast_megalopolis = geobbox(-80.5, -68, 37, 44.5)

california = geobbox(-127.5, -112, 30, 43)


def zoom(latlon, km):
    return geobbox(*calcs.bbox_from_ctr_and_range(latlon, km))