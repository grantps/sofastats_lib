from collections.abc import Sequence

from sofastats import logger
from sofastats.output.charts import mpl_pngs
from sofastats.output.charts.histogram import HistogramConf
from sofastats.output.styles.interfaces import ChartStyleSpec
from sofastats.output.utils import plot2image_as_data

def get_optimal_min_max(*, axis_min, axis_max) -> tuple[float, float]:
    """
    For boxplots and scatterplots.

    Args:
        axis_min -- the minimum y value exactly
        axis_max -- the maximum y value exactly

    Generally, we want box and scatter plots to have y-axes starting from just below the minimum point
    (e.g. lowest outlier).
    That is, avoid the common case where we have the y-axis start at 0, and all our values range tightly together.
    In which case, for box plots, we will have a series of tiny box plots up the top,
    and we won't be able to see the different parts of it e.g. LQ, median etc.
    For scatter plots our data will be too tightly scrunched up to see any spread.

    But sometimes the lowest point is not that far above 0, in which case we should set it to 0.
    A 0-based axis is preferable unless the values are a long way away. Going from 0.5-12 is silly.
    Might as well go from 0-12.

    4 scenarios:

    1) min and max are both the same
    Just try to set the max differently to the min so there is a range on the axis to display.
    See implementation for more details.

    2) min and max are both +ve
    |   *
    |
    -------
    Snap min to 0 if gap small rel to range, otherwise make min y-axis just below min point.
    Make max y-axis just above the max point.
    Make the padding from 0 the lesser of 0.1 of axis_min and 0.1 of value_range.
    The outer padding can be the lesser of the axis_max and 0.1 of value_range.

    3) min and max are -ve
    -------
    |   *
    |
    Snap max to 0 if gap small rel to range, otherwise make max y-axis just above max point.
    Make min y-axis just below min point.
    Make the padding the lesser of 0.1 of gap and 0.1 of value_range.

    4) min is -ve and max is +ve
    |   *
    -------
    |   *
    Make max 1.1*axis_max. No harm if 0.
    Make min 1.1*axis_min. No harm if 0.
    """
    logger.debug(f"Orig min max: {axis_min} {axis_max}")
    if axis_min == axis_max:
        my_value = axis_min
        if my_value < 0:
            axis_min = 1.1 * my_value
            axis_max = 0
        elif my_value == 0:
            axis_min = -1
            axis_max = 1
        elif my_value > 0:
            axis_min = 0
            axis_max = 1.1 * my_value
    elif axis_min >= 0 and axis_max >= 0:  ## both +ve
        """
        Snap min to 0 if gap small rel to range, otherwise make min y-axis just below min point.
        Make max y-axis just above the max point.
        Make the padding from 0 the lesser of 0.1 of axis_min and 0.1 of value_range.
        The outer padding can be the lesser of the axis_max and 0.1 of value_range.
        """
        gap = axis_min
        value_range = (axis_max - axis_min)
        try:
            gap2range = gap / (value_range * 1.0)
            if gap2range < 0.6:  ## close enough to snap to 0
                axis_min = 0
            else:  ## can't just be 0.9 min - e.g. looking at years from 2000-2010 would be 1800 upwards!
                axis_min -= min(0.1 * gap, 0.1 * value_range)  ## gap is never 0 and is at least 0.6 of value_range
        except ZeroDivisionError:
            pass
        axis_max += min(0.1 * axis_max, 0.1 * value_range)
    elif axis_min <= 0 and axis_max <= 0:  ## both -ve
        """
        Snap max to 0 if gap small rel to range, otherwise make max y-axis just above max point.
        Make min y-axis just below min point. Make the padding the lesser of 0.1 of gap and 0.1 of value_range.
        """
        gap = abs(axis_max)
        value_range = abs(axis_max - axis_min)
        try:
            gap2range = gap / (value_range * 1.0)
            if gap2range < 0.6:
                axis_max = 0
            else:
                axis_max += min(0.1 * gap, 0.1 * value_range)
        except ZeroDivisionError:
            pass
        axis_min -= min(0.1 * abs(axis_min), 0.1 * value_range)  ## make even more negative, but by the least possible
    elif axis_min <= 0 and axis_max >= 0:  ## spanning y-axis (even if all 0s ;-))
        """
        Pad max with 0.1*axis_max. No harm if 0.
        Pad min with 0.1*axis_min. No harm if 0.
        """
        axis_max = 1.1 * axis_max
        axis_min = 1.1 * axis_min
    else:
        pass
    logger.debug(f"Final axis_min: {axis_min}; Final axis_max {axis_max}")
    return axis_min, axis_max

def get_embedded_histogram_html(measure_field_label: str, style_spec: ChartStyleSpec,
        vals: Sequence[float], var_label: str | None = None, *,
        width_scalar: float = 1.0, label_chart_from_var_if_needed=True) -> str:
    """
    Make histogram image and return its HTML (with embedded image).
    """
    first_color_mapping = style_spec.color_mappings[0]
    chart_conf = HistogramConf(
        var_label=measure_field_label,
        chart_label=var_label,
        inner_background_color=style_spec.plot_background_color,
        bar_color=first_color_mapping.main,
        line_color=style_spec.major_grid_line_color,
        label_chart_from_var_if_needed=label_chart_from_var_if_needed)
    fig = mpl_pngs.get_histogram_fig(chart_conf, vals)
    fig.set_size_inches((5.4 * width_scalar, 4))  ## see dpi to get image size in pixels
    image_as_data = plot2image_as_data(fig)
    html = f'<img src="{image_as_data}"/>'
    return html
