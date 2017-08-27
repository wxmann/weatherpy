import os

import netCDF4
import pytest
import matplotlib.pyplot as plt

import config
from weatherpy import maps
from weatherpy.radar.nexradl2 import Nexrad2Plotter

RADAR_FILE = 'Level2_KGLD_20170713_0200.nc'

radar_dataset = None


@pytest.fixture(scope='module', autouse=True)
def lazyloaddataset():
    print('loading...')
    global radar_dataset
    radar_dataset = netCDF4.Dataset(os.sep.join([config.TEST_DATA_DIR, RADAR_FILE]))
    yield
    print('closing...')
    radar_dataset.close()


@pytest.mark.mpl_image_compare(tolerance=20)
def test_plot_reflectivity():
    fig = plt.figure()
    _run_basic_test_with('Reflectivity')
    return fig


@pytest.mark.mpl_image_compare(tolerance=20)
def test_plot_velocity():
    fig = plt.figure()
    _run_basic_test_with('RadialVelocity')
    return fig


@pytest.mark.mpl_image_compare(tolerance=20)
def test_plot_differential_reflectivity():
    fig = plt.figure()
    _run_basic_test_with('DifferentialReflectivity')
    return fig


@pytest.mark.mpl_image_compare(tolerance=20)
def test_plot_correlation_coefficient():
    fig = plt.figure()
    _run_basic_test_with('CorrelationCoefficient')
    return fig


@pytest.mark.mpl_image_compare(tolerance=20)
def test_plot_reflectivity_with_limiting_range_ring():
    fig = plt.figure()
    plotter = Nexrad2Plotter(radar_dataset)
    orig_map = plotter.default_map()
    map_to_use = maps.LargeScaleMap(orig_map.crs)
    map_to_use.extent = orig_map.extent

    mapper, _ = plotter.make_plot(mapper=map_to_use)
    mapper.draw_default()
    plotter.range_ring(mapper)
    return fig


@pytest.mark.mpl_image_compare(tolerance=20)
def test_plot_reflectivity_with_nonlimiting_range_ring():
    fig = plt.figure()
    plotter = Nexrad2Plotter(radar_dataset)
    orig_map = plotter.default_map()
    map_to_use = maps.LargeScaleMap(orig_map.crs)
    map_to_use.extent = orig_map.extent

    mapper, _ = plotter.make_plot(mapper=map_to_use)
    mapper.draw_default()
    plotter.range_ring(mapper, limit=False, fit_to_ring=False)
    return fig


def _run_basic_test_with(radartype=None, hires=True, sweep=0):
    plotter = Nexrad2Plotter(radar_dataset)
    orig_map = plotter.default_map()
    map_to_use = maps.LargeScaleMap(orig_map.crs)
    map_to_use.extent = orig_map.extent

    plotter.set_radar(radartype, hires, sweep)
    mapper, _ = plotter.make_plot(mapper=map_to_use)
    mapper.draw_default()