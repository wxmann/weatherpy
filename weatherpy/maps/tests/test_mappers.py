from unittest import TestCase
from unittest.mock import patch

import cartopy.crs as ccrs
import pytest
import matplotlib.pyplot as plt

from weatherpy import maps
from weatherpy.maps.mappers import MapperBase, LargeScaleMap


class TestBaseMapper(TestCase):
    def setUp(self):
        self.crs = ccrs.PlateCarree()
        self.extent = (1, 2, 3, 4)
        self._axes_spec = ['set_extent', 'coastlines', '__call__']
        self.axes_patcher = patch('weatherpy.maps.mappers.plt.axes', spec=self._axes_spec)
        self.ax = self.axes_patcher.start()

    def tearDown(self):
        self.axes_patcher.stop()

    def test_should_set_extent_and_retrieve_it_but_not_apply_to_axes(self):
        mapper = MapperBase(self.crs)

        mapper.extent = self.extent

        self.assertEqual(mapper.extent, self.extent)

    def test_should_initialize_drawing_with_axes_but_not_set_extent(self):
        mapper = MapperBase(self.crs)

        mapper.initialize_drawing()

        self.assertIsNotNone(mapper.ax)
        self.ax.assert_called_with(projection=self.crs)
        mapper.ax.set_extent.assert_not_called()

    def test_should_set_extent_for_axes_if_drawing_initialized(self):
        mapper = MapperBase(self.crs)
        mapper.initialize_drawing()

        mapper.extent = self.extent

        self.assertEqual(mapper.extent, self.extent)
        mapper.ax.set_extent.assert_called_with(self.extent)

    def test_should_initialize_drawing_with_provided_extent(self):
        mapper = MapperBase(self.crs)
        mapper.extent = self.extent

        mapper.initialize_drawing()

        self.assertEqual(mapper.extent, self.extent)
        self.ax.assert_called_with(projection=self.crs)
        mapper.ax.set_extent.assert_called_with(self.extent)

    def test_should_throw_ex_if_extent_is_not_a_four_element_tuple(self):
        mapper = MapperBase(self.crs)
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


@pytest.mark.mpl_image_compare
def test_drawing_us_map():
    fig = plt.figure()
    crs = maps.projections.platecarree()
    mapper = maps.LargeScaleMap(crs)
    # US box
    mapper.extent = (-130, -65, 24, 51)
    mapper.draw_coastlines()
    mapper.draw_borders()
    mapper.draw_states()
    return fig


@pytest.mark.mpl_image_compare
def test_drawing_se_map_with_counties():
    crs = maps.projections.lambertconformal()
    mapper = maps.DetailedUSMap(crs)
    # SE US box
    mapper.extent = (-98, -78, 27, 37)
    mapper.draw_borders()
    mapper.draw_counties()
