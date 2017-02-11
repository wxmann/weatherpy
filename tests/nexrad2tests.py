from datetime import datetime, timedelta
from unittest import TestCase
from unittest.mock import patch, MagicMock

from siphon.radarserver import RadarServer, RadarQuery

from weatherpy.nexrad2 import Nexrad2Request
from weatherpy.thredds import DatasetAccessException


def _create_dummy_dataset(name):
    mockobj = MagicMock(spec=['name', 'access_urls'])
    mockobj.name = name
    mockobj.access_urls = {protocol: '{}-{}'.format(name, protocol) for protocol in
                           ('HTTPServer', 'OPENDAP', 'CdmRemote')}
    return mockobj


class TestNexrad2Request(TestCase):
    def setUp(self):
        self.radar_server_patch = patch('weatherpy.nexrad2.RadarServer', autospec=True)
        self.dummy_radar_server = self.radar_server_patch.start()
        self.dummy_radar_server.query = MagicMock(spec=RadarQuery)

        self.radar_request_patch = patch('weatherpy.nexrad2._get_radar_server', return_value=self.dummy_radar_server)
        self.radar_request_patch.start()

        self.check_station_patch = patch('weatherpy.nexrad2._valid_station', return_value=True)
        self.check_station_patch.start()

    def tearDown(self):
        self.radar_request_patch.stop()
        self.check_station_patch.stop()
        self.radar_server_patch.stop()

    def test_should_initialize_catalog(self):
        req = Nexrad2Request('KMUX')
        self.assertIsNotNone(req)

    @patch('weatherpy.nexrad2._valid_station', return_value=False)
    def test_should_throw_exception_given_incorrect_station(self, validst):
        with self.assertRaises(DatasetAccessException):
            Nexrad2Request('Incorrect_station')

    @patch('weatherpy.nexrad2._sorted_datasets')
    def test_should_query_radar_by_index(self, ds_returned):
        dummy_datasets = [_create_dummy_dataset(str(name)) for name in range(3)]
        ds_returned.return_value = dummy_datasets

        req = Nexrad2Request('KMUX')
        found = req[-1]
        self.assertEqual(found, '2-OPENDAP')

    @patch('weatherpy.nexrad2._sorted_datasets')
    def test_should_query_radar_by_index_slice(self, ds_returned):
        dummy_datasets = [_create_dummy_dataset(str(name)) for name in range(3)]
        ds_returned.return_value = dummy_datasets

        req = Nexrad2Request('KMUX')
        found = req[1:3]
        self.assertEqual(found, ['1-OPENDAP', '2-OPENDAP'])

    @patch('weatherpy.nexrad2._sorted_datasets')
    def test_should_query_radar_by_index_slice_to_end(self, ds_returned):
        dummy_datasets = [_create_dummy_dataset(str(name)) for name in range(3)]
        ds_returned.return_value = dummy_datasets

        req = Nexrad2Request('KMUX')
        found = req[-2:]
        self.assertEqual(found, ['1-OPENDAP', '2-OPENDAP'])

    @patch('weatherpy.nexrad2._sorted_datasets')
    def test_should_query_radar_by_all_index_slice(self, ds_returned):
        dummy_datasets = [_create_dummy_dataset(str(name)) for name in range(3)]
        ds_returned.return_value = dummy_datasets

        req = Nexrad2Request('KMUX')
        found = req[:]
        self.assertEqual(found, ['0-OPENDAP', '1-OPENDAP', '2-OPENDAP'])

    @patch('weatherpy.nexrad2._sorted_datasets')
    def test_should_query_radar_by_timestamp(self, ds_returned):
        dummy_dataset = [_create_dummy_dataset('dataset')]
        ds_returned.return_value = dummy_dataset

        req = Nexrad2Request('KMUX')
        timestamp = datetime(2017, 2, 10, 0, 0)
        found = req[timestamp]

        self.dummy_radar_server.query.assert_called_once_with()
        station_query = self.dummy_radar_server.query.return_value.stations
        time_query = station_query.return_value.time
        station_query.assert_called_with('KMUX')
        time_query.assert_called_with(timestamp)
        self.assertEqual(found, 'dataset-OPENDAP')

    @patch('weatherpy.nexrad2._sorted_datasets')
    def test_should_query_radar_by_timestamp_range(self, ds_returned):
        dummy_datasets = [_create_dummy_dataset(str(name)) for name in range(3)]
        ds_returned.return_value = dummy_datasets

        req = Nexrad2Request('KMUX')
        early_time = datetime(2017, 2, 10, 0, 0)
        later_time = datetime(2017, 2, 10, 1, 0)
        found = req[early_time: later_time]

        self.dummy_radar_server.query.assert_called_once_with()
        station_query = self.dummy_radar_server.query.return_value.stations
        time_query = station_query.return_value.time_range
        station_query.assert_called_with('KMUX')
        time_query.assert_called_with(early_time, later_time)
        self.assertEqual(found, ['0-OPENDAP', '1-OPENDAP', '2-OPENDAP'])

    @patch('weatherpy.nexrad2.current_time_utc')
    @patch('weatherpy.nexrad2._sorted_datasets')
    def test_should_query_radar_by_timestamp_range_with_no_ending_date(self, ds_returned, time_func):
        dummy_datasets = [_create_dummy_dataset(str(name)) for name in range(3)]
        ds_returned.return_value = dummy_datasets
        time_func.return_value = datetime(2017, 2, 11, 0, 0)

        req = Nexrad2Request('KMUX')
        early_time = datetime(2017, 2, 10, 0, 0)
        found = req[early_time:]

        self.dummy_radar_server.query.assert_called_once_with()
        station_query = self.dummy_radar_server.query.return_value.stations
        time_query = station_query.return_value.time_range
        station_query.assert_called_with('KMUX')
        time_query.assert_called_with(early_time, time_func.return_value)
        self.assertEqual(found, ['0-OPENDAP', '1-OPENDAP', '2-OPENDAP'])

    @patch('weatherpy.nexrad2.current_time_utc')
    @patch('weatherpy.nexrad2._sorted_datasets')
    def test_should_query_radar_by_timestamp_range_with_no_start_date(self, ds_returned, time_func):
        dummy_datasets = [_create_dummy_dataset(str(name)) for name in range(3)]
        ds_returned.return_value = dummy_datasets
        time_func.return_value = datetime(2017, 2, 11, 0, 0)

        req = Nexrad2Request('KMUX')
        endtime = datetime(2017, 2, 12, 0, 0)
        found = req[:endtime]

        self.dummy_radar_server.query.assert_called_once_with()
        station_query = self.dummy_radar_server.query.return_value.stations
        time_query = station_query.return_value.time_range
        station_query.assert_called_with('KMUX')
        time_query.assert_called_with(time_func.return_value - timedelta(days=90), endtime)
        self.assertEqual(found, ['0-OPENDAP', '1-OPENDAP', '2-OPENDAP'])
