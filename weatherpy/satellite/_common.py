from collections import namedtuple
from datetime import timedelta

import requests

from weatherpy.internal import pyhelpers
from weatherpy.thredds import DatasetAccessException


class ThreddsSatelliteSelection(object):

    def _latest_impl(self, within, action):
        right_now = pyhelpers.current_time_utc()
        datasets = self._datasets_between(right_now - within, right_now, 'desc')

        try:
            _, ds = next(datasets)
        except StopIteration:
            raise DatasetAccessException("No datasets found within {} of right now.".format(within))
        return action(ds)

    def _around_impl(self, when, within, action):
        dataset_by_deltas = {abs((ts - when).total_seconds()): ds for ts, ds in
                             self._datasets_between(when - within, when + within, 'desc')}
        if not dataset_by_deltas:
            raise DatasetAccessException("No datasets found around: {} +/- {}".format(when, within))
        smallest_delta = min(dataset_by_deltas.keys())
        return action(dataset_by_deltas[smallest_delta])

    def _between_impl(self, t1, t2, action, sort):
        if t1 >= t2:
            raise ValueError("t1 must be less than than t2")
        if sort not in ('asc', 'desc'):
            raise ValueError("Sort must be `asc` or `desc`")
        return (action(ds) for _, ds in self._datasets_between(t1, t2, sort))

    def _since_impl(self, when, action=None, sort='asc'):
        return self._between_impl(when, pyhelpers.current_time_utc(), action, sort)

    def _datasets_between(self, t1, t2, sort):
        date1 = t1.date()
        date2 = t2.date()

        if sort == 'asc':
            date_on = date1
            while date_on <= date2:
                for ts, ds in self._datasets_on(date_on, sort):
                    if t1 <= ts < t2:
                        yield ts, ds
                date_on += timedelta(days=1)
        elif sort == 'desc':
            date_on = date2
            while date_on >= date1:
                for ts, ds in self._datasets_on(date_on, sort):
                    if t1 <= ts < t2:
                        yield ts, ds
                date_on -= timedelta(days=1)
        else:
            raise ValueError("Sort must be `asc` or `desc`")

    def _datasets_on(self, query_date, sort):
        try:
            catalog = self._get_catalog(query_date)
        except requests.exceptions.HTTPError:
            # Catalog does not exist, thus datasets are empty
            return ()
        reverse = sort == 'desc'
        dataset_keys = sorted(catalog.datasets.keys(), reverse=reverse)
        return ((self._timestamp_from_dataset(ds_key), catalog.datasets[ds_key]) for ds_key in dataset_keys)

    def _get_catalog(self, query_date):
        raise NotImplementedError("Subclasses must implement _get_catalog method")

    def _timestamp_from_dataset(self, ds_key):
        raise NotImplementedError("Subclasses must implement _timestamp_from_dataset method")


satpos = namedtuple('satpos', 'latitude longitude altitude')