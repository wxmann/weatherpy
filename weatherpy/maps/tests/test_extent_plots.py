import pytest

from weatherpy import maps

from cartopy import crs as ccrs
import matplotlib.pyplot as plt

from weatherpy.maps import extents


@pytest.mark.mpl_image_compare(tolerance=20)
def test_conus_region():
    fig = plt.figure()
    _draw_maps_with_eastern_us_region(extents.conus)
    return fig


@pytest.mark.mpl_image_compare(tolerance=20)
def test_us_southeast_region():
    fig = plt.figure()
    _draw_maps_with_eastern_us_region(extents.us_southeast)
    return fig


@pytest.mark.mpl_image_compare(tolerance=20)
def test_us_southcentral_region():
    fig = plt.figure()
    _draw_maps_with_eastern_us_region(extents.us_southctrl)
    return fig


@pytest.mark.mpl_image_compare(tolerance=20)
def test_us_southwest_region():
    fig = plt.figure()
    _draw_maps_with_west_coast_us_region(extents.us_southwest)
    return fig


@pytest.mark.mpl_image_compare(tolerance=20)
def test_us_northwest_region():
    fig = plt.figure()
    _draw_maps_with_west_coast_us_region(extents.us_northwest)
    return fig


@pytest.mark.mpl_image_compare(tolerance=20)
def test_us_northcentral_region():
    fig = plt.figure()
    _draw_maps_with_eastern_us_region(extents.us_northctrl)
    return fig


@pytest.mark.mpl_image_compare(tolerance=20)
def test_us_northeast_region():
    fig = plt.figure()
    _draw_maps_with_eastern_us_region(extents.us_northeast)
    return fig


@pytest.mark.mpl_image_compare(tolerance=20)
def test_southern_plains_region():
    fig = plt.figure()
    _draw_maps_with_eastern_us_region(extents.southern_plains)
    return fig


@pytest.mark.mpl_image_compare(tolerance=20)
def test_central_plains_region():
    fig = plt.figure()
    _draw_maps_with_eastern_us_region(extents.central_plains)
    return fig


@pytest.mark.mpl_image_compare(tolerance=20)
def test_northern_plains_region():
    fig = plt.figure()
    _draw_maps_with_eastern_us_region(extents.northern_plains)
    return fig


@pytest.mark.mpl_image_compare(tolerance=20)
def test_dixie_region():
    fig = plt.figure()
    _draw_maps_with_eastern_us_region(extents.dixie)
    return fig


@pytest.mark.mpl_image_compare(tolerance=20)
def test_midwest_region():
    fig = plt.figure()
    _draw_maps_with_eastern_us_region(extents.midwest)
    return fig


@pytest.mark.mpl_image_compare(tolerance=20)
def test_gulf_of_mexico_region():
    fig = plt.figure()
    _draw_maps_with_eastern_us_region(extents.gulf_of_mexico)
    return fig


@pytest.mark.mpl_image_compare(tolerance=20)
def test_florida_region():
    fig = plt.figure()
    _draw_maps_with_eastern_us_region(extents.florida)
    return fig


@pytest.mark.mpl_image_compare(tolerance=20)
def test_carolinas_region():
    fig = plt.figure()
    _draw_maps_with_eastern_us_region(extents.carolinas)
    return fig


@pytest.mark.mpl_image_compare(tolerance=20)
def test_northeast_megalopolis_region():
    fig = plt.figure()
    _draw_maps_with_eastern_us_region(extents.northeast_megalopolis)
    return fig


@pytest.mark.mpl_image_compare(tolerance=20)
def test_california_region():
    fig = plt.figure()
    _draw_maps_with_west_coast_us_region(extents.california)
    return fig


def _draw_maps_with_eastern_us_region(region):
    for i, proj in enumerate([ccrs.PlateCarree(),
                             ccrs.AlbersEqualArea(central_longitude=-100.0),
                             maps.projections.goes_east_nearside(),
                             ccrs.LambertConformal(),
                             ccrs.Mercator()]):
        mapper = maps.LargeScaleMap(proj)
        mapper.extent = region
        mapper.initialize_drawing('32' + str(i + 1))
        mapper.draw_default()


def _draw_maps_with_west_coast_us_region(region):
    for i, proj in enumerate([ccrs.PlateCarree(),
                             ccrs.AlbersEqualArea(central_longitude=-100.0),
                             maps.projections.goes_west_nearside(),
                             ccrs.LambertConformal(),
                             ccrs.Mercator()]):
        mapper = maps.LargeScaleMap(proj)
        mapper.extent = region
        mapper.initialize_drawing('32' + str(i + 1))
        mapper.draw_default()
