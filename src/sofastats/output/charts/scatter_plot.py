from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal
import uuid

import jinja2

from sofastats.conf.main import SortOrder
from sofastats.data_extraction.charts.scatter_plot import ScatterChartingSpec, ScatterIndivChartSpec
from sofastats.data_extraction.charts.interfaces.xy import (
    get_by_chart_series_xy_charting_spec, get_by_chart_xy_charting_spec,
    get_by_series_xy_charting_spec, get_by_xy_charting_spec)
from sofastats.output.charts.common import (
    get_common_charting_spec, get_html, get_indiv_chart_html, get_indiv_chart_title_html)
from sofastats.output.charts.interfaces import JSBool
from sofastats.output.charts.utils import  get_intrusion_of_first_x_axis_label_leftwards, get_y_axis_title_offset
from sofastats.output.interfaces import (
    DEFAULT_SUPPLIED_BUT_MANDATORY_ANYWAY, HTMLItemSpec, OutputItemType, CommonDesign)
from sofastats.output.stats.interfaces import Coord
from sofastats.output.styles.interfaces import ColorWithHighlight, StyleSpec
from sofastats.output.styles.utils import (
    fix_default_single_color_mapping, get_js_highlighting_function, get_long_color_list, get_style_spec)
from sofastats.utils.maths import format_num
from sofastats.utils.misc import todict

@dataclass(frozen=True)
class ScatterplotSeries:
    coords: Sequence[Coord]
    dot_color: str
    label: str = ''  ## series label - only relevant if showing multiple series
    dot_line_color: str | None = None
    show_regression_details: bool = False

@dataclass(frozen=True, kw_only=True)
class ScatterplotConf:
    width_inches: float
    height_inches: float
    inner_background_color: str
    text_color: str
    x_axis_label: str
    y_axis_label: str
    show_dot_lines: bool = False
    x_min: float | None = None  ## if not set pylab will automatically set chart bounds
    x_max: float | None = None
    y_min: float | None = None
    y_max: float | None = None

@dataclass(frozen=True)
class ScatterplotDojoSeriesSpec:
    """
    Used for DOJO scatter plots (which have series).

    Box plots, and more general charts with series (e.g. bar charts and line charts),
    have different specs of their own for DOJO series.
    """
    series_id: str  ## e.g. 01
    label: str
    xy_pairs: str  ## e.g. [(1.2, 2.0), ...]
    options: str  ## e.g. stroke, color, width etc. - things needed in a generic DOJO series

@dataclass(frozen=False)
class CommonColorSpec:
    axis_font: str
    chart_background: str
    chart_title_font: str
    color_mappings: Sequence[ColorWithHighlight]
    major_grid_line: str
    plot_background: str
    plot_font: str
    tool_tip_border: str

    @property
    def colors(self):
        return get_long_color_list(self.color_mappings)

@dataclass(frozen=True)
class CommonOptions:
    has_minor_ticks_js_bool: Literal['true', 'false']
    is_multi_chart: bool
    show_dot_borders: bool
    show_n_records: bool
    show_regression_line_js_bool: Literal['true', 'false']

@dataclass(frozen=True)
class CommonMiscSpec:
    axis_label_drop: int
    connector_style: str
    grid_line_width: int
    height: float  ## pixels
    left_margin_offset: float
    series_legend_label: str
    stroke_width: int
    width: float  ## pixels
    x_axis_font_size: float
    x_axis_max_val: int
    x_axis_min_val: int
    x_axis_title: str
    y_axis_max_val: float
    y_axis_min_val: float
    y_axis_title: str
    y_axis_title_offset: int

@dataclass(frozen=True)
class CommonChartingSpec:
    """
    Ready to combine with individual chart spec and feed into the Dojo JS engine.
    """
    color_spec: CommonColorSpec
    misc_spec: CommonMiscSpec
    options: CommonOptions

tpl_chart = """\
<script type="text/javascript">

{{js_highlighting_function}}

make_chart_{{chart_uuid}} = function(){

    var series = new Array();
    {% for series_spec in dojo_series_specs %}
      var series_{{series_spec.series_id}} = new Array();
          series_{{series_spec.series_id}}["label"] = "{{series_spec.label}}";
          series_{{series_spec.series_id}}["xy_pairs"] = {{series_spec.xy_pairs}};
          // options - stroke_width_to_use, fill_colour
          series_{{series_spec.series_id}}["options"] = {{series_spec.options}};
      series.push(series_{{series_spec.series_id}});
    {% endfor %}

    var conf = new Array();
        conf["axis_font_color"] = "{{axis_font}}";
        conf["axis_label_drop"] = {{axis_label_drop}};
        conf["chart_background_color"] = "{{chart_background}}";
        conf["connector_style"] = "{{connector_style}}";
        conf["grid_line_width"] = {{grid_line_width}};
        conf["has_minor_ticks"] = {{has_minor_ticks_js_bool}};
        conf["highlight"] = highlight_{{chart_uuid}};
        conf["left_margin_offset"] = {{left_margin_offset}};
        conf["major_grid_line_color"] = "{{major_grid_line}}";
        conf["n_records"] = "{{n_records}}";
        conf["plot_background_color"] = "{{plot_background}}";
        conf["plot_font_color"] = "{{plot_font}}";
        conf["show_regression_line"] = {{show_regression_line_js_bool}};
        conf["tool_tip_border_color"] = "{{tool_tip_border}}";
        conf["x_axis_font_size"] = {{x_axis_font_size}};
        conf["x_axis_max_val"] = {{x_axis_max_val}};
        conf["x_axis_min_val"] = {{x_axis_min_val}};
        conf["x_axis_title"] = "{{x_axis_title}}";
        conf["y_axis_max_val"] = {{y_axis_max_val}};
        conf["y_axis_min_val"] = {{y_axis_min_val}};
        conf["y_axis_title"] = "{{y_axis_title}}";
        conf["y_axis_title_offset"] = {{y_axis_title_offset}};

    makeScatterplot("scatterplot_{{chart_uuid}}", series, conf);
}
</script>

<div class="screen-float-only" style="margin-right: 10px; {{page_break}}">
{{indiv_title_html}}
    <div id="scatterplot_{{chart_uuid}}"
        style="width: {{width}}px; height: {{height}}px;">
    </div>
    {% if series_legend_label %}
        <p style="float: left; font-weight: bold; margin-right: 12px; margin-top: 9px;">
            {{series_legend_label}}:
        </p>
        <div id="legend_for_scatterplot_{{chart_uuid}}">
        </div>
    {% endif %}
</div>
"""

@get_common_charting_spec.register
def get_common_charting_spec(charting_spec: ScatterChartingSpec, style_spec: StyleSpec) -> CommonChartingSpec:
    ## colours
    color_mappings = style_spec.chart.color_mappings
    if charting_spec.is_single_series:
        color_mappings = fix_default_single_color_mapping(color_mappings)
    ## misc
    has_minor_ticks_js_bool: JSBool = 'true' if charting_spec.has_minor_ticks else 'false'
    stroke_width = style_spec.chart.stroke_width if charting_spec.show_dot_borders else 0
    show_regression_line_js_bool: JSBool = 'true' if charting_spec.show_regression_line else 'false'
    ## sizing
    if charting_spec.is_multi_chart:
        width, height = (630, 350)
    else:
        width, height = (700, 385)
    ## y-axis offset
    y_axis_max = charting_spec.y_axis_max_val * 1.1
    widest_y_axis_label_n_characters = len(str(int(y_axis_max)))  ## e.g. 1000.5 -> 1000 -> '1000' -> 4
    y_axis_title_offset = get_y_axis_title_offset(
        widest_y_axis_label_n_characters=widest_y_axis_label_n_characters, avg_pixels_per_y_character=8)
    intrusion_of_first_x_axis_label_leftwards = get_intrusion_of_first_x_axis_label_leftwards(
        widest_x_axis_label_n_characters=4, avg_pixels_per_x_character=5)
    left_margin_offset = max(y_axis_title_offset, intrusion_of_first_x_axis_label_leftwards) - 25
    ## sizing left margin offset

    color_spec = CommonColorSpec(
        axis_font=style_spec.chart.axis_font_color,
        chart_background=style_spec.chart.chart_background_color,
        chart_title_font=style_spec.chart.chart_title_font_color,
        color_mappings=color_mappings,
        major_grid_line=style_spec.chart.major_grid_line_color,
        plot_background=style_spec.chart.plot_background_color,
        plot_font=style_spec.chart.plot_font_color,
        tool_tip_border=style_spec.chart.tool_tip_border_color,
    )
    misc_spec = CommonMiscSpec(
        axis_label_drop=10,
        connector_style=style_spec.dojo.connector_style,
        grid_line_width=style_spec.chart.grid_line_width,
        height=height,
        left_margin_offset=left_margin_offset,
        series_legend_label=charting_spec.series_legend_label,
        stroke_width=stroke_width,
        width=width,
        x_axis_font_size=charting_spec.x_axis_font_size,
        x_axis_max_val=charting_spec.x_axis_max_val,
        x_axis_min_val=charting_spec.x_axis_min_val,
        x_axis_title=charting_spec.x_axis_title,
        y_axis_max_val=charting_spec.y_axis_max_val,
        y_axis_min_val=charting_spec.y_axis_min_val,
        y_axis_title=charting_spec.y_axis_title,
        y_axis_title_offset=y_axis_title_offset,
    )
    options = CommonOptions(
        has_minor_ticks_js_bool=has_minor_ticks_js_bool,
        is_multi_chart=charting_spec.is_multi_chart,
        show_dot_borders=charting_spec.show_dot_borders,
        show_n_records=charting_spec.show_n_records,
        show_regression_line_js_bool=show_regression_line_js_bool,
    )
    return CommonChartingSpec(
        color_spec=color_spec,
        misc_spec=misc_spec,
        options=options,
    )

@get_indiv_chart_html.register
def get_indiv_chart_html(common_charting_spec: CommonChartingSpec, indiv_chart_spec: ScatterIndivChartSpec,
        *,  chart_counter: int) -> str:
    context = todict(common_charting_spec.color_spec, shallow=True)
    context.update(todict(common_charting_spec.misc_spec, shallow=True))
    context.update(todict(common_charting_spec.options, shallow=True))
    chart_uuid = str(uuid.uuid4()).replace('-', '_')  ## needs to work in JS variable names
    page_break = 'page-break-after: always;' if chart_counter % 2 == 0 else ''
    title = indiv_chart_spec.label
    font_color = common_charting_spec.color_spec.chart_title_font
    indiv_title_html = (get_indiv_chart_title_html(chart_title=title, color=font_color)
        if common_charting_spec.options.is_multi_chart else '')
    n_records = 'N = ' + format_num(indiv_chart_spec.n_records) if common_charting_spec.options.show_n_records else ''
    dojo_series_specs = []
    for i, data_series_spec in enumerate(indiv_chart_spec.data_series_specs):
        series_id = f"{i:>02}"
        series_label = data_series_spec.label
        xy_dicts = [f"{{x: {x}, y: {y}}}" for x, y in data_series_spec.xy_pairs]
        series_xy_pairs = '[' + ', '.join(xy_dicts) + ']'
        fill_color = common_charting_spec.color_spec.colors[i]
        options = (
            f"""{{stroke: {{color: "white", width: "{common_charting_spec.misc_spec.stroke_width}px"}}, """
            f"""fill: "{fill_color}", marker: "m-6,0 c0,-8 12,-8 12,0 m-12,0 c0,8 12,8 12,0"}}""")
        dojo_series_specs.append(ScatterplotDojoSeriesSpec(series_id, series_label, series_xy_pairs, options))
    js_highlighting_function = get_js_highlighting_function(
        color_mappings=common_charting_spec.color_spec.color_mappings, chart_uuid=chart_uuid)
    indiv_context = {
        'chart_uuid': chart_uuid,
        'dojo_series_specs': dojo_series_specs,
        'indiv_title_html': indiv_title_html,
        'js_highlighting_function': js_highlighting_function,
        'n_records': n_records,
        'page_break': page_break,
    }
    context.update(indiv_context)
    environment = jinja2.Environment()
    template = environment.from_string(tpl_chart)
    html_result = template.render(context)
    return html_result


@dataclass(frozen=False)
class SimpleScatterChartDesign(CommonDesign):
    """
    Args:
        x_field_name: field defining the x value of each x-y pair
        y_field_name: field defining the y value of each x-y pair
        show_dot_borders: if `Tue` show borders around individual dots
        show_n_records: show the number of records the chart is based on
        show_regression_line: if `True` show regression line of best fit
        x_axis_font_size: font size for x-axis labels
    """
    x_field_name: str = DEFAULT_SUPPLIED_BUT_MANDATORY_ANYWAY
    y_field_name: str = DEFAULT_SUPPLIED_BUT_MANDATORY_ANYWAY

    show_dot_borders: bool = True
    show_n_records: bool = True
    show_regression_line: bool = True
    x_axis_font_size: int = 10

    def to_html_design(self) -> HTMLItemSpec:
        # style
        style_spec = get_style_spec(style_name=self.style_name)
        ## data
        intermediate_charting_spec = get_by_xy_charting_spec(
            cur=self.cur, dbe_spec=self.dbe_spec, source_table_name=self.source_table_name,
            x_field_name=self.x_field_name, y_field_name=self.y_field_name,
            table_filter_sql=self.table_filter_sql)
        ## charts details
        indiv_chart_specs = intermediate_charting_spec.to_indiv_chart_specs()
        charting_spec = ScatterChartingSpec(
            indiv_chart_specs=indiv_chart_specs,
            series_legend_label=None,
            show_dot_borders=self.show_dot_borders,
            show_n_records=self.show_n_records,
            show_regression_line=self.show_regression_line,
            x_axis_font_size=self.x_axis_font_size,
            x_axis_title=intermediate_charting_spec.x_field_name,
            y_axis_title=intermediate_charting_spec.y_field_name,
        )
        ## output
        html = get_html(charting_spec, style_spec)
        return HTMLItemSpec(
            html_item_str=html,
            output_item_type=OutputItemType.CHART,
            output_title=self.output_title,
            design_name=self.__class__.__name__,
            style_name=self.style_name,
        )


@dataclass(frozen=False)
class BySeriesScatterChartDesign(CommonDesign):
    """
    Args:
        series_field_name: the field name defining the series e.g. a `series_field_name` of 'Country'
            might separate generate different colour dots for 'USA', 'NZ', 'Denmark', and 'South Korea'.
        series_sort_order: define order of series in the legend e.g. `SortOrder.VALUES` or `SortOrder.CUSTOM`
    """
    x_field_name: str = DEFAULT_SUPPLIED_BUT_MANDATORY_ANYWAY
    y_field_name: str = DEFAULT_SUPPLIED_BUT_MANDATORY_ANYWAY
    series_field_name: str = DEFAULT_SUPPLIED_BUT_MANDATORY_ANYWAY
    series_sort_order: SortOrder = SortOrder.VALUE

    show_dot_borders: bool = True
    show_n_records: bool = True
    show_regression_line: bool = True
    x_axis_font_size: int = 10

    def to_html_design(self) -> HTMLItemSpec:
        # style
        style_spec = get_style_spec(style_name=self.style_name)
        ## data
        intermediate_charting_spec = get_by_series_xy_charting_spec(
            cur=self.cur, dbe_spec=self.dbe_spec, source_table_name=self.source_table_name,
            x_field_name=self.x_field_name, y_field_name=self.y_field_name,
            series_field_name=self.series_field_name,
            sort_orders=self.sort_orders,
            series_sort_order=self.series_sort_order,
            table_filter_sql=self.table_filter_sql)
        ## charts details
        indiv_chart_specs = intermediate_charting_spec.to_indiv_chart_specs()
        charting_spec = ScatterChartingSpec(
            indiv_chart_specs=indiv_chart_specs,
            series_legend_label=intermediate_charting_spec.series_field_name,
            show_dot_borders=self.show_dot_borders,
            show_n_records=self.show_n_records,
            show_regression_line=self.show_regression_line,
            x_axis_font_size=self.x_axis_font_size,
            x_axis_title=intermediate_charting_spec.x_field_name,
            y_axis_title=intermediate_charting_spec.y_field_name,
        )
        ## output
        html = get_html(charting_spec, style_spec)
        return HTMLItemSpec(
            html_item_str=html,
            output_item_type=OutputItemType.CHART,
            output_title=self.output_title,
            design_name=self.__class__.__name__,
            style_name=self.style_name,
        )


@dataclass(frozen=False)
class MultiChartScatterChartDesign(CommonDesign):
    """
    Args:
        chart_field_name: the field name defining the charts e.g. a `chart_field_name` of 'Country'
            might separate generate charts for 'USA', 'NZ', 'Denmark', and 'South Korea'.
        chart_sort_order: define order of charts e.g. `SortOrder.VALUES` or `SortOrder.CUSTOM`
    """
    x_field_name: str = DEFAULT_SUPPLIED_BUT_MANDATORY_ANYWAY
    y_field_name: str = DEFAULT_SUPPLIED_BUT_MANDATORY_ANYWAY
    chart_field_name: str = DEFAULT_SUPPLIED_BUT_MANDATORY_ANYWAY
    chart_sort_order: SortOrder = SortOrder.VALUE

    show_dot_borders: bool = True
    show_n_records: bool = True
    show_regression_line: bool = True
    x_axis_font_size: int = 10

    def to_html_design(self) -> HTMLItemSpec:
        # style
        style_spec = get_style_spec(style_name=self.style_name)
        ## data
        intermediate_charting_spec = get_by_chart_xy_charting_spec(
            cur=self.cur, dbe_spec=self.dbe_spec, source_table_name=self.source_table_name,
            x_field_name=self.x_field_name, y_field_name=self.y_field_name,
            chart_field_name=self.chart_field_name,
            sort_orders=self.sort_orders,
            chart_sort_order=self.chart_sort_order,
            table_filter_sql=self.table_filter_sql)
        ## charts details
        indiv_chart_specs = intermediate_charting_spec.to_indiv_chart_specs()
        charting_spec = ScatterChartingSpec(
            indiv_chart_specs=indiv_chart_specs,
            series_legend_label=None,
            show_dot_borders=self.show_dot_borders,
            show_n_records=self.show_n_records,
            show_regression_line=self.show_regression_line,
            x_axis_font_size=self.x_axis_font_size,
            x_axis_title=intermediate_charting_spec.x_field_name,
            y_axis_title=intermediate_charting_spec.y_field_name,
        )
        ## output
        html = get_html(charting_spec, style_spec)
        return HTMLItemSpec(
            html_item_str=html,
            output_item_type=OutputItemType.CHART,
            output_title=self.output_title,
            design_name=self.__class__.__name__,
            style_name=self.style_name,
        )


@dataclass(frozen=False)
class MultiChartBySeriesScatterChartDesign(CommonDesign):
    """
    Args:
        series_field_name: the field name defining the series e.g. a `series_field_name` of 'Country'
            might separate generate different colour dots for 'USA', 'NZ', 'Denmark', and 'South Korea'.
        series_sort_order: define order of series in the legend e.g. `SortOrder.VALUES` or `SortOrder.CUSTOM`
        chart_field_name: the field name defining the charts e.g. a `chart_field_name` of 'Country'
            might separate generate charts for 'USA', 'NZ', 'Denmark', and 'South Korea'.
        chart_sort_order: define order of charts e.g. `SortOrder.VALUES` or `SortOrder.CUSTOM`
    """
    x_field_name: str = DEFAULT_SUPPLIED_BUT_MANDATORY_ANYWAY
    y_field_name: str = DEFAULT_SUPPLIED_BUT_MANDATORY_ANYWAY
    series_field_name: str = DEFAULT_SUPPLIED_BUT_MANDATORY_ANYWAY
    series_sort_order: SortOrder = SortOrder.VALUE
    chart_field_name: str = DEFAULT_SUPPLIED_BUT_MANDATORY_ANYWAY
    chart_sort_order: SortOrder = SortOrder.VALUE

    show_dot_borders: bool = True
    show_n_records: bool = True
    show_regression_line: bool = True
    x_axis_font_size: int = 10

    def to_html_design(self) -> HTMLItemSpec:
        # style
        style_spec = get_style_spec(style_name=self.style_name)
        ## data
        intermediate_charting_spec = get_by_chart_series_xy_charting_spec(
            cur=self.cur, dbe_spec=self.dbe_spec, source_table_name=self.source_table_name,
            x_field_name=self.x_field_name, y_field_name=self.y_field_name,
            series_field_name=self.series_field_name, chart_field_name=self.chart_field_name,
            sort_orders=self.sort_orders,
            series_sort_order=self.series_sort_order, chart_sort_order=self.chart_sort_order,
            table_filter_sql=self.table_filter_sql)
        ## charts details
        indiv_chart_specs = intermediate_charting_spec.to_indiv_chart_specs()
        charting_spec = ScatterChartingSpec(
            indiv_chart_specs=indiv_chart_specs,
            series_legend_label=intermediate_charting_spec.series_field_name,
            show_dot_borders=self.show_dot_borders,
            show_n_records=self.show_n_records,
            show_regression_line=self.show_regression_line,
            x_axis_font_size=self.x_axis_font_size,
            x_axis_title=intermediate_charting_spec.x_field_name,
            y_axis_title=intermediate_charting_spec.y_field_name,
        )
        ## output
        html = get_html(charting_spec, style_spec)
        return HTMLItemSpec(
            html_item_str=html,
            output_item_type=OutputItemType.CHART,
            output_title=self.output_title,
            design_name=self.__class__.__name__,
            style_name=self.style_name,
        )
