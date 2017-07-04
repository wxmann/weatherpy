from collections import OrderedDict
from datetime import datetime, timedelta
from unittest import TestCase
from unittest.mock import patch, MagicMock, call

import requests

from weatherpy.satellite.goeslegacy import GoesLegacySelection
from weatherpy.thredds import DatasetAccessException


mock_catalog = MagicMock()
mock_catalog.datasets = OrderedDict()
for k in ('EAST-CONUS_4km_WV_20160128_0530.gini', 'EAST-CONUS_4km_WV_20160128_0630.gini',
          'EAST-CONUS_4km_WV_20160128_0715.gini', 'EAST-CONUS_4km_WV_20160128_0745.gini'):
    mock_catalog.datasets[k] = k


def catalog_subs(url):
    if url == 'http://thredds.ucar.edu/thredds/catalog/satellite/WV/EAST-CONUS_4km/20160128/catalog.xml':
        return mock_catalog
    else:
        raise requests.exceptions.HTTPError("Dataset is out of range: " + url)


class TestGoesLegacySelection(TestCase):

    def setUp(self):
        self.sattype = 'WV'
        self.sector = 'EAST-CONUS_4km'
        self.catalog_patcher = patch('weatherpy.satellite.goeslegacy.TDSCatalog', side_effect=catalog_subs)
        self.current_date_patcher = patch('weatherpy.internal.pyhelpers.current_time_utc')
        self.mock_catalog = self.catalog_patcher.start()
        self.current_date = self.current_date_patcher.start()

        self.sel = GoesLegacySelection(self.sattype, self.sector)
        self.action = MagicMock()
        self._consumer = list

    def tearDown(self):
        self.catalog_patcher.stop()
        self.current_date_patcher.stop()

    def test_should_be_able_to_get_latest_dataset_default_radius(self):
        self.current_date.return_value = datetime(2016, 1, 28, 7, 50)
        self.sel.latest(action=self.action)

        self.action.assert_called_with('EAST-CONUS_4km_WV_20160128_0745.gini')

    def test_fail_to_find_latest_dataset_within_custom_radius(self):
        with self.assertRaises(DatasetAccessException):
            self.current_date.return_value = datetime(2016, 1, 28, 7, 50)
            self.sel.latest(within=timedelta(minutes=1), action=self.action)

    def test_find_dataset_around_time_default_radius(self):
        self.sel.around(datetime(2016, 1, 28, 6, 45), action=self.action)

        self.action.assert_called_with('EAST-CONUS_4km_WV_20160128_0630.gini')

    def test_find_dataset_around_time_custom_radius(self):
        self.sel.around(datetime(2016, 1, 28, 4, 35), within=timedelta(hours=1), action=self.action)

        self.action.assert_called_with('EAST-CONUS_4km_WV_20160128_0530.gini')

    def test_find_datasets_between_and_exclude_higher_bound(self):
        ds_iter = self.sel.between(datetime(2016, 1, 27, 23, 0),
                                   datetime(2016, 1, 28, 7, 15), action=self.action)

        self._consumer(ds_iter)
        self.action.assert_has_calls([
            call('EAST-CONUS_4km_WV_20160128_0530.gini'),
            call('EAST-CONUS_4km_WV_20160128_0630.gini')
        ])

    def test_find_datasets_between_and_include_lower_bound(self):
        ds_iter = self.sel.between(datetime(2016, 1, 28, 7, 15),
                                   datetime(2016, 1, 30, 7, 15), action=self.action)

        self._consumer(ds_iter)
        self.action.assert_has_calls([
            call('EAST-CONUS_4km_WV_20160128_0715.gini'),
            call('EAST-CONUS_4km_WV_20160128_0745.gini')
        ])

    def test_find_datasets_since(self):
        self.current_date.return_value = datetime(2016, 1, 28, 7, 50)

        ds_iter = self.sel.since(datetime(2016, 1, 28, 7, 0), action=self.action)
        self._consumer(ds_iter)

        self.action.assert_has_calls([
            call('EAST-CONUS_4km_WV_20160128_0715.gini'),
            call('EAST-CONUS_4km_WV_20160128_0745.gini')
        ])
