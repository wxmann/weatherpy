from weatherpy.satellite import goes16

if __name__ == '__main__':
    sel = goes16.meso2(channel=14)

    with sel.latest() as plotter:
        mapper, _ = plotter.make_plot(strict=False)
        mapper.draw_default()

        import matplotlib.pyplot as plt
        plt.show()