import os

import matplotlib.pyplot as plt
import netCDF4
import pytest
import cartopy.crs as ccrs

import config
from weatherpy import ctables, maps
from weatherpy.maps import extents
from weatherpy.satellite.goes16 import Goes16Plotter

VISIBLE_SECTOR_FILE = 'GOES16_Mesoscale-1_20170628_235927_0.64_500m_41.8N_95.6W_Ch02.nc4'
INFRARED_SECTOR_FILE = 'GOES16_Mesoscale-1_20170628_235927_11.20_2km_41.8N_95.6W_Ch14.nc4'
WV_SECTOR_FILE = 'GOES16_Mesoscale-1_20170628_235927_6.19_2km_41.8N_95.6W_Ch08.nc4'

INFRARED_FULL_DISK_FILE = 'GOES16_FullDisk_20170710_000037_11.20_6km_0.0S_89.5W_Ch14.nc4'


@pytest.mark.mpl_image_compare(tolerance=20)
def test_plot_visible():
    fig = plt.figure()
    dataset = netCDF4.Dataset(os.sep.join([config.TEST_DATA_DIR, VISIBLE_SECTOR_FILE]))

    with Goes16Plotter(dataset) as plotter:
        extent = extents.zoom((41.6, -93.6), km=300)
        mapper, _ = plotter.make_plot(extent=extent)
        mapper.draw_default()

    return fig


@pytest.mark.mpl_image_compare(tolerance=20)
def test_plot_infrared_default_ctable():
    fig = plt.figure()
    dataset = netCDF4.Dataset(os.sep.join([config.TEST_DATA_DIR, INFRARED_SECTOR_FILE]))

    with Goes16Plotter(dataset) as plotter:
        extent = extents.zoom((41.6, -93.6), km=300)
        mapper, _ = plotter.make_plot(extent=extent)
        mapper.draw_default()

    return fig


@pytest.mark.mpl_image_compare(tolerance=20)
def test_plot_infrared_rainbow_ctable():
    fig = plt.figure()
    dataset = netCDF4.Dataset(os.sep.join([config.TEST_DATA_DIR, INFRARED_SECTOR_FILE]))

    with Goes16Plotter(dataset) as plotter:
        extent = extents.zoom((41.6, -93.6), km=300)
        mapper, _ = plotter.make_plot(colortable=ctables.ir.rainbow, extent=extent)
        mapper.draw_default()

    return fig


@pytest.mark.mpl_image_compare(tolerance=20)
def test_plot_extent_larger_than_data_region():
    fig = plt.figure()
    dataset = netCDF4.Dataset(os.sep.join([config.TEST_DATA_DIR, INFRARED_SECTOR_FILE]))

    with Goes16Plotter(dataset) as plotter:
        extent = extents.zoom((41.6, -93.6), km=1000)
        mapper, _ = plotter.make_plot(extent=extent)
        mapper.draw_default()

    return fig


@pytest.mark.mpl_image_compare(tolerance=20)
def test_plot_infrared_reprojected():
    fig = plt.figure()
    dataset = netCDF4.Dataset(os.sep.join([config.TEST_DATA_DIR, INFRARED_SECTOR_FILE]))

    with Goes16Plotter(dataset) as plotter:
        extent = extents.zoom((41.6, -95.1), km=500)
        crs = ccrs.NearsidePerspective(central_longitude=plotter.position.longitude,
                                       central_latitude=plotter.position.latitude,
                                       satellite_height=plotter.position.altitude)
        mapper = maps.LargeScaleMap(crs)
        mapper.extent = extent
        plotter.make_plot(mapper)
        mapper.draw_default()

    return fig


@pytest.mark.mpl_image_compare(tolerance=20)
def test_plot_outside_of_data_region():
    fig = plt.figure()
    dataset = netCDF4.Dataset(os.sep.join([config.TEST_DATA_DIR, INFRARED_SECTOR_FILE]))

    with Goes16Plotter(dataset) as plotter:
        extent = extents.zoom((37.8, -122.4), km=300)
        mapper, _ = plotter.make_plot(extent=extent)
        mapper.draw_default()

    return fig


@pytest.mark.mpl_image_compare(tolerance=20, filename='test_plot_infrared_default_ctable.png')
def test_plot_no_strict_mode():
    fig = plt.figure()
    dataset = netCDF4.Dataset(os.sep.join([config.TEST_DATA_DIR, INFRARED_SECTOR_FILE]))

    with Goes16Plotter(dataset) as plotter:
        extent = extents.zoom((41.6, -93.6), km=300)
        mapper, _ = plotter.make_plot(extent=extent, strict=False)
        mapper.draw_default()

    return fig


@pytest.mark.mpl_image_compare(tolerance=20)
def test_plot_wv_channel_default_ctable():
    fig = plt.figure()
    dataset = netCDF4.Dataset(os.sep.join([config.TEST_DATA_DIR, WV_SECTOR_FILE]))

    with Goes16Plotter(dataset) as plotter:
        extent = extents.zoom((41.6, -93.6), km=300)
        mapper, _ = plotter.make_plot(extent=extent)
        mapper.draw_default()

    return fig


@pytest.mark.mpl_image_compare(tolerance=20)
def test_plot_infrared_full_disk():
    fig = plt.figure()
    dataset = netCDF4.Dataset(os.sep.join([config.TEST_DATA_DIR, INFRARED_FULL_DISK_FILE]))

    with Goes16Plotter(dataset) as plotter:
        mapper, _ = plotter.make_plot()
        mapper.draw_default()

    return fig