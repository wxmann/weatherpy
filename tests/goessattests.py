import os
import unittest
from collections import OrderedDict
from datetime import date, datetime
from unittest.mock import patch, MagicMock

from weatherpy.goessat import DataRequest, DatasetAccessException


class DataRequestTest(unittest.TestCase):

    def setUp(self):
        self.sattype = 'WV'
        self.sector = 'EAST-CONUS_4km'
        self.patcher = patch('weatherpy.goessat.TDSCatalog')
        self.mock_catalog = self.patcher.start()

        self.mock_datasets = OrderedDict()
        self.mock_datasets['EAST-CONUS_4km_WV_20160128_0530.gini'] = MagicMock()
        self.mock_datasets['EAST-CONUS_4km_WV_20160128_0630.gini'] = MagicMock()
        self.mock_datasets['EAST-CONUS_4km_WV_20160128_0715.gini'] = MagicMock()
        self.mock_datasets['EAST-CONUS_4km_WV_20160128_0745.gini'] = MagicMock()

        self.mock_catalog.return_value.datasets = self.mock_datasets
        for dataset_name, dataset in self.mock_datasets.items():
            dataset.access_urls = {
                'OPENDAP': dataset_name + '-OPENDAP'
            }

    def tearDown(self):
        self.patcher.stop()

    def test_should_initialize_catalog_to_today(self):
        req = DataRequest(self.sattype, self.sector)
        expected_url_call = 'http://thredds.ucar.edu/thredds/catalog/satellite/WV/EAST-CONUS_4km/current/catalog.xml'
        self.mock_catalog.assert_called_with(expected_url_call)
        self.assertEqual(req.request_date, datetime.utcnow().date())

    def test_should_initialize_catalog_to_specific_day(self):
        request_date = date(2017, 1, 23)
        req = DataRequest(self.sattype, self.sector, request_date)
        expected_url_call = 'http://thredds.ucar.edu/thredds/catalog/satellite/WV/EAST-CONUS_4km/20170123/catalog.xml'
        self.mock_catalog.assert_called_with(expected_url_call)
        self.assertEqual(req.request_date, request_date)

    def test_should_set_catalog_to_specific_day(self):
        request_date = date(2017, 1, 23)
        req = DataRequest(self.sattype, self.sector)
        req.request_date = request_date

        expected_url_call = 'http://thredds.ucar.edu/thredds/catalog/satellite/WV/EAST-CONUS_4km/20170123/catalog.xml'
        self.mock_catalog.assert_called_with(expected_url_call)
        self.assertEqual(req.request_date, request_date)

    def test_should_iterate_through_dataset_names(self):
        req = DataRequest(self.sattype, self.sector)
        expected_dataset_names = [ds for ds in self.mock_datasets.keys()]
        actual_dataset_names = [ds for ds in req]
        self.assertEqual(actual_dataset_names, expected_dataset_names)

    def test_should_be_able_to_test_if_timestamp_is_in_catalog(self):
        req = DataRequest(self.sattype, self.sector)
        self.assertTrue(datetime(2016, 1, 28, 6, 30) in req)
        self.assertFalse(datetime(2016, 1, 28, 6, 33) in req)

    def test_should_be_able_to_get_size_of_catalog(self):
        req = DataRequest(self.sattype, self.sector)
        self.assertEqual(len(req), len(self.mock_datasets))

    @patch('weatherpy.goessat.plotter')
    def test_should_be_able_to_get_dataset_by_timestamp(self, plotter):
        req = DataRequest(self.sattype, self.sector)
        ds = req[datetime(2016, 1, 28, 6, 30)]
        plotter.assert_called_with('EAST-CONUS_4km_WV_20160128_0630.gini-OPENDAP', self.sattype)

    @patch('weatherpy.goessat.plotter')
    def test_should_be_able_to_get_dataset_by_index(self, plotter):
        req = DataRequest(self.sattype, self.sector)
        ds_pos = req[2]
        plotter.assert_called_with('EAST-CONUS_4km_WV_20160128_0715.gini-OPENDAP', self.sattype)

        ds_neg = req[-1]
        plotter.assert_called_with('EAST-CONUS_4km_WV_20160128_0745.gini-OPENDAP', self.sattype)

    @patch('weatherpy.goessat.plotter')
    def test_should_be_able_to_get_dataset_by_dataset_name(self, plotter):
        req = DataRequest(self.sattype, self.sector)
        ds = req('EAST-CONUS_4km_WV_20160128_0630.gini')
        plotter.assert_called_with('EAST-CONUS_4km_WV_20160128_0630.gini-OPENDAP', self.sattype)

    def test_should_throw_error_if_out_of_bounds_index(self):
        with self.assertRaises(DatasetAccessException):
            DataRequest(self.sattype, self.sector)[111]

    def test_should_throw_error_if_datetime_not_in_catalog(self):
        with self.assertRaises(DatasetAccessException):
            DataRequest(self.sattype, self.sector)[datetime(2017, 9, 9, 1, 1)]

    def test_should_throw_error_if_invalid_dataset_name(self):
        with self.assertRaises(DatasetAccessException):
            DataRequest(self.sattype, self.sector)('this is an invalid dataset')


if __name__ == '__main__':
    unittest.main()