from typing import Tuple, List
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.ticker import ScalarFormatter


def flux_array_to_square_grid(array: [], length_side: int = None) -> []:
    """
    Will copy the passed array into a square 2d grid.  Alternate rows will be flipped so that the progressing
    is "snake-n-ladders" style (along, down one, back) rather than raster scan.
    """
    if length_side is None:
        length_side = int(np.sqrt(len(array)))

    grid = np.reshape(array.copy(), (length_side, length_side))
    for row_ix in np.arange(1, 12, 2):
        grid[row_ix] = np.flip(grid[row_ix])
    return grid


def plot_histogram_to_ax(ax: Axes, flux_ratios: [float], is_blue: bool):
    """
    Produce a histogram showing the distribution of the non_ss_spectra ratios
    """
    ax.set_title(f"Histogram of the H$\\{'beta' if is_blue else 'alpha'}$/continuum\nnon_ss_spectra ratio over the fibre array")
    bin_edges = np.arange(0, 125, 5)
    ax.set_yscale("log")
    ax.yaxis.set_major_formatter(ScalarFormatter())
    ax.set(ylabel="count", xlabel="non_ss_spectra ratio")
    ax.hist(flux_ratios, bins=bin_edges, align="mid", rwidth=0.8, density=False)
    ax.annotate(f"max={max(flux_ratios):.2f}\nmin={min(flux_ratios):.2f}", xy=(0.5, 0.85), xycoords="axes fraction")
    return


def plot_fibre_heatmap_to_ax(fig: Figure, ax: Axes, flux_ratios: [float]):
    c_map = cm.get_cmap("plasma")
    norm = matplotlib.colors.Normalize(vmin=0, vmax=100)
    flux_grid = flux_array_to_square_grid(flux_ratios)
    ax.set_title(f"The heatmap of the non_ss_spectra ratio\nover the FRODOspec fibre array\n")
    ax.set(xlim=(0, 12), ylim=(0, 12), xticks=[0, 2, 4, 6, 8, 10, 12], xticklabels=[], yticks=[0, 2, 4, 6, 8, 10, 12])
    ax.imshow(flux_grid, cmap=c_map, norm=norm, origin="upper", aspect="equal", extent=(0, 12, 12, 0))
    fig.colorbar(cm.ScalarMappable(cmap=c_map, norm=norm), ax=[ax], orientation="vertical", fraction=0.2, pad=0.15)
    return


def plot_spectrum_to_ax(ax: Axes, wavelength: [float], ss_spec_flux: [float], title: str,
                        c_range: Tuple[float, float] = None, h_range: Tuple[float, float] = None,
                        sky_flux: [float] = None, nss_spec_flux: [float] = None):
    ax.set_xlabel("Wavelength [angstrom]")
    ax.set_ylabel("Arbitrary flux")
    ax.set_title(title)
    x_tick_range = (min(wavelength), max(wavelength))
    ax.set_xticks(np.arange(x_tick_range[0], x_tick_range[1]+1, 250), minor=False)
    ax.set_xticks(np.arange(x_tick_range[0], x_tick_range[1]+1, 50), minor=True)
    color = "b" if x_tick_range[0] < 5000 else "r"

    if ss_spec_flux is not None and len(ss_spec_flux) == len(wavelength):
        ax.plot(wavelength, ss_spec_flux, color=color, linestyle="-", linewidth=0.25)

    if nss_spec_flux is not None and len(nss_spec_flux) == len(wavelength):
        ax.plot(wavelength, nss_spec_flux, color="grey", linestyle="-", linewidth=0.25, alpha=0.3)

    if sky_flux is not None and len(sky_flux) == len(wavelength):
        ax.plot(wavelength, sky_flux, color="c", linestyle="-", linewidth=0.25, alpha=0.5)

    if c_range is not None:
        ax.axvspan(xmin=c_range[0], xmax=c_range[1], color="c", alpha=0.05)

    if h_range is not None:
        ax.axvspan(xmin=h_range[0], xmax=h_range[1], color=color, alpha=0.05)
    return


def plot_rss_spectra(wavelength: [float, float], flux: [float, float], flux_ratios: [float], basename: str, sky_mask: [bool], spec_mask: [bool],
                     c_range: Tuple[float, float], h_range: Tuple[float, float], output_dir: str, enhance: bool = True):
    fig = plt.figure(figsize=(12.8, 25.6), constrained_layout=True)
    ax = fig.add_subplot(1, 1, 1)

    ax.set_xlabel("Wavelength [angstrom]")
    ax.set_ylabel("Arbitrary flux")
    ax.set_title(f"The RSS_NONSS spectra in {basename}")
    x_tick_range = (min(wavelength[0, :]), max(wavelength[0, :]))
    ax.set_xticks(np.arange(x_tick_range[0], x_tick_range[1]+1, 250), minor=False)
    ax.set_xticks(np.arange(x_tick_range[0], x_tick_range[1]+1, 50), minor=True)
    ax.set(ylim=(-1000, 150000))

    num_spectra = len(wavelength)
    y_offset = 1000
    ax.set_yticks(np.arange(0, num_spectra * y_offset, 2 * y_offset), minor=False)
    ax.set_yticklabels(np.arange(0, num_spectra, 2), minor=False)

    spec_color = "b" if x_tick_range[0] < 5000 else "r"
    spec_sel = np.where(spec_mask)[0]
    sky_sel = np.where(sky_mask)[0]
    for spec_ix in np.arange(0, num_spectra):
        if spec_ix in spec_sel:
            color = spec_color
        elif spec_ix in sky_sel:
            color = "darkcyan"
        else:
            color = "goldenrod"

        # Optionally, expand the vertical dynamic range before plotting.  Makes features easier to see lne features.
        y_pos = spec_ix * y_offset
        plot_flux = np.power(flux[spec_ix, :].copy(), 2 if enhance else 1)
        ax.plot(wavelength[spec_ix, :], np.add(plot_flux, y_pos), color=color, linestyle="-", linewidth=0.25)
        ax.annotate(f"[{flux_ratios[spec_ix]:.2f}]", xy=(np.min(wavelength) - 50, y_pos), xycoords="data")

    if c_range is not None:
        ax.axvspan(xmin=c_range[0], xmax=c_range[1], color="c", alpha=0.05)
    if h_range is not None:
        ax.axvspan(xmin=h_range[0], xmax=h_range[1], color=spec_color, alpha=0.05)

    plt.savefig(f"{output_dir}/rss_nonss_{basename}.png", dpi=300)
    plt.close()
    return

