from unittest import TestCase

import numpy as np

from weatherpy.internal import calcs


class TestCalcs(TestCase):
    def test_destination_point(self):
        lon = -73.984
        lat = 40.76
        heading = 45
        distance = 88.8561
        lon2, lat2 = calcs.destination_point(lon, lat, distance, heading)

        self.assertAlmostEqual(lat2, 41.3224612, delta=0.01)
        self.assertAlmostEqual(lon2, -73.2318226, delta=0.01)

    def test_get_bbox_from_2dcoord(self):
        coord = np.asarray([[-1, -5], [2, 3], [5, 0]])
        x0, x1, y0, y1 = calcs.bbox_from_coord(coord)
        self.assertAlmostEqual(x0, -1)
        self.assertAlmostEqual(x1, 5)
        self.assertAlmostEqual(y0, -5)
        self.assertAlmostEqual(y1, 3)
