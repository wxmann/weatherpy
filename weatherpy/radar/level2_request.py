import functools
from datetime import datetime, timedelta

from siphon.radarserver import get_radarserver_datasets, RadarServer

import config
from weatherpy.internal import current_time_utc, index_time_slice_helper
from weatherpy.thredds import DatasetAccessException


def get_radar_server(host, dataset):
    full_datasets = get_radarserver_datasets(host)
    if dataset not in full_datasets:
        raise ValueError("Invalid dataset: {} for host: {}".format(dataset, host))
    url = full_datasets[dataset].follow().catalog_url
    return RadarServer(url)


class Nexrad2Request(object):
    def __init__(self, station, server=None, protocol='OPENDAP'):
        self._station = station
        self._radarserver = server or get_radar_server(config.LEVEL_2_RADAR_CATALOG.host,
                                                       config.LEVEL_2_RADAR_CATALOG.dataset)
        self._check_station(station)
        self._protocol = protocol
        self._get_datasets = functools.partial(_sorted_datasets, radarserver=self._radarserver)

    def _check_station(self, st):
        if not _valid_station(st, self._radarserver):
            raise DatasetAccessException("Invalid station: {}".format(st))

    def __getitem__(self, item):
        if isinstance(item, int):
            return self._get_from_index(item)
        elif isinstance(item, datetime):
            return self._get_from_timestamp(item)
        elif isinstance(item, slice):
            return self._get_from_slice(item)
        else:
            raise ValueError("Indexed dataset must be an integer or timestamp.")

    def _get_from_index(self, index):
        query = self._radarserver.query()
        query.stations(self._station).all_times()
        try:
            found_ds = self._get_datasets(query)[index]
            if isinstance(found_ds, list):
                return (self._open(ds) for ds in found_ds)
            return self._open(found_ds)
        except IndexError:
            raise DatasetAccessException("No dataset found for index: {}".format(index))

    def _get_from_timestamp(self, timestamp):
        query = self._radarserver.query()
        query.stations(self._station).time(timestamp)
        try:
            ds = self._get_datasets(query)[0]
            return self._open(ds)
        except IndexError:
            raise DatasetAccessException("No dataset found for timestasmp: {}".format(timestamp))

    def _get_from_slice(self, sliceobj):
        def ts_slice(sliceobj):
            start = sliceobj.start
            stop = sliceobj.stop
            step = sliceobj.step
            if stop is None:
                stop = current_time_utc()
            if start is None:
                raise ValueError("Must provide a start time for slice")

            query = self._radarserver.query()
            query.stations(self._station)
            if step is None:
                query.time_range(start, stop)
                found_ds = self._get_datasets(query)
                return (ds.access_urls[self._protocol] for ds in found_ds)
            elif isinstance(step, (timedelta, int)):
                return self._iter_for_stepped_timestamp_slice(query, start, step, stop)
            else:
                raise ValueError("Invalid type of step. Require int or timedelta")

        return index_time_slice_helper(self._get_from_index, ts_slice)(sliceobj)

    def _iter_for_stepped_timestamp_slice(self, query, start, step, stop):
        if isinstance(step, timedelta):
            timeslot = start
            # this (<=) is inconsistent with the GOES implementation (<) but consistent with the non-step
            # implementation handled via thredds.
            # meh?
            while timeslot <= stop:
                query.time(timeslot)
                try:
                    found_ds = self._get_datasets(query)[0]
                except IndexError:
                    # if no dataset for the time, exit out of the loop; we're done
                    return
                yield self._open(found_ds)
                timeslot += step
        elif isinstance(step, int):
            query.time_range(start, stop)
            for i, found_ds in enumerate(self._get_datasets(query)):
                if i % step == 0:
                    yield self._open(found_ds)

    def _open(self, ds):
        # if self._protocol != 'OPENDAP':
        #     raise ValueError("Only support OPENDAP at this time")
        return ds.access_urls[self._protocol]


def _valid_station(st, radarserver):
    return radarserver.validate_query(radarserver.query().stations(st).all_times())


def _sorted_datasets(query, radarserver):
    catalog = radarserver.get_catalog(query)
    return sorted(catalog.datasets.values(), key=lambda ds: ds.name)