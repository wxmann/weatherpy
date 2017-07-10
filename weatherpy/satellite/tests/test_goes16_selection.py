from collections import OrderedDict
from datetime import datetime, timedelta
from unittest import TestCase
from unittest.mock import patch, MagicMock, call

import requests

from weatherpy.satellite.goes16 import Goes16Selection
from weatherpy.thredds import DatasetAccessException

CHANNEL = 2
SECTOR = 'CONUS'

june21_datasets = OrderedDict()
for k in (
        'GOES16_20170621_235919_0.64_500m_33.3N_91.4W.nc4',
):
    june21_datasets[k] = k

june22_datasets = OrderedDict()
for k in (
        'GOES16_20170622_003719_0.64_500m_33.3N_91.4W.nc4',
        'GOES16_20170622_004719_0.64_500m_33.3N_91.4W.nc4',
        'GOES16_20170622_011619_0.64_500m_33.3N_91.4W.nc4',
        'GOES16_20170622_011719_0.64_500m_33.3N_91.4W.nc4'
):
    june22_datasets[k] = k

june21_catalog = MagicMock()
june21_catalog.datasets = june21_datasets

june22_catalog = MagicMock()
june22_catalog.datasets = june22_datasets


def catalog_subs(url):
    if url == 'http://thredds-jumbo.unidata.ucar.edu/thredds/catalog/satellite/goes16/GOES16/CONUS/Channel02/' \
              '20170622/catalog.xml':
        return june22_catalog
    elif url == 'http://thredds-jumbo.unidata.ucar.edu/thredds/catalog/satellite/goes16/GOES16/CONUS/Channel02/' \
                '20170621/catalog.xml':
        return june21_catalog
    else:
        raise requests.exceptions.HTTPError("Dataset is out of range: " + url)


class Test_Goes16Selection(TestCase):
    def setUp(self):
        self.catalog_patcher = patch('weatherpy.satellite.goes16.TDSCatalog', side_effect=catalog_subs)
        self.mock_catalog = self.catalog_patcher.start()

        self.current_date_patcher = patch('weatherpy.internal.pyhelpers.current_time_utc',
                                          return_value=datetime(2017, 6, 22, 1, 20))
        self.current_date_patch = self.current_date_patcher.start()

        self.action_func = MagicMock()
        self._consume_itr = list

        self.selector = Goes16Selection(SECTOR, CHANNEL)

    #### latest ####

    def test_should_get_latest_within_default_radius(self):
        self.selector.latest(action=self.action_func)

        self.action_func.assert_called_with('GOES16_20170622_011719_0.64_500m_33.3N_91.4W.nc4')

    def test_should_get_latest_within_custom_radius(self):
        self.current_date_patch.return_value = datetime(2017, 6, 22, 2, 16)
        self.selector.latest(within=timedelta(hours=1), action=self.action_func)

        self.action_func.assert_called_with('GOES16_20170622_011719_0.64_500m_33.3N_91.4W.nc4')

    def test_should_get_latest_where_latest_is_on_previous_date(self):
        self.current_date_patch.return_value = datetime(2017, 6, 22, 0, 0)
        self.selector.latest(action=self.action_func)

        self.action_func.assert_called_with('GOES16_20170621_235919_0.64_500m_33.3N_91.4W.nc4')

    def test_should_raise_if_not_datasets_within_radius(self):
        self.current_date_patch.return_value = datetime(2017, 9, 22, 0, 0)

        with self.assertRaises(DatasetAccessException):
            self.selector.latest(action=self.action_func)

    #### around ####

    def test_should_get_around_within_default_radius(self):
        self.selector.around(datetime(2017, 6, 22, 0, 46), action=self.action_func)

        self.action_func.assert_called_with('GOES16_20170622_004719_0.64_500m_33.3N_91.4W.nc4')

    def test_should_get_the_earliest_dataset_if_two_are_equally_distant(self):
        self.selector.around(datetime(2017, 6, 22, 0, 42, 19), action=self.action_func)

        self.action_func.assert_called_with('GOES16_20170622_003719_0.64_500m_33.3N_91.4W.nc4')

    def test_should_raise_ex_if_around_out_of_range(self):
        with self.assertRaises(DatasetAccessException):
            self.selector.around(datetime(2008, 6, 18, 0, 46))

    #### between ####

    def test_should_get_between_two_times_asc(self):
        self._consume_itr(self.selector.between(datetime(2017, 6, 22, 0, 0), datetime(2017, 6, 22, 1, 0),
                                                action=self.action_func))

        self.action_func.assert_has_calls([call('GOES16_20170622_003719_0.64_500m_33.3N_91.4W.nc4'),
                                           call('GOES16_20170622_004719_0.64_500m_33.3N_91.4W.nc4')])

    def test_should_get_between_two_times_desc(self):
        self._consume_itr(self.selector.between(datetime(2017, 6, 22, 0, 0), datetime(2017, 6, 22, 1, 0),
                                                action=self.action_func, sort='desc'))

        self.action_func.assert_has_calls(reversed([call('GOES16_20170622_003719_0.64_500m_33.3N_91.4W.nc4'),
                                                    call('GOES16_20170622_004719_0.64_500m_33.3N_91.4W.nc4')]))

    def test_should_get_between_two_times_on_different_dates_asc(self):
        self._consume_itr(self.selector.between(datetime(2017, 6, 20, 0, 0), datetime(2017, 6, 22, 1, 0),
                                                action=self.action_func))

        self.action_func.assert_has_calls([call('GOES16_20170621_235919_0.64_500m_33.3N_91.4W.nc4'),
                                           call('GOES16_20170622_003719_0.64_500m_33.3N_91.4W.nc4'),
                                           call('GOES16_20170622_004719_0.64_500m_33.3N_91.4W.nc4')])

    def test_should_get_between_two_times_on_different_dates_desc(self):
        self._consume_itr(self.selector.between(datetime(2017, 6, 20, 0, 0), datetime(2017, 6, 22, 1, 0),
                                                action=self.action_func, sort='desc'))

        self.action_func.assert_has_calls(reversed([call('GOES16_20170621_235919_0.64_500m_33.3N_91.4W.nc4'),
                                                    call('GOES16_20170622_003719_0.64_500m_33.3N_91.4W.nc4'),
                                                    call('GOES16_20170622_004719_0.64_500m_33.3N_91.4W.nc4')]))

    def test_should_raise_if_bounds_are_swapped(self):
        with self.assertRaises(ValueError):
            self.selector.between(datetime(2017, 7, 1, 0, 0), datetime(2017, 6, 1, 0, 0),
                                  action=self.action_func)

    def test_should_raise_if_sort_param_is_invalid(self):
        with self.assertRaises(ValueError):
            self.selector.between(datetime(2017, 6, 22, 0, 0), datetime(2017, 6, 22, 1, 0),
                                  action=self.action_func, sort='')

    #### since ####

    def test_should_get_datasets_since_asc(self):
        self.current_date_patch.return_value = datetime(2017, 6, 22, 1, 0)
        self._consume_itr(self.selector.since(datetime(2017, 6, 21, 23, 0), action=self.action_func))

        self.action_func.assert_has_calls([call('GOES16_20170621_235919_0.64_500m_33.3N_91.4W.nc4'),
                                           call('GOES16_20170622_003719_0.64_500m_33.3N_91.4W.nc4'),
                                           call('GOES16_20170622_004719_0.64_500m_33.3N_91.4W.nc4')])

    def test_should_get_datasets_since_desc(self):
        self.current_date_patch.return_value = datetime(2017, 6, 22, 1, 0)
        self._consume_itr(self.selector.since(datetime(2017, 6, 21, 23, 0), action=self.action_func,
                                              sort='desc'))

        self.action_func.assert_has_calls(reversed([call('GOES16_20170621_235919_0.64_500m_33.3N_91.4W.nc4'),
                                                    call('GOES16_20170622_003719_0.64_500m_33.3N_91.4W.nc4'),
                                                    call('GOES16_20170622_004719_0.64_500m_33.3N_91.4W.nc4')]))

    def test_should_raise_if_since_argument_is_after_current_date(self):
        self.current_date_patch.return_value = datetime(2017, 6, 22, 1, 0)
        with self.assertRaises(ValueError):
            self.selector.since(datetime(2018, 1, 1, 1, 0), action=self.action_func)

    def tearDown(self):
        self.catalog_patcher.stop()
        self.current_date_patcher.stop()
