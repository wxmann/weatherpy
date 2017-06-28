from unittest import TestCase

import numpy as np

from weatherpy.internal import calcs, relative_percentage


class TestCalcs(TestCase):
    def test_destination_point(self):
        lon = -73.984
        lat = 40.76
        heading = 45
        distance = 88.8561
        lon2, lat2 = calcs.destination_point(lon, lat, distance, heading)

        self.assertAlmostEqual(lat2, 41.3224612, delta=0.01)
        self.assertAlmostEqual(lon2, -73.2318226, delta=0.01)

    def test_bbox_from_coord(self):
        coord = np.asarray([[-1, -5], [2, 3], [5, 0]])
        x0, x1, y0, y1 = calcs.bbox_from_coord(coord)
        self.assertAlmostEqual(x0, -1)
        self.assertAlmostEqual(x1, 5)
        self.assertAlmostEqual(y0, -5)
        self.assertAlmostEqual(y1, 3)

    def test_bbox_from_ctr_and_range(self):
        ctr = (25.76, -80.19)  # miami, fl
        dist = 300  # km
        lon0, lon1, lat0, lat1 = calcs.bbox_from_ctr_and_range(ctr, dist)

        self.assertAlmostEqual(lon0, -83.18, delta=0.01)
        self.assertAlmostEqual(lon1, -77.20, delta=0.01)
        self.assertAlmostEqual(lat0, 23.06, delta=0.01)
        self.assertAlmostEqual(lat1, 28.46, delta=0.01)

    def test_relative_percentage(self):
        x = 50
        minval, maxval = 25, 100
        self.assertAlmostEqual(relative_percentage(x, minval, maxval), 0.333, 3)