from collections import namedtuple

from weatherpy.units import Scale


class Colortable(object):
    def __init__(self, cmap, norm, unit):
        self._cmap = cmap
        self._norm = norm
        self._unit = unit

    @property
    def cmap(self):
        return self._cmap

    @property
    def norm(self):
        return self._norm

    @property
    def unit(self):
        return self._unit


rgb = namedtuple('rgb', 'r g b')
rgba = namedtuple('rgba', 'r g b a')

RGB_SCALE = Scale(0, 255)
UNITY_SCALE = Scale()


def to_rgba(rgb_tup):
    if isinstance(rgb_tup, rgba):
        return rgb_tup
    return rgba(rgb_tup.r, rgb_tup.g, rgb_tup.b, 1.0)


def to_fractional(rgb_tup):
    r, g, b = (RGB_SCALE.convert(rgb_tup.r, UNITY_SCALE),
               RGB_SCALE.convert(rgb_tup.g, UNITY_SCALE),
               RGB_SCALE.convert(rgb_tup.b, UNITY_SCALE))
    if isinstance(rgb_tup, rgb):
        return rgb(r, g, b)
    else:
        return rgba(r, g, b, rgb_tup.a)
