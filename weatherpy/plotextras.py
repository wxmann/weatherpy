import functools
from contextlib import contextmanager

import matplotlib.path as mpath
import matplotlib.pyplot as plt
import numpy as np
import pylab
from mpl_toolkits.axes_grid1.inset_locator import inset_axes

from weatherpy import logger
from weatherpy.calcs import miles2km, destination_point


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


def top_right_inset(ax, colortable, width='50%', height='3%', title=None, labels=True,
                    color=None, label_size=10,
                    **legend_kwargs):
    ax_inset = inset_axes(ax,
                          width=width,
                          height=height,
                          loc=1,
                          axes_kwargs=dict(zorder=999))
    cbar = plot_legend(colortable, cax=ax_inset, orientation='horizontal', **legend_kwargs)
    if title is not None:
        cbar.set_label(title, color=color)
    if labels:
        cbar.outline.set_edgecolor(color)
        cbar.ax.xaxis.set_tick_params(color=color)
        plt.setp(plt.getp(cbar.ax.axes, 'xticklabels'), color=color, size=label_size)


def bottom_right_stamp(txt, ax, **text_kwargs):
    x = 0.99
    y = 1.0 - x
    return ax.text(x, y, txt, transform=ax.transAxes,
                   horizontalalignment='right', verticalalignment='bottom', **text_kwargs)


def ring_path(r_mi, ctr):
    theta = np.linspace(0, 360, 100)
    r_km = miles2km(r_mi)
    dest = np.vectorize(functools.partial(destination_point, ctr[0], ctr[1], r_km))
    ring = np.asarray(dest(theta)).T
    return mpath.Path(ring)


def save_image_no_border(fig, saveloc):
    logger.info('[PLOT] Saving image to: {}'.format(saveloc))
    for ax in fig.get_axes():
        ax.set_frame_on(False)
    # plt.axis('off')
    pylab.savefig(saveloc, bbox_inches='tight', pad_inches=0, transparent=False)


@contextmanager
def figcontext(*args, **kwargs):
    fig = None
    try:
        fig = plt.figure(*args, **kwargs)
        yield fig
    finally:
        if fig is not None:
            plt.close(fig)