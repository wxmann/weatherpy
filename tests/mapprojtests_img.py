import nose
from matplotlib.testing.decorators import image_comparison

from weatherpy.maps import projections, drawers


@image_comparison(baseline_images=['us_map'],
                  extensions=['png'])
def test_drawing_us_map():
    crs = projections.platecarree()
    mapper = drawers.LargeScaleMap(crs)
    # US box
    mapper.extent = (-130, -65, 24, 51)
    mapper.draw_coastlines()
    mapper.draw_borders()
    mapper.draw_states()


@image_comparison(baseline_images=['se_map'],
                  extensions=['png'])
def test_drawing_se_map_with_counties():
    crs = projections.lambertconformal()
    mapper = drawers.DetailedCountyMap(crs)
    # SE US box
    mapper.extent = (-98, -78, 27, 37)
    mapper.draw_borders()
    mapper.draw_counties()


if __name__ == '__main__':
    nose.main()