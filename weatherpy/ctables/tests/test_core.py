from unittest import TestCase

from weatherpy.ctables.core import rgb, rgba, to_rgba, to_fractional


class TestCtableCore(TestCase):
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