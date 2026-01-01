"""
Why making single dispatch for:
* get_common_charting_spec
* get_indiv_chart_html?

Two options:
1) pass to a function which works out type of chart and then, using a switch logic,
calls the specific module and function required for that chart type.
2) pass to a function which will pass to the correct function without a switch logic.
Adding new outputs requires using the singledispatch decorator.
The core code doesn't have to change depending on which charts are available.
I chose option 2). It is a taste issue in this case - either would work.

get_html(charting_spec, style_spec)
"""
from functools import singledispatch

from sofastats.conf.main import TEXT_WIDTH_WHEN_ROTATED
from sofastats.output.charts.interfaces import AreaChartingSpec, LeftMarginOffsetSpec, LineArea, LineChartingSpec
from sofastats.output.charts.utils import (get_axis_label_drop, get_height, get_left_margin_offset, get_x_axis_font_size,
    get_dojo_format_x_axis_numbers_and_labels, get_y_axis_title_offset)
from sofastats.output.styles.interfaces import StyleSpec
from sofastats.utils.misc import get_width_after_left_margin

## https://towardsdatascience.com/simplify-your-functions-with-functools-partial-and-singledispatch-b7071f7543bb
@singledispatch
def get_common_charting_spec(charting_spec, style_spec):
    raise NotImplementedError("Unable to find registered get_common_charting_spec function "
        f"for {type(charting_spec)}")

@singledispatch
def get_indiv_chart_html(common_charting_spec, chart_spec, chart_counter):
    raise NotImplementedError("Unable to find registered get_indiv_chart_html function "
        f"for {type(common_charting_spec)}")

def get_html(charting_spec, style_spec: StyleSpec) -> str:
    common_charting_spec = get_common_charting_spec(charting_spec, style_spec)  ## correct version e.g. from pie module, depending on charting_spec type
    chart_html_strs = []
    for n, chart_spec in enumerate(charting_spec.indiv_chart_specs, 1):
        indiv_chart_html = get_indiv_chart_html(common_charting_spec, chart_spec, chart_counter=n)  ## as above through power of functools.singledispatch
        chart_html_strs.append(indiv_chart_html)
    html = '\n\n'.join(chart_html_strs)
    return html

def get_line_area_misc_spec(charting_spec: LineChartingSpec | AreaChartingSpec, style_spec: StyleSpec,
        series_legend_label: str, left_margin_offset_spec: LeftMarginOffsetSpec) -> LineArea.CommonMiscSpec:
    ## calculation
    if isinstance(charting_spec, LineChartingSpec):
        chart_js_fn_name = 'makeLineChart'
    elif isinstance(charting_spec, AreaChartingSpec):
        chart_js_fn_name = 'makeAreaChart'
    else:
        raise TypeError(f"Expected either Line or Area charting spec but got {type(charting_spec)}")
    dojo_format_x_axis_numbers_and_labels = get_dojo_format_x_axis_numbers_and_labels(charting_spec.categories)
    x_axis_font_size = get_x_axis_font_size(
        n_x_items=charting_spec.n_x_items, is_multi_chart=charting_spec.is_multi_chart)
    if charting_spec.is_time_series:
        x_axis_categories = charting_spec.categories
        dojo_format_x_axis_numbers_and_labels = '[]'
    else:
        x_axis_categories = None
    y_axis_max = charting_spec.max_y_val * 1.1
    axis_label_drop = get_axis_label_drop(is_multi_chart=charting_spec.is_multi_chart,
        rotated_x_labels=charting_spec.rotate_x_labels,
        max_x_axis_label_lines=charting_spec.max_x_axis_label_lines)
    axis_label_rotate = -90 if charting_spec.rotate_x_labels else 0
    max_x_label_width = (
        TEXT_WIDTH_WHEN_ROTATED if charting_spec.rotate_x_labels else charting_spec.max_x_axis_label_len)
    width_after_left_margin = get_width_after_left_margin(
        n_x_items=charting_spec.n_x_items, n_items_horizontally_per_x_item=charting_spec.n_series, min_pixels_per_sub_item=10,
        x_item_padding_pixels=2, sub_item_padding_pixels=5,
        x_axis_title=charting_spec.x_axis_title,
        widest_x_label_n_characters=max_x_label_width, avg_pixels_per_character=8,
        min_chart_width_one_item=200, min_chart_width_multi_item=400,
        is_multi_chart=charting_spec.is_multi_chart, multi_chart_size_scalar=0.9,
        is_time_series=charting_spec.is_time_series, show_major_ticks_only=charting_spec.show_major_ticks_only,
    )
    x_axis_title_len = len(charting_spec.x_axis_title)
    y_axis_title_offset = get_y_axis_title_offset(
        x_axis_title_len=x_axis_title_len, rotated_x_labels=charting_spec.rotate_x_labels)
    left_margin_offset = get_left_margin_offset(width_after_left_margin=width_after_left_margin,
        offsets=left_margin_offset_spec, is_multi_chart=charting_spec.is_multi_chart,
        y_axis_title_offset=y_axis_title_offset, rotated_x_labels=charting_spec.rotate_x_labels)
    width = left_margin_offset + width_after_left_margin
    height = get_height(axis_label_drop=axis_label_drop,
        rotated_x_labels=charting_spec.rotate_x_labels, max_x_axis_label_len=charting_spec.max_x_axis_label_len)
    return LineArea.CommonMiscSpec(
        chart_js_fn_name=chart_js_fn_name,
        axis_label_drop=axis_label_drop,
        axis_label_rotate=axis_label_rotate,
        connector_style=style_spec.dojo.connector_style,
        grid_line_width=style_spec.chart.grid_line_width,
        height=height,
        left_margin_offset=left_margin_offset,
        series_legend_label=series_legend_label,
        width=width,
        x_axis_font_size=x_axis_font_size,
        x_axis_numbers_and_labels=dojo_format_x_axis_numbers_and_labels,
        x_axis_categories=x_axis_categories,
        x_axis_title=charting_spec.x_axis_title,
        y_axis_title=charting_spec.y_axis_title,
        y_axis_max=y_axis_max,
        y_axis_title_offset=y_axis_title_offset,
)
