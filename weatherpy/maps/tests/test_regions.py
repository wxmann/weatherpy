import pytest

from weatherpy import maps

from cartopy import crs as ccrs
import matplotlib.pyplot as plt


@pytest.mark.mpl_image_compare
def test_conus_region():
    fig = plt.figure()
    crs = ccrs.AlbersEqualArea()
    mapper = maps.LargeScaleMap(crs)
    mapper.extent = maps.regions.conus
    mapper.draw_default()