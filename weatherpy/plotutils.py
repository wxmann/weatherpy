import matplotlib.pyplot as plt
import pylab


def plot_legend(colortable, **plot_kwargs):
    sm = plt.cm.ScalarMappable(cmap=colortable.cmap, norm=colortable.norm)
    # fake up the array of the scalar mappable. Um...
    sm._A = []
    plt.colorbar(sm, **plot_kwargs)


def save_image_no_border(ax, saveloc, dpi=None):
    ax.set_frame_on(False)
    plt.axis('off')
    pylab.savefig(saveloc, bbox_inches='tight', pad_inches=0, transparent=True, dpi=dpi)