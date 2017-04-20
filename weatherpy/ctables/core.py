import functools
from collections import namedtuple

from weatherpy.calcs import relative_percentage

colortable = namedtuple('colortable', 'cmap norm')

rgb = namedtuple('rgb', 'r g b')
rgba = namedtuple('rgba', 'r g b a')

MIN_RGB_VALUE = 0
MAX_RGB_VALUE = 255


def to_rgba(rgb_tup):
    if isinstance(rgb_tup, rgba):
        return rgb_tup
    return rgba(rgb_tup.r, rgb_tup.g, rgb_tup.b, 1.0)


def to_fractional(rgb_tup):
    if isinstance(rgb_tup, rgb):
        return rgb(_rgb_frac(rgb_tup.r), _rgb_frac(rgb_tup.g), _rgb_frac(rgb_tup.b))
    else:
        return rgba(_rgb_frac(rgb_tup.r), _rgb_frac(rgb_tup.g), _rgb_frac(rgb_tup.b), rgb_tup.a)


_rgb_frac = functools.partial(relative_percentage, minval=MIN_RGB_VALUE, maxval=MAX_RGB_VALUE)