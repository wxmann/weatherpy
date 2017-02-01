import unittest
import warnings
from unittest.mock import patch

import cartopy.crs as ccrs

from weatherpy.mapproj import CartopyMapper


class CartopyMapperTest(unittest.TestCase):
    def setUp(self):
        self.crs = ccrs.PlateCarree()
        self.extent = (1, 2, 3, 4)
        self._axes_spec = ['set_extent', 'coastlines', '__call__']
        self.axes_patcher = patch('weatherpy.mapproj.plt.axes', spec=self._axes_spec)
        self.ax = self.axes_patcher.start()

    def tearDown(self):
        self.axes_patcher.stop()

    def test_should_set_extent_and_retrieve_it_but_not_apply_to_axes(self):
        mapper = CartopyMapper(self.crs)

        mapper.extent = self.extent

        self.assertEqual(mapper.extent, self.extent)
        self.assertIsNone(mapper.ax)

    def test_should_initialize_drawing_with_axes_but_not_set_extent(self):
        mapper = CartopyMapper(self.crs)

        mapper.initialize_drawing()

        self.assertIsNotNone(mapper.ax)
        self.ax.assert_called_with(projection=self.crs)
        mapper.ax.set_extent.assert_not_called()

    def test_should_set_extent_for_axes_if_drawing_initialized(self):
        mapper = CartopyMapper(self.crs)
        mapper.initialize_drawing()

        mapper.extent = self.extent

        self.assertEqual(mapper.extent, self.extent)
        mapper.ax.set_extent.assert_called_with(self.extent)

    def test_should_initialize_drawing_with_provided_extent(self):
        mapper = CartopyMapper(self.crs)
        mapper.extent = self.extent

        mapper.initialize_drawing()

        self.assertEqual(mapper.extent, self.extent)
        self.ax.assert_called_with(projection=self.crs)
        mapper.ax.set_extent.assert_called_with(self.extent)

    def test_should_throw_ex_if_extent_is_not_a_four_element_tuple(self):
        mapper = CartopyMapper(self.crs)
        with self.assertRaises(ValueError):
            mapper.extent = (1, 2)
        with self.assertRaises(ValueError):
            mapper.extent = None

    def test_should_set_line_property(self):
        mapper = CartopyMapper(self.crs)
        mapper.set_line_property('color', 'red')
        self.assertDictEqual(mapper.line_properties, {
            'color': 'red',
            'width': CartopyMapper.DEFAULT_LINE_WIDTH,
            'resolution': CartopyMapper.DEFAULT_RESOLUTION
        })

    @patch('weatherpy.mapproj.warnings', spec=warnings)
    def test_should_not_set_incorrect_line_property(self, warnings_module):
        mapper = CartopyMapper(self.crs)
        mapper.set_line_property('colour', 'red')
        self.assertDictEqual(mapper.line_properties, {
            'color': CartopyMapper.DEFAULT_LINE_COLOR,
            'width': CartopyMapper.DEFAULT_LINE_WIDTH,
            'resolution': CartopyMapper.DEFAULT_RESOLUTION
        })
        warnings_module.warn.assert_called_with("There is no line property: colour. Nothing has been set.")

    # The following test calling the args list correctly (same between coastlines/borders/states).
    # There are additional test that actually test the images in the e2e file.

    def test_should_call_draw_coastlines_with_default_args(self):
        mapper = CartopyMapper(self.crs)

        mapper.draw_coastlines()

        mapper.ax.coastlines.assert_called_with(resolution=CartopyMapper.DEFAULT_RESOLUTION,
                                                color=CartopyMapper.DEFAULT_LINE_COLOR,
                                                linewidth=CartopyMapper.DEFAULT_LINE_WIDTH)

    def test_should_call_draw_coastlines_with_specific_args(self):
        mapper = CartopyMapper(self.crs)

        mapper.draw_coastlines(color='red', something_else='1')

        mapper.ax.coastlines.assert_called_with(resolution=CartopyMapper.DEFAULT_RESOLUTION,
                                                color='red',
                                                linewidth=CartopyMapper.DEFAULT_LINE_WIDTH,
                                                something_else='1')
