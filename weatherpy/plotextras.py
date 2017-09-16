import functools
from contextlib import contextmanager

import matplotlib.path as mpath
import matplotlib.pyplot as plt
import matplotlib.patheffects as path_effects
import numpy as np
from mpl_toolkits.axes_grid1.inset_locator import inset_axes

from weatherpy import units
from weatherpy.internal import destination_point, logger


def plot_legend(colortable, **plot_kwargs):
    sm = plt.cm.ScalarMappable(cmap=colortable.cmap, norm=colortable.norm)
    # fake up the array of the scalar mappable. Um...
    sm._A = []
    cbar = plt.colorbar(sm, **plot_kwargs)
    return cbar


def plot_offright_inset(ax, colortable, width='3%', height='100%', title=None, color=None, **legend_kwargs):
    ax_inset = inset_axes(ax,
                          width=width,
                          height=height,
                          loc=3,
                          bbox_to_anchor=(1.02, 0, 1, 1),
                          bbox_transform=ax.transAxes,
                          borderpad=0)
    cbar = plot_legend(colortable, title=title, cax=ax_inset, orientation='vertical', **legend_kwargs)
    if title is not None:
        cbar.set_label(title, color=color)
    if color is not None:
        cbar.outline.set_edgecolor(color)
        cbar.ax.xaxis.set_tick_params(color=color)
        plt.setp(plt.getp(cbar.ax.axes, 'yticklabels'), color=color)


def colorbar_inset(ax, colortable, loc=2, width='50%', height='3%', title=None,
                   color='white', label_size=8, major_ticks=True, minor_ticks=False, edgecolor=None,
                   **legend_kwargs):

    logger.info('[EXTRAS] Plotting colorbar')
    ax_inset = inset_axes(ax,
                          width=width,
                          height=height,
                          loc=loc,
                          axes_kwargs=dict(zorder=999))

    cbar = plot_legend(colortable, cax=ax_inset, orientation='horizontal', **legend_kwargs)
    if title is not None:
        cbar.set_label(title, color=color)
    if edgecolor:
        cbar.outline.set_edgecolor(edgecolor)

    if major_ticks:
        tick_kw = dict()
    else:
        tick_kw = dict(bottom='off', top='off')
    cbar.ax.xaxis.set_tick_params(color=color, which='major', direction='in', **tick_kw)

    if minor_ticks:
        cbar.ax.xaxis.set_tick_params(color=color, which='minor', direction='in')
        cbar.ax.minorticks_on()

    if label_size:
        plt.setp(plt.getp(cbar.ax.axes, 'xticklabels'), color=color, size=label_size, y=1.0,
                 path_effects=[_text_shadow])


_text_shadow = path_effects.withSimplePatchShadow(offset=(0.5, -0.5), alpha=0.6, shadow_rgbFace='black')


def bottom_right_stamp(txt, ax, **text_kwargs):
    x = 0.99
    y = 1.0 - x
    return ax.text(x, y, txt, transform=ax.transAxes,
                   horizontalalignment='right', verticalalignment='bottom',
                   path_effects=[_text_shadow], **text_kwargs)


def ring_path(r_mi, ctr):
    theta = np.linspace(0, 360, 100)
    r_km = units.KILOMETER.convert(r_mi, units.MILE)
    dest = np.vectorize(functools.partial(destination_point, ctr[0], ctr[1], r_km))
    ring = np.asarray(dest(theta)).T
    return mpath.Path(ring)


def save_image_no_border(fig, saveloc):
    logger.info('[PLOT] Saving image to: {}'.format(saveloc))
    # commenting these out as they remove any inset axes
    # for ax in fig.get_axes():
    #     ax.set_frame_on(False)
    # plt.axis('off')

    # pad inches < 0 as a hack to remove a bit of extra padding around images.
    fig.savefig(saveloc, bbox_inches='tight', pad_inches=-0.05, transparent=False)


@contextmanager
def figcontext(*args, **kwargs):
    fig = None
    try:
        fig = plt.figure(*args, **kwargs)
        yield fig
    finally:
        if fig is not None:
            plt.close(fig)