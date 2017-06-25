from unittest import TestCase
from unittest.mock import patch

from weatherpy import units
from weatherpy.ctables.core import rgb, rgba, to_rgba, to_fractional, Colortable


class Test_CtableCore(TestCase):
    def test_convert_rgb_to_rgba(self):
        an_rgb = rgb(1, 2, 3)
        an_rgba = rgba(1, 2, 3, 0.5)

        self.assertEqual(to_rgba(an_rgb), rgba(1, 2, 3, 1.0))
        self.assertEqual(to_rgba(an_rgba), an_rgba)

    def test_convert_rgb_and_rgba_to_fractional(self):
        an_rgb = rgb(0, 255, 127.5)
        an_rgba = rgba(0, 255, 127.5, 0.75)

        self.assertEqual(to_fractional(an_rgb), rgb(0, 1, 0.5))
        self.assertEqual(to_fractional(an_rgba), rgba(0, 1, 0.5, 0.75))


class Test_Colortable(TestCase):

    def setUp(self):
        self.mpl_colormap_patcher = patch('matplotlib.colors.LinearSegmentedColormap')
        self.mpl_norm_patcher = patch('matplotlib.colors.Normalize')
        self.load_patcher = patch('weatherpy.ctables.palette_loader.colordict_to_cmap')

        self.mpl_colormap_patch = self.mpl_colormap_patcher.start()
        self.mpl_norm_patch = self.mpl_norm_patcher.start()
        self.load_patch = self.load_patcher.start()

        self.test_colors_dict = {
            100: [rgb(31, 31, 31)],
            50: [rgb(31, 255, 255)],
            -50: [rgb(255, 255, 31)],
            -100: [rgb(145, 31, 145)]
        }

        self.test_cmap_dict = {
            'red': [(0.0, 145 / 255., 145 / 255.), (0.25, 1.0, 1.0), (0.75, 31 / 255., 31 / 255.),
                    (1.0, 31 / 255., 31 / 255.)],
            'green': [(0.0, 31 / 255., 31 / 255.), (0.25, 1.0, 1.0), (0.75, 1.0, 1.0,), (1.0, 31 / 255., 31 / 255.)],
            'blue': [(0.0, 145 / 255., 145 / 255.), (0.25, 31 / 255., 31 / 255.), (0.75, 1.0, 1.0),
                     (1.0, 31 / 255., 31 / 255.)],
            'alpha': [(0.0, 1.0, 1.0), (0.25, 1.0, 1.0), (0.75, 1.0, 1.0), (1.0, 1.0, 1.0)]
        }

        self.load_patch.return_value = self.test_cmap_dict

    def test_create_colortable(self):
        ctable = Colortable('test', self.test_colors_dict, units.CELSIUS)

        self.load_patch.assert_called_with(self.test_colors_dict)
        self.mpl_colormap_patch.assert_called_with('test_C', self.test_cmap_dict)
        self.mpl_norm_patch.assert_called_with(-100, 100, clip=False)

        self.assertEqual(ctable.name, 'test_C')
        self.assertEqual(ctable.unit, units.CELSIUS)
        self.assertEqual(ctable.cmap, self.mpl_colormap_patch.return_value)
        self.assertEqual(ctable.norm, self.mpl_norm_patch.return_value)

        for k, v in ctable.raw.items():
            self.assertEqual(tuple(self.test_colors_dict[k]), v)

    def test_convert_colortable_units(self):
        ctable_C = Colortable('test', self.test_colors_dict, units.CELSIUS)
        ctable_K = ctable_C.convert(units.KELVIN)

        converted_dict = {units.CELSIUS.convert(k, units.KELVIN): v for k, v in self.test_colors_dict.items()}

        self.load_patch.assert_called_with(converted_dict)
        self.mpl_norm_patch.assert_called_with(-100 + 273.15, 100 + 273.15, clip=False)

        self.assertEqual(ctable_K.name, 'test_K')
        self.assertEqual(ctable_K.unit, units.KELVIN)

        for k, v in ctable_K.raw.items():
            self.assertEqual(tuple(converted_dict[k]), v)

    def test_create_and_convert_colortable_scale_units(self):
        original_units = units.Scale(-100, 100)
        new_units = units.Scale()

        ctable0 = Colortable('test', self.test_colors_dict)
        ctable1 = ctable0.convert(new_units)

        converted_dict = {original_units.convert(k, new_units): v for k, v in self.test_colors_dict.items()}

        self.load_patch.assert_called_with(converted_dict)
        self.mpl_norm_patch.assert_called_with(0, 1, clip=False)

        self.assertEqual(ctable1.name, 'test_0.0-1.0')
        self.assertEqual(ctable1.unit, new_units)

        for k, v in ctable1.raw.items():
            self.assertEqual(tuple(converted_dict[k]), v)