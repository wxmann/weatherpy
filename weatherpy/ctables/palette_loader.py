from weatherpy import units, logger
from weatherpy.ctables.core import rgb, rgba, to_rgba, to_fractional, Colortable, RGB_SCALE, UNITY_SCALE
from weatherpy.internal.calcs import relative_percentage
from weatherpy.units import UnitsException


def load_colortable(name, palfile):
    rawcolors, unit = colorbar_from_pal(palfile)
    return Colortable(name, rawcolors, unit)

#################################################
#    Converting .pal to dictionary of colors    #
#################################################


def colorbar_from_pal(palfile):
    colorbar = {}
    unit = None
    with open(palfile, encoding='utf-8') as paldata:
        for line in paldata:
            if line and line[0] != ';':
                results = _parse_pal_line(line)
                if isinstance(results, tuple) and len(results) == 2:
                    bndy, clrs = results
                    if bndy is not None:
                        colorbar[float(bndy)] = clrs
                elif isinstance(results, units.Unit):
                    unit = results
    return colorbar, unit


def _parse_pal_line(line):
    tokens = line.split()
    header = tokens[0] if tokens else None

    if header is not None:
        if 'color' in header.lower():
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

        elif 'unit' in header.lower():
            unitstr = tokens[1]
            try:
                return units.get(unitstr)
            except UnitsException:
                logger.info('Could not parse unit: {}, defaulting to no unit'.format(unitstr))
                return None

    return None, None


def _getcolor(rgba_vals, has_alpha):
    if has_alpha:
        alpha = UNITY_SCALE.convert(float(rgba_vals[3]), RGB_SCALE)
        return rgba(r=int(rgba_vals[0]), g=int(rgba_vals[1]), b=int(rgba_vals[2]), a=alpha)
    else:
        return rgb(r=int(rgba_vals[0]), g=int(rgba_vals[1]), b=int(rgba_vals[2]))


###################################################
# Converting dict to cmap and norm for matplotlib #
###################################################


def colordict_to_cmap(colors_dict):
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