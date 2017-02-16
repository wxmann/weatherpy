import matplotlib.pyplot as plt
import pylab
from mpl_toolkits.axes_grid1.inset_locator import inset_axes


def plot_legend(colortable, title=None, **plot_kwargs):
    sm = plt.cm.ScalarMappable(cmap=colortable.cmap, norm=colortable.norm)
    # fake up the array of the scalar mappable. Um...
    sm._A = []
    cbar = plt.colorbar(sm, **plot_kwargs)
    if title is not None:
        cbar.ax.set_title(title)
    return cbar


def plot_offright_inset(ax, colortable, width='3%', height='100%', title=None,
                        **legend_kwargs):
    ax_inset = inset_axes(ax,
                          width=width,
                          height=height,
                          loc=3,
                          bbox_to_anchor=(1.02, 0, 1, 1),
                          bbox_transform=ax.transAxes,
                          borderpad=0)
    plot_legend(colortable, title=title, cax=ax_inset, orientation='vertical', **legend_kwargs)


def save_image_no_border(ax, saveloc, dpi=None):
    ax.set_frame_on(False)
    plt.axis('off')
    pylab.savefig(saveloc, bbox_inches='tight', pad_inches=0, transparent=True, dpi=dpi)


def top_left_stamp(txt, mapper, **text_kwargs):
    x = 0.01
    y = 1.0 - x
    return mapper.ax.text(x, y, txt,
                          transform=mapper.ax.transAxes,
                          horizontalalignment='left',
                          verticalalignment='top',
                          **text_kwargs)
