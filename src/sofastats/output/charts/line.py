from collections.abc import Sequence
from dataclasses import dataclass
from statistics import median
import uuid

import jinja2

from sofastats import logger
from sofastats.conf.main import SortOrder
from sofastats.data_extraction.charts.amount_spec_extraction import (
    get_by_category_charting_spec, get_by_chart_category_charting_spec, get_by_chart_series_category_charting_spec,
    get_by_series_category_charting_spec)
from sofastats.data_extraction.charts.misc_interfaces import DataSeriesSpec, IndivChartSpec
from sofastats.output.charts.common import (
    get_common_charting_spec, get_html, get_indiv_chart_html, get_line_area_misc_spec)
from sofastats.output.charts.interfaces import (
    DojoSeriesSpec, JSBool, LeftMarginOffsetSpec, LineArea, LineChartingSpec, PlotStyle)
from sofastats.output.interfaces import (
    DEFAULT_SUPPLIED_BUT_MANDATORY_ANYWAY, HTMLItemSpec, OutputItemType, CommonDesign)
from sofastats.output.styles.interfaces import StyleSpec
from sofastats.output.styles.utils import get_long_colour_list, get_style_spec
from sofastats.utils.maths import format_num
from sofastats.utils.misc import todict

@dataclass(frozen=True)
class CommonColourSpec(LineArea.CommonColourSpec):
    colours: Sequence[str]

@dataclass(frozen=True)
class CommonOptions(LineArea.CommonOptions):
    show_smooth_line: bool
    show_trend_line: bool

@dataclass(frozen=True)
class CommonChartingSpec:
    """
    Ready to combine with individual chart specs
    and feed into the Dojo JS engine.
    """
    colour_spec: CommonColourSpec
    misc_spec: LineArea.CommonMiscSpec
    options: CommonOptions

def get_trend_y_vals(y_vals: Sequence[float]) -> Sequence[float]:
    """
    Returns values to plot a straight line which fits the y_vals provided
    """
    sum_y = sum(y_vals)
    logger.debug(f"sumy={sum_y}")
    n = len(y_vals)
    sum_x = sum(range(1, n + 1))
    logger.debug(f"{sum_x=}")
    sum_xy = 0
    sum_x2 = 0
    for x, y_val in enumerate(y_vals, 1):
        sum_xy += x * y_val
        sum_x2 += x ** 2
    logger.debug(f"{sum_xy}")
    logger.debug(f"{sum_x2=}")
    b_num = (n * sum_xy) - (sum_x * sum_y)
    logger.debug(f"b_num={b_num}")
    b_denom = (n * sum_x2) - (sum_x ** 2)
    logger.debug(f"b_denom={b_denom}")
    b = b_num / (1.0 * b_denom)
    a = (sum_y - (sum_x * b)) / (1.0 * n)
    trend_y_vals = []
    for x in range(1, n + 1):
        trend_y_vals.append(a + b * x)
    return trend_y_vals

def get_smooth_y_vals(y_vals: Sequence[float]) -> Sequence[float]:
    """
    Returns values to plot a smoothed line which fits the y_vals provided.
    """
    smooth_y_vals = []
    for i, y_val in enumerate(y_vals):
        if 1 < i < len(y_vals) - 2:
            smooth_y_vals.append(median(y_vals[i - 2: i + 3]))
        elif i in (1, len(y_vals) - 2):
            smooth_y_vals.append(median(y_vals[i - 1: i + 2]))
        elif i == 0:
            smooth_y_vals.append((2 * y_val + y_vals[i + 1]) / 3)
        elif i == len(y_vals) - 1:
            smooth_y_vals.append((2 * y_val + y_vals[i - 1]) / 3)
    return smooth_y_vals

def get_dojo_trend_series_spec(common_charting_spec: CommonChartingSpec,
        single_data_series_spec: DataSeriesSpec) -> DojoSeriesSpec:
    """
    For time-series lines we're using coordinates so can just have the end points
    e.g. [all[0], all[-1]]
    The non-time series lines need one value per x-axis detail
    otherwise the line only goes from the first to the second x-value.

    id is 01 because only a single other series and that will be 00
    smooth will be 02
    OK if we have one or the other of smooth and trend (or neither)
    as long as they are distinct
    """
    orig_y_vals = single_data_series_spec.amounts
    trend_y_vals = get_trend_y_vals(orig_y_vals)
    trend_series_id = '01'
    trend_series_label = 'Trend line'
    trend_line_colour = common_charting_spec.colour_spec.colours[1]  ## obviously don't conflict with main series colour or possible smooth line colour
    if common_charting_spec.options.is_time_series:
        trend_series_x_axis_vals = [common_charting_spec.misc_spec.x_axis_categories[0]]
        trend_series_y_vals = [trend_y_vals[0], trend_y_vals[-1]]
        trend_series_vals = LineArea.get_time_series_vals(
            trend_series_x_axis_vals, trend_series_y_vals, common_charting_spec.misc_spec.x_axis_title)
        marker_plot_style = PlotStyle.DEFAULT if common_charting_spec.options.show_markers else PlotStyle.UNMARKED
    else:
        trend_series_vals = trend_y_vals  ## need
        marker_plot_style = PlotStyle.UNMARKED
    trend_options = (f"""{{stroke: {{color: "{trend_line_colour}", width: "6px"}}, """
        f"""yLbls: {LineArea.DUMMY_TOOL_TIPS}, plot: "{marker_plot_style}"}}""")
    trend_series_spec = DojoSeriesSpec(trend_series_id, trend_series_label, trend_series_vals, trend_options)
    return trend_series_spec

def get_dojo_smooth_series_spec(common_charting_spec: CommonChartingSpec,
        single_data_series_spec: DataSeriesSpec) -> DojoSeriesSpec:
    """
    id is 02 because only a single other series and that will be 00
    trend will be 01
    OK if we have one or the other of smooth and trend (or neither)
    as long as they are distinct
    """
    orig_y_vals = single_data_series_spec.amounts
    smooth_y_vals = get_smooth_y_vals(orig_y_vals)
    smooth_series_id = '02'
    smooth_series_label = 'Smooth line'
    smooth_line_colour = common_charting_spec.colour_spec.colours[2]  ## obviously don't conflict with main series colour or possible trend line colour
    smooth_options = (f"""{{stroke: {{color: "{smooth_line_colour}", width: "6px"}}, """
        f"""yLbls: {LineArea.DUMMY_TOOL_TIPS}, plot: "{PlotStyle.CURVED}"}}""")
    if common_charting_spec.options.is_time_series:
        smooth_series_vals = LineArea.get_time_series_vals(
            common_charting_spec.misc_spec.x_axis_categories,
            smooth_y_vals, common_charting_spec.misc_spec.x_axis_title)
    else:
        smooth_series_vals = smooth_y_vals
    smooth_series_spec = DojoSeriesSpec(smooth_series_id, smooth_series_label, smooth_series_vals, smooth_options)
    return smooth_series_spec

@get_common_charting_spec.register
def get_common_charting_spec(charting_spec: LineChartingSpec, style_spec: StyleSpec) -> CommonChartingSpec:
    ## colours
    colour_mappings = style_spec.chart.colour_mappings
    if charting_spec.is_single_series:
        colour_mappings = colour_mappings[:3]  ## only need the first 1-3 depending on whether trend and smoothed lines
    colours = get_long_colour_list(colour_mappings)
    ## misc
    has_minor_ticks_js_bool: JSBool = ('true' if charting_spec.n_x_items >= LineArea.DOJO_MINOR_TICKS_NEEDED_PER_X_ITEM
        else 'false')
    has_micro_ticks_js_bool: JSBool = ('true' if charting_spec.n_x_items > LineArea.DOJO_MICRO_TICKS_NEEDED_PER_X_ITEM
        else 'false')
    is_time_series_js_bool: JSBool = 'true' if charting_spec.is_time_series else 'false'
    if charting_spec.is_single_series and not (charting_spec.show_smooth_line or charting_spec.show_trend_line):
        series_legend_label = ''
    else:
        series_legend_label = charting_spec.series_legend_label
    left_margin_offset_spec = LeftMarginOffsetSpec(
        initial_offset=18, wide_offset=25, rotate_offset=4, multi_chart_offset=10)
    colour_spec = CommonColourSpec(
        axis_font=style_spec.chart.axis_font_colour,
        chart_bg=style_spec.chart.chart_bg_colour,
        colours=colours,
        major_grid_line=style_spec.chart.major_grid_line_colour,
        plot_bg=style_spec.chart.plot_bg_colour,
        plot_font=style_spec.chart.plot_font_colour,
        plot_font_filled=style_spec.chart.plot_font_colour_filled,
        tooltip_border=style_spec.chart.tooltip_border_colour,
    )
    misc_spec = get_line_area_misc_spec(charting_spec, style_spec, series_legend_label, left_margin_offset_spec)
    options = CommonOptions(
        has_micro_ticks_js_bool=has_micro_ticks_js_bool,
        has_minor_ticks_js_bool=has_minor_ticks_js_bool,
        is_multi_chart=charting_spec.is_multi_chart,
        is_single_series=charting_spec.is_single_series,
        is_time_series=charting_spec.is_time_series,
        is_time_series_js_bool=is_time_series_js_bool,
        show_n_records=charting_spec.show_n_records,
        show_smooth_line=charting_spec.show_smooth_line,
        show_trend_line=charting_spec.show_trend_line,
        show_markers=charting_spec.show_markers,
    )
    return CommonChartingSpec(
        colour_spec=colour_spec,
        misc_spec=misc_spec,
        options=options,
    )

@get_indiv_chart_html.register
def get_indiv_chart_html(common_charting_spec: CommonChartingSpec, indiv_chart_spec: IndivChartSpec,
        *,  chart_counter: int) -> str:
    context = todict(common_charting_spec.colour_spec, shallow=True)
    context.update(todict(common_charting_spec.misc_spec, shallow=True))
    context.update(todict(common_charting_spec.options, shallow=True))
    chart_uuid = str(uuid.uuid4()).replace('-', '_')  ## needs to work in JS variable names
    page_break = 'page-break-after: always;' if chart_counter % 2 == 0 else ''
    indiv_title_html = (f"<p><b>{indiv_chart_spec.label}</b></p>" if common_charting_spec.options.is_multi_chart else '')
    n_records = 'N = ' + format_num(indiv_chart_spec.n_records) if common_charting_spec.options.show_n_records else ''
    ## each standard series
    dojo_series_specs = []
    marker_plot_style = PlotStyle.DEFAULT if common_charting_spec.options.show_markers else PlotStyle.UNMARKED
    for i, data_series_spec in enumerate(indiv_chart_spec.data_series_specs):
        series_id = f"{i:>02}"
        series_label = data_series_spec.label
        if common_charting_spec.options.is_time_series:
            series_vals = LineArea.get_time_series_vals(
                common_charting_spec.misc_spec.x_axis_categories, data_series_spec.amounts,
                common_charting_spec.misc_spec.x_axis_title)
        else:
            series_vals = str(data_series_spec.amounts)
        ## options
        ## e.g. {stroke: {color: '#e95f29', width: '6px'}, yLbls: ['x-val: 2016-01-01<br>y-val: 12<br>0.8%', ... ], plot: 'default'};
        line_colour = common_charting_spec.colour_spec.colours[i]
        y_lbls_str = str(data_series_spec.tool_tips)
        options = (f"""{{stroke: {{color: "{line_colour}", width: "6px"}}, """
            f"""yLbls: {y_lbls_str}, plot: "{marker_plot_style}"}}""")
        dojo_series_specs.append(DojoSeriesSpec(series_id, series_label, series_vals, options))
    ## trend and smooth series (if appropriate)
    single_data_series_spec = indiv_chart_spec.data_series_specs[0]
    if common_charting_spec.options.show_trend_line:
        if not common_charting_spec.options.is_single_series:
            raise Exception("Can only show trend lines if one series of results.")
        trend_series_spec = get_dojo_trend_series_spec(
            common_charting_spec, single_data_series_spec=single_data_series_spec)
        dojo_series_specs.append(trend_series_spec)  ## seems that the later you add something the lower it is
    if common_charting_spec.options.show_smooth_line:
        if not common_charting_spec.options.is_single_series:
            raise Exception("Can only show trend lines if one series of results.")
        smooth_series_spec = get_dojo_smooth_series_spec(
            common_charting_spec, single_data_series_spec=single_data_series_spec
        )
        dojo_series_specs.append(smooth_series_spec)
    indiv_context = {
        'chart_uuid': chart_uuid,
        'dojo_series_specs': dojo_series_specs,
        'indiv_title_html': indiv_title_html,
        'n_records': n_records,
        'page_break': page_break,
    }
    context.update(indiv_context)
    environment = jinja2.Environment()
    template = environment.from_string(LineArea.tpl_chart)
    html_result = template.render(context)
    return html_result


@dataclass(frozen=False)
class LineChartDesign(CommonDesign):
    style_name: str = 'default'

    category_field_name: str = DEFAULT_SUPPLIED_BUT_MANDATORY_ANYWAY
    category_sort_order: SortOrder = SortOrder.VALUE

    is_time_series: bool = False
    show_major_ticks_only: bool = True
    show_markers: bool = True
    show_smooth_line: bool = False
    show_trend_line: bool = False
    rotate_x_labels: bool = False
    show_n_records: bool = True
    x_axis_font_size: int = 12
    y_axis_title: str = 'Freq'

    def to_html_design(self) -> HTMLItemSpec:
        # style
        style_spec = get_style_spec(style_name=self.style_name)
        ## data
        intermediate_charting_spec = get_by_category_charting_spec(
            cur=self.cur, dbe_spec=self.dbe_spec, src_tbl_name=self.source_table_name,
            category_field_name=self.category_field_name,
            sort_orders=self.sort_orders,
            category_sort_order=self.category_sort_order,
            tbl_filt_clause=self.table_filter)
        ## chart details
        charting_spec = LineChartingSpec(
            categories=intermediate_charting_spec.sorted_categories,
            indiv_chart_specs=[intermediate_charting_spec.to_indiv_chart_spec(), ],
            series_legend_label=None,
            rotate_x_labels=self.rotate_x_labels,
            show_n_records=self.show_n_records,
            is_time_series=self.is_time_series,
            show_major_ticks_only=self.show_major_ticks_only,
            show_markers=self.show_markers,
            show_smooth_line=self.show_smooth_line,
            show_trend_line=self.show_trend_line,
            x_axis_font_size=self.x_axis_font_size,
            x_axis_title=intermediate_charting_spec.category_field_name,
            y_axis_title=self.y_axis_title,
        )
        ## output
        html = get_html(charting_spec, style_spec)
        return HTMLItemSpec(
            html_item_str=html,
            style_name=self.style_name,
            output_item_type=OutputItemType.CHART,
        )


@dataclass(frozen=False)
class MultiLineChartDesign(CommonDesign):
    style_name: str = 'default'

    category_field_name: str = DEFAULT_SUPPLIED_BUT_MANDATORY_ANYWAY
    category_sort_order: SortOrder = SortOrder.VALUE
    series_field_name: str = DEFAULT_SUPPLIED_BUT_MANDATORY_ANYWAY
    series_sort_order: SortOrder = SortOrder.VALUE

    is_time_series: bool = False
    show_major_ticks_only: bool = True
    show_markers: bool = True
    show_smooth_line: bool = False
    show_trend_line: bool = False
    rotate_x_labels: bool = False
    show_n_records: bool = True
    x_axis_font_size: int = 12
    y_axis_title: str = 'Freq'

    def to_html_design(self) -> HTMLItemSpec:
        # style
        style_spec = get_style_spec(style_name=self.style_name)
        ## data
        intermediate_charting_spec = get_by_series_category_charting_spec(
            cur=self.cur, dbe_spec=self.dbe_spec, src_tbl_name=self.source_table_name,
            category_field_name=self.category_field_name, series_field_name=self.series_field_name,
            sort_orders=self.sort_orders,
            category_sort_order=self.category_sort_order, series_sort_order=self.series_sort_order,
            tbl_filt_clause=self.table_filter)
        ## chart details
        charting_spec = LineChartingSpec(
            categories=intermediate_charting_spec.sorted_categories,
            indiv_chart_specs=[intermediate_charting_spec.to_indiv_chart_spec(), ],
            series_legend_label=intermediate_charting_spec.series_field_name,
            rotate_x_labels=self.rotate_x_labels,
            show_n_records=self.show_n_records,
            is_time_series=self.is_time_series,
            show_major_ticks_only=self.show_major_ticks_only,
            show_markers=self.show_markers,
            show_smooth_line=self.show_smooth_line,
            show_trend_line=self.show_trend_line,
            x_axis_font_size=self.x_axis_font_size,
            x_axis_title=intermediate_charting_spec.category_field_name,
            y_axis_title=self.y_axis_title,
        )
        ## output
        html = get_html(charting_spec, style_spec)
        return HTMLItemSpec(
            html_item_str=html,
            style_name=self.style_name,
            output_item_type=OutputItemType.CHART,
        )


@dataclass(frozen=False)
class MultiChartLineChartDesign(CommonDesign):
    style_name: str = 'default'

    category_field_name: str = DEFAULT_SUPPLIED_BUT_MANDATORY_ANYWAY
    category_sort_order: SortOrder = SortOrder.VALUE
    chart_field_name: str = DEFAULT_SUPPLIED_BUT_MANDATORY_ANYWAY
    chart_sort_order: SortOrder = SortOrder.VALUE

    is_time_series: bool = False
    show_major_ticks_only: bool = True
    show_markers: bool = True
    show_smooth_line: bool = False
    show_trend_line: bool = False
    rotate_x_labels: bool = False
    show_n_records: bool = True
    x_axis_font_size: int = 12
    y_axis_title: str = 'Freq'

    def to_html_design(self) -> HTMLItemSpec:
        # style
        style_spec = get_style_spec(style_name=self.style_name)
        ## data
        intermediate_charting_spec = get_by_chart_category_charting_spec(
            cur=self.cur, dbe_spec=self.dbe_spec, src_tbl_name=self.source_table_name,
            category_field_name=self.category_field_name,
            chart_field_name=self.chart_field_name,
            sort_orders=self.sort_orders,
            category_sort_order=self.category_sort_order,
            chart_sort_order=self.chart_sort_order,
            tbl_filt_clause=self.table_filter)
        ## chart details
        charting_spec = LineChartingSpec(
            categories=intermediate_charting_spec.sorted_categories,
            indiv_chart_specs=intermediate_charting_spec.to_indiv_chart_specs(),
            series_legend_label=None,
            rotate_x_labels=self.rotate_x_labels,
            show_n_records=self.show_n_records,
            is_time_series=self.is_time_series,
            show_major_ticks_only=self.show_major_ticks_only,
            show_markers=self.show_markers,
            show_smooth_line=self.show_smooth_line,
            show_trend_line=self.show_trend_line,
            x_axis_font_size=self.x_axis_font_size,
            x_axis_title=intermediate_charting_spec.category_field_name,
            y_axis_title=self.y_axis_title,
        )
        ## output
        html = get_html(charting_spec, style_spec)
        return HTMLItemSpec(
            html_item_str=html,
            style_name=self.style_name,
            output_item_type=OutputItemType.CHART,
        )


@dataclass(frozen=False)
class MultiChartMultiLineChartDesign(CommonDesign):
    style_name: str = 'default'

    category_field_name: str = DEFAULT_SUPPLIED_BUT_MANDATORY_ANYWAY
    category_sort_order: SortOrder = SortOrder.VALUE
    series_field_name: str = DEFAULT_SUPPLIED_BUT_MANDATORY_ANYWAY
    series_sort_order: SortOrder = SortOrder.VALUE
    chart_field_name: str = DEFAULT_SUPPLIED_BUT_MANDATORY_ANYWAY
    chart_sort_order: SortOrder = SortOrder.VALUE

    is_time_series: bool = False
    show_major_ticks_only: bool = True
    show_markers: bool = True
    show_smooth_line: bool = False
    show_trend_line: bool = False
    rotate_x_labels: bool = False
    show_n_records: bool = True
    x_axis_font_size: int = 12
    y_axis_title: str = 'Freq'

    def to_html_design(self) -> HTMLItemSpec:
        # style
        style_spec = get_style_spec(style_name=self.style_name)
        ## data
        intermediate_charting_spec = get_by_chart_series_category_charting_spec(
            cur=self.cur, dbe_spec=self.dbe_spec, src_tbl_name=self.source_table_name,
            category_field_name=self.category_field_name,
            series_field_name=self.series_field_name,
            chart_field_name=self.chart_field_name,
            sort_orders=self.sort_orders,
            category_sort_order=self.category_sort_order,
            series_sort_order=self.series_sort_order,
            chart_sort_order=self.chart_sort_order,
            tbl_filt_clause=self.table_filter)
        ## chart details
        charting_spec = LineChartingSpec(
            categories=intermediate_charting_spec.sorted_categories,
            indiv_chart_specs=intermediate_charting_spec.to_indiv_chart_specs(),
            series_legend_label=intermediate_charting_spec.series_field_name,
            rotate_x_labels=self.rotate_x_labels,
            show_n_records=self.show_n_records,
            is_time_series=self.is_time_series,
            show_major_ticks_only=self.show_major_ticks_only,
            show_markers=self.show_markers,
            show_smooth_line=self.show_smooth_line,
            show_trend_line=self.show_trend_line,
            x_axis_font_size=self.x_axis_font_size,
            x_axis_title=intermediate_charting_spec.category_field_name,
            y_axis_title=self.y_axis_title,
        )
        ## output
        html = get_html(charting_spec, style_spec)
        return HTMLItemSpec(
            html_item_str=html,
            style_name=self.style_name,
            output_item_type=OutputItemType.CHART,
        )
