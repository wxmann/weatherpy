import unittest
from unittest.mock import patch

import cartopy.crs as ccrs

from weatherpy.maps.drawers import BaseCartopyDrawer, LargeScaleMap


class CartopyDrawerTest(unittest.TestCase):
    def setUp(self):
        self.crs = ccrs.PlateCarree()
        self.extent = (1, 2, 3, 4)
        self._axes_spec = ['set_extent', 'coastlines', '__call__']
        self.axes_patcher = patch('weatherpy.maps.drawers.plt.axes', spec=self._axes_spec)
        self.ax = self.axes_patcher.start()

    def tearDown(self):
        self.axes_patcher.stop()

    def test_should_set_extent_and_retrieve_it_but_not_apply_to_axes(self):
        mapper = BaseCartopyDrawer(self.crs)

        mapper.extent = self.extent

        self.assertEqual(mapper.extent, self.extent)

    def test_should_initialize_drawing_with_axes_but_not_set_extent(self):
        mapper = BaseCartopyDrawer(self.crs)

        mapper.initialize_drawing()

        self.assertIsNotNone(mapper.ax)
        self.ax.assert_called_with(projection=self.crs)
        mapper.ax.set_extent.assert_not_called()

    def test_should_set_extent_for_axes_if_drawing_initialized(self):
        mapper = BaseCartopyDrawer(self.crs)
        mapper.initialize_drawing()

        mapper.extent = self.extent

        self.assertEqual(mapper.extent, self.extent)
        mapper.ax.set_extent.assert_called_with(self.extent)

    def test_should_initialize_drawing_with_provided_extent(self):
        mapper = BaseCartopyDrawer(self.crs)
        mapper.extent = self.extent

        mapper.initialize_drawing()

        self.assertEqual(mapper.extent, self.extent)
        self.ax.assert_called_with(projection=self.crs)
        mapper.ax.set_extent.assert_called_with(self.extent)

    def test_should_throw_ex_if_extent_is_not_a_four_element_tuple(self):
        mapper = BaseCartopyDrawer(self.crs)
        with self.assertRaises(ValueError):
            mapper.extent = (1, 2)
        with self.assertRaises(ValueError):
            mapper.extent = None

    def test_should_set_line_property(self):
        mapper = LargeScaleMap(self.crs)
        mapper.properties.strokecolor = 'red'
        mapper.draw_coastlines()

        func_name, args, kwargs = mapper.ax.coastlines.mock_calls[0]
        self.assertEqual(kwargs['color'], 'red')
