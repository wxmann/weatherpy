from unittest import TestCase

import cartopy.crs as ccrs
import numpy as np

from weatherpy.maps.extents import geobbox


class Test_Geobbox(TestCase):
    def setUp(self):
        self.extent = geobbox(-100, -90, 20, 40)

    def test_get_geobbox_as_tuple(self):
        self.assertEqual(self.extent.as_tuple(), (-100, -90, 20, 40))

    def test_get_west_east_south_north(self):
        self.assertEqual(self.extent.west, -100)
        self.assertEqual(self.extent.east, -90)
        self.assertEqual(self.extent.south, 20)
        self.assertEqual(self.extent.north, 40)

    def test_get_indices_west_east_south_north(self):
        self.assertEqual(self.extent[0], -100)
        self.assertEqual(self.extent[1], -90)
        self.assertEqual(self.extent[2], 20)
        self.assertEqual(self.extent[3], 40)

        with self.assertRaises(IndexError):
            self.extent[4]

    def test_geobbox_eq(self):
        self.assertEqual(self.extent, geobbox(-100, -90, 20, 40))
        self.assertNotEqual(self.extent, geobbox(-100, -89.9, 20, 40))
        self.assertNotEqual(self.extent, (-100, -90, 20, 40))
        self.assertNotEqual(self.extent, geobbox(-100, -90, 20, 40, 'another_crs'))

    def test_get_top_border(self):
        top = self.extent.top_border(numpts=5)
        np.testing.assert_array_equal(top, np.array([[-100, 40],
                                                     [-97.5, 40],
                                                     [-95, 40],
                                                     [-92.5, 40],
                                                     [-90, 40]]))

    def test_get_bottom_border(self):
        bottom = self.extent.bottom_border(numpts=5)
        np.testing.assert_array_equal(bottom, np.array([[-100, 20],
                                                        [-97.5, 20],
                                                        [-95, 20],
                                                        [-92.5, 20],
                                                        [-90, 20]]))

    def test_get_left_border(self):
        top = self.extent.left_border(numpts=3)
        np.testing.assert_array_equal(top, np.array([[-100, 20],
                                                     [-100, 30],
                                                     [-100, 40]]))

    def test_get_right_border(self):
        top = self.extent.right_border(numpts=3)
        np.testing.assert_array_equal(top, np.array([[-90, 20],
                                                     [-90, 30],
                                                     [-90, 40]]))

    def test_transform_to_crs(self):
        transformed = self.extent.transform_to(ccrs.LambertConformal())

        np.testing.assert_allclose(np.array(transformed.as_tuple()),
                                   np.array([-438316.88046, 657209.93258, -2132001.958898, 127241.242301]))

        self.assertEqual(transformed._crs, ccrs.LambertConformal())
