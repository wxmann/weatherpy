import functools
import os
from collections import namedtuple

from matplotlib import colors

import config

colortable = namedtuple('colortable', 'cmap norm')
rgb = namedtuple('rgb', 'r g b')
rgba = namedtuple('rgba', 'r g b a')

_min_rgb = 0
_max_rgb = 255


def to_rgba(rgb_tup):
    if isinstance(rgb_tup, rgba):
        return rgb_tup
    return rgba(rgb_tup.r, rgb_tup.g, rgb_tup.b, 1.0)


def to_fractional(rgb_tup):
    if isinstance(rgb_tup, rgb):
        return rgb(_rgb_frac(rgb_tup.r), _rgb_frac(rgb_tup.g), _rgb_frac(rgb_tup.b))
    else:
        return rgba(_rgb_frac(rgb_tup.r), _rgb_frac(rgb_tup.g), _rgb_frac(rgb_tup.b), rgb_tup.a)


def relative_pos(val, minval, maxval):
    return (val - minval) / (maxval - minval)


_rgb_frac = functools.partial(relative_pos, minval=_min_rgb, maxval=_max_rgb)


###################################################
# Converting dict to cmap and norm for matplotlib #
###################################################


def colors_to_cmap_and_norm(name, colors_dict):
    cmap_dict = _rawdict2cmapdict(colors_dict)
    norm = colors.Normalize(min(colors_dict), max(colors_dict), clip=False)
    return colors.LinearSegmentedColormap(name, cmap_dict), norm


def _rawdict2cmapdict(colors_dict):
    cmap_dict = {
        'red': [],
        'green': [],
        'blue': [],
        'alpha': []
    }
    max_bound = max(colors_dict)
    min_bound = min(colors_dict)

    if max_bound == min_bound:
        raise ValueError("Color map requires more than one color")

    bounds_in_order = sorted(colors_dict.keys())

    for i, bound in enumerate(bounds_in_order):
        if i == len(bounds_in_order) - 1:
            # last element, avoid having extra entries in the colortable map
            pass
        else:
            lobound = bounds_in_order[i]
            hibound = bounds_in_order[i+1]
            locolors = colors_dict[lobound]
            hicolors = colors_dict[hibound]
            if not locolors or not hicolors:
                raise ValueError("Invalid colormap file, empty colors.")
            if len(locolors) < 2:
                locolors.append(hicolors[0])

            lobound_frac = relative_pos(lobound, min_bound, max_bound)
            hibound_frac = relative_pos(hibound, min_bound, max_bound)
            locolor1 = to_fractional(to_rgba(locolors[0]))
            locolor2 = to_fractional(to_rgba(locolors[1]))
            hicolor1 = to_fractional(to_rgba(hicolors[0]))

            def _append_colors(color):
                attr = color[0]
                # the first element
                if i == 0:
                    cmap_dict[color].append((lobound_frac, getattr(locolor1, attr), getattr(locolor1, attr)))
                    cmap_dict[color].append((hibound_frac, getattr(locolor2, attr), getattr(hicolor1, attr)))
                else:
                    cmap_dict[color].append((hibound_frac, getattr(locolor2, attr), getattr(hicolor1, attr)))

            _append_colors('red')
            _append_colors('green')
            _append_colors('blue')
            _append_colors('alpha')

    for k in cmap_dict:
        cmap_dict[k] = sorted(cmap_dict[k], key=lambda tup: tup[0])
    return cmap_dict


#################################################
#    Converting .pal to dictionary of colors    #
#################################################


def from_pal(palfile):
    colorbar = {}
    with open(palfile) as paldata:
        for line in paldata:
            bndy, clrs = _parse_pal_line(line)
            if bndy is not None:
                colorbar[float(bndy)] = clrs
    return colorbar


def _parse_pal_line(line):
    tokens = line.split()
    header = tokens[0] if tokens else None

    if header is not None and 'color' in header.lower():
        cdata = tokens[1:]
        isrgba = 'color4' in header.lower()
        if not cdata:
            return None, None
        bndy = cdata[0]
        rgba_vals = cdata[1:]
        clrs = [_getcolor(rgba_vals, isrgba)]

        if len(rgba_vals) > 4:
            index = 4 if isrgba else 3
            rgba_vals = rgba_vals[index:]
            clrs.append(_getcolor(rgba_vals, isrgba))

        return bndy, clrs

    return None, None


def _getcolor(rgba_vals, has_alpha):
    if has_alpha:
        alpha = float(rgba_vals[3]) / _max_rgb
        return rgba(r=int(rgba_vals[0]), g=int(rgba_vals[1]), b=int(rgba_vals[2]), a=alpha)
    else:
        return rgb(r=int(rgba_vals[0]), g=int(rgba_vals[1]), b=int(rgba_vals[2]))


###########################
#  Standard colortables.  #
###########################

def load_colortable(name, palfile):
    rawcolors = from_pal(palfile)
    cmap, norm = colors_to_cmap_and_norm(name, rawcolors)
    return colortable(cmap=cmap, norm=norm)


class Repo(object):
    @staticmethod
    def _get_rel_path(palette_file):
        return os.sep.join(['', 'colortable-palettes', palette_file])

    files = {
        'IR_navy': 'IR_navy.pal',
        'IR_rainbow': 'IR_rainbow.pal',
        'IR_rammb': 'IR_rammb.pal',
        'IR4': 'IR4.pal',
        'IR_cimms2': 'IR_cimms2.pal',
        'VIS_depth': 'Visible-depth.pal',
        'WV3_accuwx': 'WV3_accuwx.pal',
        'WV_noaa': 'WV_noaa.pal',
        'refl_avl': 'refl_avl.pal',
        'nws_default': 'NWS_Default.pal',
        'radarscope': 'RadarScope.pal'
    }

    def __init__(self):
        pass

    def __getattr__(self, item):
        try:
            return load_colortable(item, config.ROOT_PROJECT_DIR + Repo._get_rel_path(Repo.files[item]))
        except KeyError:
            raise InvalidColortableException("Invalid colortable provided: {}".format(item))


class InvalidColortableException(Exception):
    pass


_repo = Repo()

# IR satellite
ir_navy = _repo.IR_navy
ir_rainbow = _repo.IR_rainbow
ir_rammb = _repo.IR_rammb
ir4 = _repo.IR4
ir_cimms = _repo.IR_cimms2

# VIS satellite
vis_depth = _repo.VIS_depth

# WV satellite
wv_accuwx = _repo.WV3_accuwx
wv_noaa = _repo.WV_noaa

# Reflectivity
refl_avl = _repo.refl_avl
nws = _repo.nws_default
radarscope = _repo.radarscope

