import pytest

import matplotlib.pyplot as plt
import cartopy.crs as ccrs

from weatherpy.maps import artist


@pytest.mark.mpl_image_compare(tolerance=20)
def test_draw_standalone():
    crs = ccrs.Mercator()

    mapper = artist.MapArtist(crs, extent=(-127.5, -112, 30, 43))
    mapper.draw()

    return plt.gcf()


@pytest.mark.mpl_image_compare(tolerance=20)
def test_draw_switching_extents():
    fig = plt.figure()
    crs = ccrs.Mercator()

    mapper = artist.MapArtist(crs, extent=(-127.5, -112, 30, 43))
    mapper.draw(subplot=211, fig=fig)

    mapper.extent = (-90, -77.5, 23, 32.5)
    mapper.draw(subplot=212, fig=fig)

    return fig


@pytest.mark.mpl_image_compare(tolerance=20)
def test_draw_switching_properties():
    fig = plt.figure()
    crs = ccrs.Mercator()

    mapper = artist.MapArtist(crs, extent=(-127.5, -112, 30, 43))
    mapper.backend.border_properties.strokecolor = 'blue'
    mapper.draw(subplot=311, fig=fig)

    mapper.backend.border_properties.alpha = 0.2
    mapper.draw(subplot=312, fig=fig)

    mapper.backend.border_properties.alpha = 1.0
    mapper.backend.border_properties.strokecolor = 'black'
    mapper.draw(subplot=313, fig=fig)

    return fig


@pytest.mark.mpl_image_compare(tolerance=20)
def test_draw_different_layers():
    fig = plt.figure()
    crs = ccrs.Mercator()

    mapper = artist.MapArtist(crs, extent=(-127.5, -112, 30, 43))
    mapper.draw(subplot=211, detailed=True)
    mapper.draw(subplot=212, layers=['states'])

    return fig