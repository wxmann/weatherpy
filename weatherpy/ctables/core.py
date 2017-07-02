from collections import namedtuple

from matplotlib import colors

from weatherpy import units
from weatherpy.ctables import palette_loader
from weatherpy.units import Scale


class Colortable(object):
    def __init__(self, basename, colors_dict, unit=None):
        # TODO: register ctable name to matplotlib?
        self._basename = basename
        self._colors_dict = colors_dict
        if unit is None:
            self._unit = units.Scale(min(colors_dict), max(colors_dict))
        else:
            self._unit = unit
        self._cmap, self._norm = self._calculate_cmap_and_norm()

    def _calculate_cmap_and_norm(self):
        cmap_dict = palette_loader.colordict_to_cmap(self._colors_dict)
        cmap = colors.LinearSegmentedColormap(self.name, cmap_dict)
        norm = colors.Normalize(min(self._colors_dict), max(self._colors_dict), clip=False)
        return cmap, norm

    @property
    def name(self):
        return self._basename + '_' + self._unit.abbrevs[0]

    @property
    def raw(self):
        return {k: tuple(v) for k, v in self._colors_dict.items()}

    @property
    def cmap(self):
        return self._cmap

    @property
    def norm(self):
        return self._norm

    @property
    def unit(self):
        return self._unit

    def convert(self, to_unit):
        if to_unit == self._unit:
            return self
        elif isinstance(to_unit, str):
            to_unit = units.get(to_unit)

        # implementation detail: the values of new_dict must be deep-copies
        # TODO: This bug should be addressed in the near-future
        new_dict = {self._unit.convert(k, to_unit): list(v) for k, v in self._colors_dict.items()}
        return Colortable(self._basename, new_dict, to_unit)

    def __eq__(self, other):
        if self is other:
            return True
        return isinstance(other, Colortable) and (self._basename,
                                                  self._cmap,
                                                  self._norm,
                                                  self._unit) == (other._basename,
                                                                  other._cmap,
                                                                  other._norm,
                                                                  other._unit)

    def __hash__(self):
        return hash((self._basename, self._cmap, self._norm, self._unit))


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
