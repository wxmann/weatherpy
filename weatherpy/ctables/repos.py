import os
from functools import wraps

import config
from weatherpy.ctables.palette_loader import load_colortable


class Repo(object):
    def __init__(self):
        super(Repo, self).__setattr__('_entries', {})

    def __getattr__(self, item):
        return self._entries[item]()

    def __setattr__(self, label, palfile_or_mpl_cmap):
        if palfile_or_mpl_cmap.endswith('.pal'):
            self._entries[label] = _load_for_repo(label, palfile_or_mpl_cmap)
        else:
            self._entries[label] = _return_arg(palfile_or_mpl_cmap)


def memoized(func):
    cache = {}

    @wraps(func)
    def wrapped_func(*args, **kwargs):
        key = str(args) + str(kwargs)
        if key not in cache:
            val = func(*args, **kwargs)
            cache[key] = val
            return val
        return cache[key]

    return wrapped_func


def lock_args(func):
    @wraps(func)
    def wrapped_func(*args, **kwargs):
        return lambda: func(*args, **kwargs)

    return wrapped_func


@lock_args
@memoized
def _load_for_repo(ctable_name, filename):
    abs_path = os.sep.join([config.PALETTES_DIR, filename])
    return load_colortable(ctable_name, abs_path)


@lock_args
def _return_arg(arg):
    return arg


ir = Repo()
ir.navy = 'IR_navy.pal'
ir.rainbow = 'IR_rainbow.pal'
ir.enh4 = 'IR4.pal'
ir.cimms = 'IR_cimms2.pal'
ir.alpha = 'IR_alpha.pal'

vis = Repo()
vis.default = 'Visible-depth.pal'
vis.optimized = 'Visible-depth-modified.pal'
vis.transparent = 'Visible-trans.pal'

wv = Repo()
wv.accuwx = 'WV3_accuwx.pal'
wv.noaa = 'WV_noaa.pal'

reflectivity = Repo()
reflectivity.avl = 'refl_avl.pal'
reflectivity.nws_default = 'NWS_Default.pal'
reflectivity.radarscope = 'RadarScope.pal'

velocity = Repo()
velocity.default = 'Enhanced-Velocity.pal'

diff_reflectivity = Repo()
diff_reflectivity.default = 'AWIPS-ZDR.pal'
