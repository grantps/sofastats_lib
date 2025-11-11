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
from sofastats.output.charts.utils import (get_axis_lbl_drop, get_height, get_left_margin_offset, get_x_axis_font_size,
                                           get_x_axis_lbls_val_and_text, get_y_axis_title_offset)
from sofastats.output.styles.interfaces import StyleSpec

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
        legend_lbl: str, left_margin_offset_spec: LeftMarginOffsetSpec) -> LineArea.CommonMiscSpec:
    ## calculation
    if isinstance(charting_spec, LineChartingSpec):
        chart_js_fn_name = 'makeLineChart'
    elif isinstance(charting_spec, AreaChartingSpec):
        chart_js_fn_name = 'makeAreaChart'
    else:
        raise TypeError(f"Expected either Line or Area charting spec but got {type(charting_spec)}")
    x_axis_lbls_val_and_text = get_x_axis_lbls_val_and_text(charting_spec.category_specs)
    x_axis_font_size = get_x_axis_font_size(
        n_x_items=charting_spec.n_x_items, is_multi_chart=charting_spec.is_multi_chart)
    if charting_spec.is_time_series:
        x_axis_specs = charting_spec.category_specs
        x_axis_lbls = '[]'
    else:
        x_axis_specs = None
        x_axis_lbls = '[' + ',\n            '.join(x_axis_lbls_val_and_text) + ']'
    y_axis_max = charting_spec.max_y_val * 1.1
    axis_lbl_drop = get_axis_lbl_drop(is_multi_chart=charting_spec.is_multi_chart,
        rotated_x_lbls=charting_spec.rotate_x_lbls,
        max_x_axis_lbl_lines=charting_spec.max_x_axis_lbl_lines)
    axis_lbl_rotate = -90 if charting_spec.rotate_x_lbls else 0
    max_x_lbl_width = (TEXT_WIDTH_WHEN_ROTATED if charting_spec.rotate_x_lbls else charting_spec.max_x_axis_lbl_len)
    horiz_x_lbls = not charting_spec.rotate_x_lbls
    show_major_ticks_only = (False if charting_spec.is_time_series and horiz_x_lbls
        else charting_spec.show_major_ticks_only)  ## override
    width_after_left_margin = LineArea.get_width_after_left_margin(
        is_multi_chart=charting_spec.is_multi_chart, multi_chart_width_factor=0.9,
        n_x_items=charting_spec.n_x_items, n_series=charting_spec.n_series,
        max_x_lbl_width=max_x_lbl_width, is_time_series=charting_spec.is_time_series,
        show_major_ticks_only=show_major_ticks_only, x_axis_title=charting_spec.x_axis_title)
    x_axis_title_len = len(charting_spec.x_axis_title)
    y_axis_title_offset = get_y_axis_title_offset(
        x_axis_title_len=x_axis_title_len, rotated_x_lbls=charting_spec.rotate_x_lbls)
    left_margin_offset = get_left_margin_offset(width_after_left_margin=width_after_left_margin,
        offsets=left_margin_offset_spec, is_multi_chart=charting_spec.is_multi_chart,
        y_axis_title_offset=y_axis_title_offset, rotated_x_lbls=charting_spec.rotate_x_lbls)
    width = left_margin_offset + width_after_left_margin
    height = get_height(axis_lbl_drop=axis_lbl_drop,
        rotated_x_lbls=charting_spec.rotate_x_lbls, max_x_axis_lbl_len=charting_spec.max_x_axis_lbl_len)
    return LineArea.CommonMiscSpec(
        chart_js_fn_name=chart_js_fn_name,
        axis_lbl_drop=axis_lbl_drop,
        axis_lbl_rotate=axis_lbl_rotate,
        connector_style=style_spec.dojo.connector_style,
        grid_line_width=style_spec.chart.grid_line_width,
        height=height,
        left_margin_offset=left_margin_offset,
        legend_lbl=legend_lbl,
        width=width,
        x_axis_font_size=x_axis_font_size,
        x_axis_lbls=x_axis_lbls,
        x_axis_specs=x_axis_specs,
        x_axis_title=charting_spec.x_axis_title,
        y_axis_title=charting_spec.y_axis_title,
        y_axis_max=y_axis_max,
        y_axis_title_offset=y_axis_title_offset,
)
