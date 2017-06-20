from collections import OrderedDict
from datetime import datetime
from unittest import TestCase
from unittest.mock import patch, MagicMock

from weatherpy.satellite.goes16 import Goes16Selection, Goes16Plotter

CHANNEL = 1
SECTOR = 'CONUS'

parent_catalog_refs = OrderedDict()
parent_catalog_refs['20170617'] = 'a'
parent_catalog_refs['20170618'] = 'b'

parent_catalog = MagicMock()
parent_catalog.catalog_refs = parent_catalog_refs


june18_datasets = OrderedDict()
for k in (
    'GOES16_20170618_003719_0.64_500m_33.3N_91.4W.nc4',
    'GOES16_20170618_004719_0.64_500m_33.3N_91.4W.nc4',
    'GOES16_20170618_011719_0.64_500m_33.3N_91.4W.nc4'
):
    june18_datasets[k] = k

june18_catalog = MagicMock()
june18_catalog.datasets = june18_datasets


def catalog_subs(url):
    if url == 'http://thredds-jumbo.unidata.ucar.edu/thredds/catalog/satellite/goes16/GOES16/catalog.xml':
        return parent_catalog
    elif url == 'http://thredds-jumbo.unidata.ucar.edu/thredds/catalog/satellite/goes16/GOES16/20170618/CONUS' \
                '/Channel01/catalog.xml':
        return june18_catalog
    else:
        raise AssertionError("TDSCatalog called with an unexpected URL: " + str(url))


class Test_Goes16Selection(TestCase):

    def setUp(self):
        self.catalog_patcher = patch('weatherpy.satellite.goes16.TDSCatalog', side_effect=catalog_subs)
        self.mock_catalog = self.catalog_patcher.start()

        self.plotter_patcher = patch('weatherpy.satellite.goes16.dap_plotter')
        self.mock_plotter_func = self.plotter_patcher.start()

    def test_should_get_latest(self):
        selector = Goes16Selection(SECTOR, CHANNEL)
        selector.latest()

        self.mock_plotter_func.assert_called_with('GOES16_20170618_011719_0.64_500m_33.3N_91.4W.nc4', Goes16Plotter)

    def test_should_get_closest_to_in_range(self):
        selector = Goes16Selection(SECTOR, CHANNEL)
        selector.closest_to(datetime(2017, 6, 18, 0, 46))

        self.mock_plotter_func.assert_called_with('GOES16_20170618_004719_0.64_500m_33.3N_91.4W.nc4', Goes16Plotter)

    def test_should_raise_closest_to_out_of_range(self):
        selector = Goes16Selection(SECTOR, CHANNEL)
        with self.assertRaises(ValueError):
            selector.closest_to(datetime(2008, 6, 18, 0, 46))

    def tearDown(self):
        self.catalog_patcher.stop()
        self.plotter_patcher.stop()
