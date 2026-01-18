"""
https://matplotlib.org/matplotblog/posts/pyplot-vs-object-oriented-interface/
"""
from typing import Sequence

from matplotlib import rcParams as mpl_settings
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

from sofastats import logger
from sofastats.stats_calc.engine import get_normal_ys, get_regression_result
from sofastats.output.charts.histogram import HistogramConf
from sofastats.output.charts.scatter_plot import ScatterplotConf, ScatterplotSeries
from sofastats.stats_calc.histogram import get_bin_details_from_vals

def set_gen_mpl_settings(axes_label_size=14, xtick_label_size=10, ytick_label_size=10):
    mpl_settings['axes.labelsize'] = axes_label_size
    mpl_settings['xtick.labelsize'] = xtick_label_size
    mpl_settings['ytick.labelsize'] = ytick_label_size

def get_histogram_fig(chart_conf: HistogramConf, vals: Sequence[float]) -> Figure:
    """
    Start by getting nice initial bins bounds
    (without looking at the actual individual values and frequencies per bin yet).
    Based entirely on the min and max values.

    Then translate into details needed to actually make histogram esp frequencies per bin.

    Then try to fix any saw-toothing detected if it is possible.
    Requires enough bins to be able to reduce them and recalculate.
    """
    fig, ax = plt.subplots()
    rect = ax.patch
    rect.set_facecolor(chart_conf.inner_background_color)
    bin_spec, bin_freqs = get_bin_details_from_vals(vals)
    ax.set_xlabel(chart_conf.var_label)
    ax.set_ylabel('P')

    if chart_conf.chart_label:
        chart_label = chart_conf.chart_label
    else:
        if chart_conf.label_chart_from_var_if_needed:
            chart_label = f"Histogram for {chart_conf.var_label}"
        else:
            chart_label = None
    if chart_label:
        ax.set_title(chart_label)
    ## see entry for hist in http://matplotlib.sourceforge.net/api/axes_api.html
    ## density=True means the integral of the histogram is 1 (the area = 1)
    ## the wider the bins the smaller the P values
    ## See https://plotly.com/chart-studio-help/histogram/
    ## See also https://matplotlib.org/stable/gallery/statistics/histogram_features.html
    n, bins, patches = ax.hist(vals, bin_spec.n_bins, density=True,
        range=(bin_spec.lower_limit, bin_spec.upper_limit),
        facecolor=chart_conf.bar_color, edgecolor=chart_conf.line_color)
    # ensure enough y-axis to show all of normpdf
    y_min, y_max = ax.get_ylim()
    norm_ys = get_normal_ys(vals, bins)
    logger.debug(norm_ys)
    logger.debug(f"{y_min=}, {y_max=}")
    logger.debug(f'norm max: {max(norm_ys)}; axis max: {y_max}')
    if max(norm_ys) > y_max:
        ax.set_ylim(ymax=1.05 * max(norm_ys))
    ## actually plot norm ys
    ax.plot(bins, norm_ys, color=chart_conf.line_color, linewidth=4)
    logger.debug(f"n={n}, bins={bins}, patches={patches}")
    plt.close(fig)  ## free up the memory
    return fig

def get_scatterplot_fig(vars_series: Sequence[ScatterplotSeries], chart_conf: ScatterplotConf) -> Figure:
    fig, ax = plt.subplots()
    fig.set_size_inches((chart_conf.width_inches, chart_conf.height_inches))
    if chart_conf.x_min is not None and chart_conf.x_max is not None:
        ax.axis(xmin=chart_conf.x_min, xmax=chart_conf.x_max)
    if chart_conf.y_min is not None and chart_conf.y_max is not None:
        ax.axis(ymin=chart_conf.y_min, ymax=chart_conf.y_max)
    ax.set_xlabel(chart_conf.x_axis_label)
    ax.set_ylabel(chart_conf.y_axis_label)
    for var_series in vars_series:
        xs = []
        ys = []
        for coord in var_series.coords:
            xs.append(coord.x)
            ys.append(coord.y)
        dot_line_color = (var_series.dot_line_color if chart_conf.show_dot_lines
            else var_series.dot_color)
        ax.plot(xs, ys, 'o', color=var_series.dot_color, label=var_series.label, markeredgecolor=dot_line_color)
        if var_series.show_regression_details:
            ## Label can't be identical as the points series so add a space.
            ## Will look like correct and matching label without clashing.
            line_label = f"{var_series.label} " if var_series.label else ''
            regression_result = get_regression_result(xs, ys)
            ax.plot([min(xs), max(ys)], [regression_result.y0, regression_result.y1], '-',
                color=var_series.dot_color, linewidth=5, label=line_label)
        ax.annotate(text=f"N={len(xs):,}", xy=(0.02, 0.96), xytext=(0.025, 0.925),
            textcoords='axes fraction', fontsize=7, color=chart_conf.text_color)
    ax.set_facecolor(chart_conf.inner_background_color)
    return fig
