import unittest
from collections import OrderedDict
from datetime import date, datetime, timedelta
from unittest.mock import patch, MagicMock

from weatherpy.goessat import GoesDataRequest
from weatherpy.thredds import DatasetAccessException, timestamp_from_dataset


class GoesDataRequestTest(unittest.TestCase):

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

        self.req = GoesDataRequest(self.sattype, self.sector)

    def tearDown(self):
        self.patcher.stop()

    def test_should_be_able_to_get_dataset_by_index(self):
        ds_pos = self.req[2]
        self.assertEqual(ds_pos, 'EAST-CONUS_4km_WV_20160128_0715.gini-OPENDAP')

        ds_neg = self.req[-1]
        self.assertEqual(ds_neg, 'EAST-CONUS_4km_WV_20160128_0745.gini-OPENDAP')

    def test_should_be_able_to_get_dataset_by_index_slice(self):
        ds_pos = self.req[1: 3]
        self.assertEqual(next(ds_pos), 'EAST-CONUS_4km_WV_20160128_0630.gini-OPENDAP')
        self.assertEqual(next(ds_pos), 'EAST-CONUS_4km_WV_20160128_0715.gini-OPENDAP')
        with self.assertRaises(StopIteration):
            next(ds_pos)

    def test_should_be_able_to_get_datset_by_index_slice_to_end(self):
        ds_pos = self.req[-2:]
        self.assertEqual(next(ds_pos), 'EAST-CONUS_4km_WV_20160128_0715.gini-OPENDAP')
        self.assertEqual(next(ds_pos), 'EAST-CONUS_4km_WV_20160128_0745.gini-OPENDAP')
        with self.assertRaises(StopIteration):
            next(ds_pos)

    def test_should_be_able_to_get_dataset_by_full_slice(self):
        ds_pos = self.req[:]
        self.assertEqual(next(ds_pos), 'EAST-CONUS_4km_WV_20160128_0530.gini-OPENDAP')
        self.assertEqual(next(ds_pos), 'EAST-CONUS_4km_WV_20160128_0630.gini-OPENDAP')
        self.assertEqual(next(ds_pos), 'EAST-CONUS_4km_WV_20160128_0715.gini-OPENDAP')
        self.assertEqual(next(ds_pos), 'EAST-CONUS_4km_WV_20160128_0745.gini-OPENDAP')
        with self.assertRaises(StopIteration):
            next(ds_pos)

    def test_should_raise_error_if_index_out_of_bounds(self):
        with self.assertRaises(DatasetAccessException):
            self.req[-100]

    def test_should_be_able_to_get_dataset_by_timestamp(self):
        ds = self.req[datetime(2016, 1, 28, 6, 30)]
        self.assertEqual(ds, 'EAST-CONUS_4km_WV_20160128_0630.gini-OPENDAP')

    def test_should_be_able_to_get_dataset_by_timestamp_slice(self):
        init_time = datetime(2016, 1, 28, 6, 30)
        ds = self.req[init_time: init_time + timedelta(hours=1)]
        self.assertEqual(next(ds), 'EAST-CONUS_4km_WV_20160128_0630.gini-OPENDAP')
        self.assertEqual(next(ds), 'EAST-CONUS_4km_WV_20160128_0715.gini-OPENDAP')
        with self.assertRaises(StopIteration):
            next(ds)

    @patch('weatherpy.goessat.current_time_utc', return_value=datetime(2016, 1, 28, 23, 59))
    def test_should_be_able_to_get_dataset_by_timestamp_slice_to_end(self, current_time_patch):
        init_time = datetime(2016, 1, 28, 6, 30)
        ds = self.req[init_time:]
        self.assertEqual(next(ds), 'EAST-CONUS_4km_WV_20160128_0630.gini-OPENDAP')
        self.assertEqual(next(ds), 'EAST-CONUS_4km_WV_20160128_0715.gini-OPENDAP')
        self.assertEqual(next(ds), 'EAST-CONUS_4km_WV_20160128_0745.gini-OPENDAP')
        with self.assertRaises(StopIteration):
            next(ds)
            
    def test_should_raise_exception_if_timestamp_slice_from_start(self):
        with self.assertRaises(DatasetAccessException):
            self.req[: datetime(2016, 1, 31, 0, 0)]

    def test_should_raise_exception_if_not_use_int_or_timestamp_to_get_dataset(self):
        with self.assertRaises(DatasetAccessException):
            self.req[1.5]

    def test_should_raise_exception_if_mix_int_and_timestamp_to_get_dataset(self):
        with self.assertRaises(ValueError):
            self.req[5: datetime(2017, 1, 31, 0, 0)]

    def test_should_get_timestamp_from_dataset_name(self):
        ds_name = 'EAST-CONUS_4km_IR_20170201_0645.gini'
        ts = timestamp_from_dataset(ds_name)
        self.assertEqual(ts, datetime(2017, 2, 1, 6, 45))

if __name__ == '__main__':
    unittest.main()