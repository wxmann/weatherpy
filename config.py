import os
from collections import namedtuple

ROOT_PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))

RESOURCES_DIR = os.sep.join([ROOT_PROJECT_DIR, 'resources'])

PALETTES_DIR = os.sep.join([RESOURCES_DIR, 'colortable-palettes'])

SHAPEFILE_DIR = os.sep.join([RESOURCES_DIR, 'shapefiles'])

radarcatalog = namedtuple('radarcatalog', 'host dataset')

LEVEL_2_RADAR_CATALOG = radarcatalog('http://thredds.ucar.edu/thredds/', 'NEXRAD Level II Radar from IDD')

TEST_DATA_DIR = os.sep.join([RESOURCES_DIR, 'fortests'])

# LEVEL_2_RADAR_CATALOG_BACKUP = radarcatalog('http://tds.meteo.psu.edu:8080/thredds/idd/radars.xml',
#                                             'NEXRAD Level II Radar WSR-88D')

NOMADS_OPENDAP = 'http://nomads.ncep.noaa.gov:9090/dods'
