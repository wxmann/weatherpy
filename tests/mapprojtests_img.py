import nose
from matplotlib.testing.decorators import image_comparison

from weatherpy import mapproj


@image_comparison(baseline_images=['us_map'],
                  extensions=['png'])
def test_drawing_us_map():
    mapper = mapproj.platecarree()
    # US box
    mapper.extent = (-130, -65, 24, 51)
    mapper.draw_coastlines()
    mapper.draw_borders()
    mapper.draw_states()


if __name__ == '__main__':
    nose.main()