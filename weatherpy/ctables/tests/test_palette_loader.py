from unittest import TestCase
from unittest import mock

from weatherpy.ctables import palette_loader
from weatherpy.ctables.core import rgb, rgba


class TestPaletteLoader(TestCase):

    @mock.patch('matplotlib.colors.LinearSegmentedColormap')
    def test_should_convert_colortable_only_rgb_to_cmap_and_norm(self, cmapfn):
        name = 'test'

        tbl = {
            100: [rgb(31, 31, 31)],
            50: [rgb(31, 255, 255)],
            -50: [rgb(255, 255, 31)],
            -100: [rgb(145, 31, 145)]
        }

        expected_cmap_dict = {
            'red': [(0.0, 145 / 255., 145 / 255.), (0.25, 1.0, 1.0), (0.75, 31 / 255., 31 / 255.),
                    (1.0, 31 / 255., 31 / 255.)],
            'green': [(0.0, 31 / 255., 31 / 255.), (0.25, 1.0, 1.0), (0.75, 1.0, 1.0,), (1.0, 31 / 255., 31 / 255.)],
            'blue': [(0.0, 145 / 255., 145 / 255.), (0.25, 31 / 255., 31 / 255.), (0.75, 1.0, 1.0),
                     (1.0, 31 / 255., 31 / 255.)],
            'alpha': [(0.0, 1.0, 1.0), (0.25, 1.0, 1.0), (0.75, 1.0, 1.0), (1.0, 1.0, 1.0)]
        }

        _, norm = palette_loader.colorbar_to_cmap_and_norm(name, tbl)

        args_last_call = cmapfn.call_args_list[-1][0]
        arg_name, arg_dict = args_last_call[0], args_last_call[1]
        self.maxDiff = None
        self.assertEqual(arg_name, name)
        self._assert_cmap_dicts_equal(arg_dict, expected_cmap_dict)
        self.assertEqual(norm.vmin, -100)
        self.assertEqual(norm.vmax, 100)

    @mock.patch('matplotlib.colors.LinearSegmentedColormap')
    def test_should_convert_colortable_with_discontinuities_and_alpha_to_cmap_and_norm(self, cmapfn):
        name = 'test'

        tbl = {
            40: [rgba(0, 0, 0, 0.0)],
            30: [rgba(238, 243, 237, 1.0)],
            20: [rgb(0, 4, 165), rgb(0, 217, 255)],
            10: [rgb(52, 133, 15), rgb(124, 255, 0)],
            0: [rgb(160, 99, 45), rgb(250, 0, 0)],
        }

        expected_cmap_dict = {
            'red': [(0.0, 160 / 255., 160 / 255.), (0.25, 250 / 255., 52 / 255.), (0.5, 124 / 255, 0),
                    (0.75, 0, 238 / 255), (1.0, 0, 0)],
            'green': [(0.0, 99 / 255., 99 / 255), (0.25, 0, 133/ 255), (0.5, 1, 4 / 255),
                      (0.75, 217 / 255., 243 / 255.,), (1.0, 0, 0)],
            'blue': [(0.0, 45 / 255., 45 / 255), (0.25, 0, 15 / 255), (0.5, 0, 165 / 255),
                     (0.75, 1, 237 / 255), (1.0, 0, 0)],
            'alpha': [(0.0, 1.0, 1.0), (0.25, 1.0, 1.0), (0.5, 1.0, 1.0), (0.75, 1.0, 1.0), (1.0, 0.0, 0.0)]
        }

        _, norm = palette_loader.colorbar_to_cmap_and_norm(name, tbl)

        args_last_call = cmapfn.call_args_list[-1][0]
        arg_name, arg_dict = args_last_call[0], args_last_call[1]
        self.maxDiff = None
        self.assertEqual(arg_name, name)
        self._assert_cmap_dicts_equal(arg_dict, expected_cmap_dict)
        self.assertEqual(norm.vmin, 0)
        self.assertEqual(norm.vmax, 40)

    def _assert_cmap_dicts_equal(self, dict1, dict2):
        self.assertCountEqual(dict1.keys(), dict2.keys())
        for k in dict1.keys():
            # ordering of the tuples in the value of the dict matters, for matplotlib colormap purposes.
            self.assertEqual(dict1[k], dict2[k])

    def test_should_load_colortable_with_one_rgb_per_line(self):
        file = 'resources/IR_cimms2.pal'
        clrtbl = palette_loader.colorbar_from_pal(file)
        expected = {
            50: [rgb(31, 31, 31, )],
            30: [rgb(0, 113, 113)],
            0: [rgb(31, 255, 255)],
            -30: [rgb(0, 0, 115)],
            -40: [rgb(31, 241, 40)],
            -50: [rgb(255, 255, 31)],
            -60: [rgb(255, 0, 0)],
            -70: [rgb(0, 0, 0)],
            -90: [rgb(255, 255, 255)],
            -110: [rgb(145, 31, 145)]
        }
        self.assertDictEqual(clrtbl, expected)

    def test_should_load_colortable_with_rgba_and_multiple_rgb_per_line(self):
        file = 'resources/IR_navy.pal'
        clrtbl = palette_loader.colorbar_from_pal(file)
        expected = {
            30: [rgba(0, 0, 0, 0.0)],
            -30: [rgba(238, 243, 237, 1.0)],
            -50: [rgb(0, 4, 165), rgb(0, 217, 255)],
            -70: [rgb(52, 133, 15), rgb(124, 255, 0)],
            -80: [rgb(160, 99, 45), rgb(250, 0, 0)],
            -90: [rgb(242, 159, 41), rgb(255, 255, 6)]
        }
        self.assertDictEqual(clrtbl, expected)
