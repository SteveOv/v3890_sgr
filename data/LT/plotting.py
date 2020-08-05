from typing import Tuple, List, Union
import warnings
from pathlib import Path
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.ticker import ScalarFormatter
from astropy.units import Quantity
from specutils import SpectralRegion, Spectrum1D, SpectrumCollection


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
    ax.set_title(f"Histogram of the H$\\{'beta' if is_blue else 'alpha'}$/continuum\nflux ratio over the fibre array")
    bin_edges = np.arange(0, 125, 5)
    ax.set_yscale("log")
    ax.yaxis.set_major_formatter(ScalarFormatter())
    ax.set(ylabel="count", xlabel="flux ratio")
    ax.hist(flux_ratios, bins=bin_edges, align="mid", rwidth=0.8, density=False)
    ax.annotate(f"max={max(flux_ratios):.2f}\nmin={min(flux_ratios):.2f}", xy=(0.5, 0.85), xycoords="axes fraction")
    return


def plot_fibre_heatmap_to_ax(fig: Figure, ax: Axes, flux_ratios: [float]):
    c_map = cm.get_cmap("plasma")
    norm = matplotlib.colors.Normalize(vmin=0, vmax=100)
    flux_grid = flux_array_to_square_grid(flux_ratios)
    ax.set_title(f"The heatmap of the flux ratio\nover the FRODOSpec fibre array\n")
    ax.set(xlim=(0, 12), ylim=(0, 12), xticks=[0, 2, 4, 6, 8, 10, 12], xticklabels=[], yticks=[0, 2, 4, 6, 8, 10, 12])
    ax.imshow(flux_grid, cmap=c_map, norm=norm, origin="upper", aspect="equal", extent=(0, 12, 12, 0))
    fig.colorbar(cm.ScalarMappable(cmap=c_map, norm=norm), ax=[ax], orientation="vertical", fraction=0.2, pad=0.15)
    return


def plot_spectrum_to_ax(ax: Axes, spectrum: Spectrum1D, title: str,
                        c_range: SpectralRegion = None, h_range: SpectralRegion = None,
                        sky_flux: [Quantity] = None, nss_spec_flux: [Quantity] = None):
    ax.set_xlabel(f"Wavelength [{spectrum.wavelength.unit}]")
    ax.set_ylabel(f"flux [{spectrum.flux.unit}]")
    ax.set_title(title)
    ax.set_xticks(_calculate_ticks(spectrum.wavelength.value, 250), minor=False)
    ax.set_xticks(_calculate_ticks(spectrum.wavelength.value, 50), minor=True)
    ax.set_xticklabels(ax.get_xticks(minor=False))
    color = "b" if min(ax.get_xticks(minor=True)) < 4500 else "r"

    wavelength = spectrum.wavelength
    ax.plot(wavelength, spectrum.flux, color=color, linestyle="-", linewidth=0.25)

    if nss_spec_flux is not None and len(nss_spec_flux) == len(wavelength):
        ax.plot(wavelength, nss_spec_flux, color="grey", linestyle="-", linewidth=0.25, alpha=0.3)

    if sky_flux is not None and len(sky_flux) == len(wavelength):
        ax.plot(wavelength, sky_flux, color="c", linestyle="-", linewidth=0.25, alpha=0.5)

    if c_range is not None:
        ax.axvspan(xmin=c_range.lower.value, xmax=c_range.upper.value, color="c", alpha=0.05)

    if h_range is not None:
        ax.axvspan(xmin=h_range.lower.value, xmax=h_range.upper.value, color=color, alpha=0.05)
    return


def plot_spectrum(spectrum: Spectrum1D, title: str, filename: Union[str, Path],
                  c_range: SpectralRegion = None, h_range: SpectralRegion = None):
    plt.rc("font", size=8)
    fig = plt.figure(figsize=(6.4, 3.2), constrained_layout=True)
    ax = fig.add_subplot(1, 1, 1)
    plot_spectrum_to_ax(ax, spectrum, title, c_range=c_range, h_range=h_range)
    plt.savefig(filename, dpi=300)
    plt.close()
    return


def plot_rss_spectra(spectra: SpectrumCollection, flux_ratios: [float], basename: str,
                     sky_mask: [bool], spec_mask: [bool], c_range: SpectralRegion, h_range: SpectralRegion,
                     output_dir: Union[str, Path], expand_flux: bool = True):
    fig = plt.figure(figsize=(12.8, 25.6), constrained_layout=True)
    ax = fig.add_subplot(1, 1, 1)
    ax.set_title(f"The RSS_NONSS FRODOSpec spectra in {basename}")
    ax.set_xlabel(f"Wavelength [{spectra.wavelength.unit}]")

    ax.set_xticks(_calculate_ticks(spectra.wavelength.value, 100), minor=False)
    ax.set_xticks(_calculate_ticks(spectra.wavelength.value, 25), minor=True)
    ax.tick_params(axis="x", bottom=True, top=True, labelbottom=True, labeltop=True)
    ax.set(ylim=(-1000, 150000))

    num_spectra = spectra.shape[0]
    y_offset = 1000
    is_blue = spectra.wavelength[0, 0].value < 4500

    note_x_pos = min(ax.get_xticks(minor=False)) - (50 if is_blue else 85)
    ax.set_yticks(np.arange(0, num_spectra * y_offset, 2 * y_offset), minor=False)
    ax.set_yticklabels(np.arange(0, num_spectra, 2), minor=False)

    spec_color = "b" if is_blue else "r"
    spec_sel = np.where(spec_mask)[0]
    sky_sel = np.where(sky_mask)[0]

    flux_expansion = 1
    if expand_flux:
        # Optionally, expand the vertical dynamic range before plotting.  Makes line/continuum features easier to see.
        # We derive an exponent to apply to the data of between 1 & 2 and inversely proportional to the strength of the
        # flux ratios.  Don't use max(flux) here as that would respond to spikes.  Using the ratio is more controlled.
        ratio_key = (np.max(flux_ratios) // 15) / 10
        flux_expansion = np.max([1, 2 - ratio_key])

    y_label = f"flux [{spectra.flux.unit}]"
    y_label += f" (scaled as $y = f_{{\\lambda}}^{{{flux_expansion}}}$)" if flux_expansion != 1 else ""
    print(f"\tplot_rss_spectra: " + y_label)
    ax.set_ylabel(y_label)

    with warnings.catch_warnings():
        # Copy the flux applying any dynamic boost.  numpy warns about the fractional power but still does the job.
        warnings.simplefilter("ignore")
        flux = np.float_power(spectra.flux.value.copy(), flux_expansion)

    for spec_ix in np.arange(0, num_spectra):
        if spec_ix in spec_sel:
            color = spec_color
            width = 0.5
        elif spec_ix in sky_sel:
            color = "darkcyan"
            width = 0.5
        else:
            color = "goldenrod"
            width = 0.25

        # Also apply the vertical offset to distribute the spectra up the page
        y_pos = spec_ix * y_offset
        ax.plot(spectra.wavelength[spec_ix], np.add(flux[spec_ix], y_pos), linestyle="-", color=color, linewidth=width)
        ax.annotate(f"[{flux_ratios[spec_ix]:.2f}]", xy=(note_x_pos, y_pos), xycoords="data")

    if c_range is not None:
        ax.axvspan(xmin=c_range.lower.value, xmax=c_range.upper.value, color="c", alpha=0.05)
    if h_range is not None:
        ax.axvspan(xmin=h_range.lower.value, xmax=h_range.upper.value, color=spec_color, alpha=0.05)

    ax.grid(which="minor", linestyle="-", linewidth=0.25, alpha=0.3)
    ax.grid(which="major", linestyle="-", linewidth=0.25, alpha=0.5)
    plt.savefig(f"{output_dir}/rss_nonss_{basename}.png", dpi=300)
    plt.close()
    return


def _calculate_ticks(data: [float], interval: int) -> [float]:
    flat = data.flatten()
    tick_from = round(min(flat) / interval) * interval
    tick_top = round(max(flat) / interval) * interval
    ticks = np.arange(tick_from, tick_top + 1, interval)
    return ticks
