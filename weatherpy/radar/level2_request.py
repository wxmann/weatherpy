import requests
from siphon.radarserver import get_radarserver_datasets, RadarServer

import config
from weatherpy.internal import pyhelpers
from weatherpy.radar.level2_plotting import Level2RadarPlotter
from weatherpy.thredds import DatasetAccessException, dap_plotter


def get_radar_server(host, dataset):
    full_datasets = get_radarserver_datasets(host)
    if dataset not in full_datasets:
        raise ValueError("Invalid dataset: {} for host: {}".format(dataset, host))
    url = full_datasets[dataset].follow().catalog_url
    return RadarServer(url)


class Nexrad2Request(object):
    @staticmethod
    def _default_action(ds):
        return dap_plotter(ds, Level2RadarPlotter)

    def __init__(self, station, server=None):
        self._radarserver = server or get_radar_server(config.LEVEL_2_RADAR_CATALOG.host,
                                                       config.LEVEL_2_RADAR_CATALOG.dataset)

        self._q = self._init_query(station)

    def _init_query(self, st):
        st_q = self._radarserver.query().stations(st)
        if not self._radarserver.validate_query(st_q):
            raise DatasetAccessException("Invalid station: {}".format(st))
        return st_q

    def latest(self, action=None):
        if action is None:
            action = Nexrad2Request._default_action
        query = self._q.all_times()
        all_ds = self._get_datasets(query, 'desc')
        try:
            latest_ds = next(all_ds)
        except StopIteration:
            raise DatasetAccessException("No radar datasets found")
        return action(latest_ds)

    def around(self, when, action=None):
        if action is None:
            action = Nexrad2Request._default_action
        query = self._q.time(when)
        ds = self._get_datasets(query, 'asc')

        try:
            ds_around = next(ds)
        except StopIteration:
            raise DatasetAccessException("No dataset found around {}".format(when))
        return action(ds_around)

    def between(self, t1, t2, action=None, sort='asc'):
        if sort not in ('asc', 'desc'):
            raise ValueError("Sort must be `asc` or `desc`")
        if t1 >= t2:
            raise ValueError("t1 must be less than t2")
        if action is None:
            action = Nexrad2Request._default_action
        query = self._q.time_range(t1, t2)

        return (action(ds) for ds in self._get_datasets(query, sort))

    def since(self, when, action=None, sort='asc'):
        return self.between(when, pyhelpers.current_time_utc(), action, sort)

    def _get_datasets(self, query, sort):
        try:
            catalog = self._radarserver.get_catalog(query)
        except requests.exceptions.HTTPError:
            # Catalog does not exist, thus datasets are empty
            return ()
        reverse = sort == 'desc'
        dataset_keys = sorted(catalog.datasets.keys(), reverse=reverse)
        return (catalog.datasets[ds_key] for ds_key in dataset_keys)