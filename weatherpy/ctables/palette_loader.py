from matplotlib import colors

from weatherpy.ctables.core import rgb, rgba, MAX_RGB_VALUE, to_rgba, to_fractional, colortable
from weatherpy.internal.calcs import relative_percentage


def load_colortable(name, palfile):
    rawcolors = colorbar_from_pal(palfile)
    cmap, norm = colorbar_to_cmap_and_norm(name, rawcolors)
    return colortable(cmap=cmap, norm=norm)

#################################################
#    Converting .pal to dictionary of colors    #
#################################################


def colorbar_from_pal(palfile):
    colorbar = {}
    with open(palfile) as paldata:
        for line in paldata:
            if line and line[0] != ';':
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
        alpha = float(rgba_vals[3]) / MAX_RGB_VALUE
        return rgba(r=int(rgba_vals[0]), g=int(rgba_vals[1]), b=int(rgba_vals[2]), a=alpha)
    else:
        return rgb(r=int(rgba_vals[0]), g=int(rgba_vals[1]), b=int(rgba_vals[2]))


###################################################
# Converting dict to cmap and norm for matplotlib #
###################################################


def colorbar_to_cmap_and_norm(name, colors_dict):
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

            lobound_frac = relative_percentage(lobound, min_bound, max_bound)
            hibound_frac = relative_percentage(hibound, min_bound, max_bound)
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
