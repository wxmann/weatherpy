from collections import OrderedDict
from datetime import datetime
from unittest import TestCase
from unittest.mock import MagicMock, patch, call

from siphon.catalog import Dataset
from siphon.radarserver import RadarQuery, RadarServer

from weatherpy.radar.level2_request import Nexrad2Request
from weatherpy.thredds import DatasetAccessException


def _create_dummy_dataset(name):
    mockobj = MagicMock(spec=['name', 'access_urls'])
    mockobj.name = name
    mockobj.access_urls = {protocol: '{}-{}'.format(name, protocol) for protocol in
                           ('HTTPServer', 'OPENDAP', 'CdmRemote')}
    return mockobj


ds_keys = (
    'Level2_KMUX_20170715_2333.ar2v',
    'Level2_KMUX_20170715_2349.ar2v',
    'Level2_KMUX_20170715_2336.ar2v',
    'Level2_KMUX_20170716_0003.ar2v',
    'Level2_KMUX_20170716_0013.ar2v'
)

dummy_datasets = OrderedDict({ds_key: MagicMock(name=ds_key, spec=Dataset) for ds_key in ds_keys})

dummy_catalog = MagicMock()
dummy_catalog.datasets = dummy_datasets

empty_catalog = MagicMock()
empty_catalog.datasets = OrderedDict()


class TestNexrad2Request(TestCase):
    def setUp(self):
        self.dummy_radar_server = MagicMock(spec=RadarServer)
        self.q = RadarQuery()

        self.dummy_radar_server.query.return_value = self.q
        self.selection = Nexrad2Request('KMUX', self.dummy_radar_server)
        self.action = MagicMock()
        self._consume = list

    def test_should_create_selection(self):
        sel = Nexrad2Request('KMUX', self.dummy_radar_server)
        self.assert_correct_query(spatial={'stn': ('KMUX',)}, temporal={})
        self.assertIsNotNone(sel)

    def test_should_throw_exception_given_incorrect_station(self):
        self.dummy_radar_server.validate_query.return_value = False
        with self.assertRaises(DatasetAccessException):
            Nexrad2Request('Incorrect_station', self.dummy_radar_server)

    def test_should_get_latest_radar(self):
        self.dummy_radar_server.get_catalog.return_value = dummy_catalog

        self.selection.latest(self.action)

        self.assert_correct_query(spatial={'stn': ('KMUX',)}, temporal={'temporal': 'all'})
        self.dummy_radar_server.get_catalog.assert_called_with(self.q)
        self.action.assert_called_with(dummy_datasets[ds_keys[-1]])

    def test_should_raise_if_no_latest_radar(self):
        self.dummy_radar_server.get_catalog.return_value = empty_catalog
        with self.assertRaises(DatasetAccessException):
            self.selection.latest(self.action)

        self.assert_correct_query(spatial={'stn': ('KMUX',)}, temporal={'temporal': 'all'})

    def test_should_get_radars_between(self):
        self.dummy_radar_server.get_catalog.return_value = dummy_catalog

        t1 = datetime(2017, 7, 15, 23, 30)
        t2 = datetime(2017, 7, 16, 0, 30)
        items = self.selection.between(t1, t2, action=self.action)
        self._consume(items)

        self.assert_correct_query(spatial={'stn': ('KMUX',)},
                                  temporal={'time_start': t1.isoformat(),
                                            'time_end': t2.isoformat()})
        self.dummy_radar_server.get_catalog.assert_called_with(self.q)

        sorted_ds_keys = sorted(ds_keys)
        self.action.assert_has_calls([call(dummy_datasets[ds_key]) for ds_key in sorted_ds_keys])

    def test_should_get_empty_radars_between(self):
        self.dummy_radar_server.get_catalog.return_value = empty_catalog

        t1 = datetime(2017, 7, 15, 23, 30)
        t2 = datetime(2017, 7, 16, 0, 30)
        items = self.selection.between(t1, t2, action=self.action)
        consumed = self._consume(items)

        self.assert_correct_query(spatial={'stn': ('KMUX',)},
                                  temporal={'time_start': t1.isoformat(),
                                            'time_end': t2.isoformat()})
        self.dummy_radar_server.get_catalog.assert_called_with(self.q)

        self.action.assert_not_called()
        self.assertFalse(consumed)

    def test_should_get_radars_between_desc(self):
        self.dummy_radar_server.get_catalog.return_value = dummy_catalog

        t1 = datetime(2017, 7, 15, 23, 30)
        t2 = datetime(2017, 7, 16, 0, 30)
        items = self.selection.between(t1, t2, action=self.action, sort='desc')
        self._consume(items)

        self.assert_correct_query(spatial={'stn': ('KMUX',)},
                                  temporal={'time_start': t1.isoformat(),
                                            'time_end': t2.isoformat()})
        self.dummy_radar_server.get_catalog.assert_called_with(self.q)

        sorted_ds_keys = sorted(ds_keys, reverse=True)
        self.action.assert_has_calls([call(dummy_datasets[ds_key]) for ds_key in sorted_ds_keys])

    def test_should_get_radars_since(self):
        self.dummy_radar_server.get_catalog.return_value = dummy_catalog

        t1 = datetime(2017, 7, 15, 0, 0)
        t2 = datetime(2017, 7, 16, 0, 30)

        with patch('weatherpy.radar.level2_request.pyhelpers.current_time_utc', return_value=t2):
            items = self.selection.since(t1, action=self.action)
            self._consume(items)
            self.assert_correct_query(spatial={'stn': ('KMUX',)},
                                      temporal={'time_start': t1.isoformat(),
                                                'time_end': t2.isoformat()})
            self.dummy_radar_server.get_catalog.assert_called_with(self.q)

            sorted_ds_keys = sorted(ds_keys)
            self.action.assert_has_calls([call(dummy_datasets[ds_key]) for ds_key in sorted_ds_keys])

    def test_should_get_radars_around(self):
        around_cat = MagicMock()
        ds_key = 'Level2_KMUX_20170716_0003.ar2v'
        around_ds = OrderedDict({ds_key: MagicMock(name=ds_key, spec=Dataset)})
        around_cat.datasets = around_ds
        self.dummy_radar_server.get_catalog.return_value = around_cat

        time = datetime(2017, 7, 15, 0, 0)
        self.selection.around(time, action=self.action)

        self.assert_correct_query(spatial={'stn': ('KMUX',)},
                                  temporal={'time': time.isoformat()})
        self.dummy_radar_server.get_catalog.assert_called_with(self.q)
        self.action.assert_called_with(around_ds[ds_key])

    def assert_correct_query(self, spatial, temporal):
        for k, v in self.q.spatial_query.items():
            self.assertIn(k, spatial)
            self.assertEqual(spatial[k], v)

        for k, v in self.q.time_query.items():
            self.assertIn(k, temporal)
            self.assertEqual(temporal[k], v)
