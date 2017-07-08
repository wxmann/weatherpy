from weatherpy.maps import extents
from weatherpy.satellite import goeslegacy


def latest_ir_southwest_us():
    sel = goeslegacy.conus_west('ir').latest()
    with sel:
        mapper, _ = sel.make_plot(extent=extents.us_southwest)
        mapper.draw_default()

    import matplotlib.pyplot as plt
    plt.show()

if __name__ == '__main__':
    latest_ir_southwest_us()