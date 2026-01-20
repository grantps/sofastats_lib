from abc import abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal
import uuid

import jinja2

from sofastats.conf.main import TEXT_WIDTH_N_CHARACTERS_WHEN_ROTATED, ChartMetric, SortOrder
import sofastats.data_extraction.charts.amounts as from_data
from sofastats.data_extraction.charts.interfaces.common import IndivChartSpec
from sofastats.output.charts.common import (
    get_common_charting_spec, get_html, get_indiv_chart_html, get_indiv_chart_title_html)
from sofastats.output.charts.interfaces import ChartingSpecAxes, DojoSeriesSpec, JSBool
from sofastats.output.charts.utils import (get_axis_label_drop, get_height,
    get_dojo_format_x_axis_numbers_and_labels, get_intrusion_of_first_x_axis_label_leftwards,
    get_width_after_left_margin, get_x_axis_font_size, get_y_axis_title_offset)
from sofastats.output.interfaces import (
    DEFAULT_SUPPLIED_BUT_MANDATORY_ANYWAY, CommonDesign, HTMLItemSpec, OutputItemType)
from sofastats.output.styles.interfaces import ColorWithHighlight, StyleSpec
from sofastats.output.styles.utils import (
    fix_default_single_color_mapping, get_js_highlighting_function, get_long_color_list, get_style_spec)
from sofastats.utils.maths import format_num
from sofastats.utils.misc import todict

MIN_PIXELS_PER_X_ITEM = 60
MIN_CLUSTER_WIDTH_PIXELS = 60
PADDING_PIXELS = 35
DOJO_MINOR_TICKS_NEEDED_PER_X_ITEM = 10  ## whatever works. Tested on cluster of Age vs Cars


@dataclass(frozen=False)
class CommonBarDesign(CommonDesign):
    """
    Args:
        metric: defines what bar heights represent - whether ChartMetric.FREQ, ChartMetric.PCT, etc.
        field_name: the name of the field being aggregated when the metric is an aggregate
            e.g. ChartMetric.AVG or ChartMetric.SUM
        y_axis_title: title displayed vertically alongside y-axis
    """

    metric: ChartMetric = ChartMetric.FREQ
    field_name: str | None = None
    y_axis_title: str | None = None

    def __post_init__(self):
        super().__post_init__()
        if self.y_axis_title is None:  ##TODO - no field name unless aggregating
            if self.metric == ChartMetric.AVG:
                self.y_axis_title = f"Average {self.field_name}"
            elif self.metric == ChartMetric.FREQ:
                self.y_axis_title = 'Frequency'
            elif self.metric == ChartMetric.PCT:
                self.y_axis_title = 'Percent'
            elif self.metric == ChartMetric.SUM:
                self.y_axis_title = f"Summed {self.field_name}"
            else:
                raise ValueError(f'Metric {self.metric} is not supported.')
        if self.field_name is None:
            if self.metric in (ChartMetric.AVG, ChartMetric.SUM):
                raise ValueError("A field_name must be set if the metric aggregates "
                    "e.g. ChartMetric.AVG or ChartMetric.SUM")
        else:
            if self.metric not in (ChartMetric.AVG, ChartMetric.SUM):
                raise ValueError("A field_name should only be supplied if the metric aggregates "
                    "e.g. ChartMetric.AVG or ChartMetric.SUM")

    @abstractmethod
    def to_html_design(self) -> HTMLItemSpec:
        pass

@dataclass(frozen=False)
class SimpleBarChartDesign(CommonBarDesign):
    """
    Args:
        category_field_name: name of field in the x-axis
        category_sort_order: define order of categories in each chart e.g. `SortOrder.VALUES` or `SortOrder.CUSTOM`
        rotate_x_labels: make x-axis labels vertical
        show_borders: show a coloured border around the bars
        show_n_records: show the number of records the chart is based on
        x_axis_font_size: font size for x-axis labels
    """
    category_field_name: str = DEFAULT_SUPPLIED_BUT_MANDATORY_ANYWAY
    category_sort_order: SortOrder = SortOrder.VALUE

    rotate_x_labels: bool = False
    show_borders: bool = False
    show_n_records: bool = True
    x_axis_font_size: int = 12

    def to_html_design(self) -> HTMLItemSpec:
        ## style
        style_spec = get_style_spec(style_name=self.style_name)
        ## data
        intermediate_charting_spec = from_data.get_by_category_charting_spec(
            cur=self.cur, dbe_spec=self.dbe_spec, source_table_name=self.source_table_name,
            category_field_name=self.category_field_name, sort_orders=self.sort_orders,
            category_sort_order=self.category_sort_order,
            metric=self.metric, field_name=self.field_name,
            table_filter_sql=self.table_filter_sql, decimal_points=self.decimal_points)
        ## chart details
        charting_spec = BarChartingSpec(
            categories=intermediate_charting_spec.sorted_categories,
            indiv_chart_specs=[intermediate_charting_spec.to_indiv_chart_spec(), ],
            series_legend_label=None,
            rotate_x_labels=self.rotate_x_labels,
            show_borders=self.show_borders,
            border_width=style_spec.chart.border_width,
            show_n_records=self.show_n_records,
            x_axis_font_size=self.x_axis_font_size,
            x_axis_title=intermediate_charting_spec.category_field_name,
            y_axis_title=self.y_axis_title,
        )
        ## output
        html = get_html(charting_spec, style_spec)  ## see get_indiv_chart_html() below
        return HTMLItemSpec(
            html_item_str=html,
            output_item_type=OutputItemType.CHART,
            output_title=self.output_title,
            design_name=self.__class__.__name__,
            style_name=self.style_name,
        )


@dataclass(frozen=False)
class MultiChartBarChartDesign(CommonBarDesign):
    """
    Args:
        chart_field_name: the field name defining the charts e.g. a `chart_field_name` of 'Country'
            might separate generate charts for 'USA', 'NZ', 'Denmark', and 'South Korea'.
        chart_sort_order: define order of charts e.g. `SortOrder.VALUES` or `SortOrder.CUSTOM`
    """
    category_field_name: str = DEFAULT_SUPPLIED_BUT_MANDATORY_ANYWAY
    category_sort_order: SortOrder = SortOrder.VALUE
    chart_field_name: str = DEFAULT_SUPPLIED_BUT_MANDATORY_ANYWAY
    chart_sort_order: SortOrder = SortOrder.VALUE

    metric: ChartMetric = ChartMetric.FREQ
    rotate_x_labels: bool = False
    show_borders: bool = False
    show_n_records: bool = True
    x_axis_font_size: int = 12

    def to_html_design(self) -> HTMLItemSpec:
        # style
        style_spec = get_style_spec(style_name=self.style_name)
        ## data
        intermediate_charting_spec = from_data.get_by_chart_category_charting_spec(
            cur=self.cur, dbe_spec=self.dbe_spec, source_table_name=self.source_table_name,
            category_field_name=self.category_field_name, chart_field_name=self.chart_field_name,
            sort_orders=self.sort_orders,
            category_sort_order=self.category_sort_order, chart_sort_order=self.chart_sort_order,
            metric=self.metric, field_name=self.field_name,
            table_filter_sql=self.table_filter_sql, decimal_points=self.decimal_points)
        ## charts details
        charting_spec = BarChartingSpec(
            border_width=style_spec.chart.border_width,
            categories=intermediate_charting_spec.sorted_categories,
            indiv_chart_specs=intermediate_charting_spec.to_indiv_chart_specs(),
            series_legend_label=None,
            rotate_x_labels=self.rotate_x_labels,
            show_borders=self.show_borders,
            show_n_records=self.show_n_records,
            x_axis_font_size=self.x_axis_font_size,
            x_axis_title=intermediate_charting_spec.category_field_name,
            y_axis_title=self.y_axis_title,
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
class ClusteredBarChartDesign(CommonBarDesign):
    """
    Args:
        series_field_name: the field name defining the series e.g. a `series_field_name` of 'Country'
            might separate generate bars within each category cluster for 'USA', 'NZ', 'Denmark', and 'South Korea'.
        series_sort_order: define order of series within each category cluster e.g. `SortOrder.VALUES` or `SortOrder.CUSTOM`
    """
    category_field_name: str = DEFAULT_SUPPLIED_BUT_MANDATORY_ANYWAY
    category_sort_order: SortOrder = SortOrder.VALUE
    series_field_name: str = DEFAULT_SUPPLIED_BUT_MANDATORY_ANYWAY
    series_sort_order: SortOrder = SortOrder.VALUE

    metric: ChartMetric = ChartMetric.FREQ
    rotate_x_labels: bool = False
    show_borders: bool = False
    show_n_records: bool = True
    x_axis_font_size: int = 12

    def to_html_design(self) -> HTMLItemSpec:
        # style
        style_spec = get_style_spec(style_name=self.style_name)
        ## data
        intermediate_charting_spec = from_data.get_by_series_category_charting_spec(
            cur=self.cur, dbe_spec=self.dbe_spec, source_table_name=self.source_table_name,
            category_field_name=self.category_field_name, series_field_name=self.series_field_name,
            sort_orders=self.sort_orders,
            category_sort_order=self.category_sort_order, series_sort_order=self.series_sort_order,
            metric=self.metric, field_name=self.field_name,
            table_filter_sql=self.table_filter_sql, decimal_points=self.decimal_points)
        ## chart details
        charting_spec = BarChartingSpec(
            border_width=style_spec.chart.border_width,
            categories=intermediate_charting_spec.sorted_categories,
            indiv_chart_specs=[intermediate_charting_spec.to_indiv_chart_spec(), ],
            series_legend_label=intermediate_charting_spec.series_field_name,
            rotate_x_labels=self.rotate_x_labels,
            show_borders=self.show_borders,
            show_n_records=self.show_n_records,
            x_axis_font_size=self.x_axis_font_size,
            x_axis_title=intermediate_charting_spec.category_field_name,
            y_axis_title=self.y_axis_title,
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
class MultiChartClusteredBarChartDesign(CommonBarDesign):
    """
    Args:
        series_field_name: the field name defining the series e.g. a `series_field_name` of 'Country'
            might separate generate bars within each category cluster for 'USA', 'NZ', 'Denmark', and 'South Korea'.
        series_sort_order: define order of series within each category cluster e.g. `SortOrder.VALUES` or `SortOrder.CUSTOM`
        chart_field_name: the field name defining the charts e.g. a `chart_field_name` of 'Country'
            might separate generate charts for 'USA', 'NZ', 'Denmark', and 'South Korea'.
        chart_sort_order: define order of charts e.g. `SortOrder.VALUES` or `SortOrder.CUSTOM`
    """
    category_field_name: str = DEFAULT_SUPPLIED_BUT_MANDATORY_ANYWAY
    category_sort_order: SortOrder = SortOrder.VALUE
    series_field_name: str = DEFAULT_SUPPLIED_BUT_MANDATORY_ANYWAY
    series_sort_order: SortOrder = SortOrder.VALUE
    chart_field_name: str = DEFAULT_SUPPLIED_BUT_MANDATORY_ANYWAY
    chart_sort_order: SortOrder = SortOrder.VALUE

    metric: ChartMetric = ChartMetric.FREQ
    rotate_x_labels: bool = False
    show_borders: bool = False
    show_n_records: bool = True
    x_axis_font_size: int = 12

    def to_html_design(self) -> HTMLItemSpec:
        # style
        style_spec = get_style_spec(style_name=self.style_name)
        ## data
        intermediate_charting_spec = from_data.get_by_chart_series_category_charting_spec(
            cur=self.cur, dbe_spec=self.dbe_spec, source_table_name=self.source_table_name,
            category_field_name=self.category_field_name,
            series_field_name=self.series_field_name,
            chart_field_name=self.chart_field_name,
            sort_orders=self.sort_orders,
            category_sort_order=self.category_sort_order,
            series_sort_order=self.series_sort_order,
            chart_sort_order=self.chart_sort_order,
            metric=self.metric, field_name=self.field_name,
            table_filter_sql=self.table_filter_sql,
            decimal_points=self.decimal_points)
        ## chart details
        charting_spec = BarChartingSpec(
            border_width=style_spec.chart.border_width,
            categories=intermediate_charting_spec.sorted_categories,
            indiv_chart_specs=intermediate_charting_spec.to_indiv_chart_specs(),
            series_legend_label=intermediate_charting_spec.series_field_name,
            rotate_x_labels=self.rotate_x_labels,
            show_borders=self.show_borders,
            show_n_records=self.show_n_records,
            x_axis_font_size=self.x_axis_font_size,
            x_axis_title=intermediate_charting_spec.category_field_name,
            y_axis_title=self.y_axis_title,
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

@dataclass
class BarChartingSpec(ChartingSpecAxes):
    show_borders: bool
    border_width: int
    metric: ChartMetric = ChartMetric.FREQ

@dataclass(frozen=False)
class CommonColorSpec:
    axis_font: str
    border_color: str
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
    show_borders: bool
    show_n_records: bool

@dataclass(frozen=True)
class CommonMiscSpec:
    axis_label_drop: int
    axis_label_rotate: int
    border_width: int
    connector_style: str
    grid_line_width: int
    height: float  ## pixels
    left_margin_offset: float
    metric: ChartMetric
    series_legend_label: str
    width: float  ## pixels
    x_axis_numbers_and_labels: str  ## Format required by Dojo e.g. [{value: 1, text: "Female"}, {value: 2, text: "Male"}]
    x_axis_font_size: float
    x_axis_title: str
    x_gap: int
    y_axis_title: str
    y_axis_title_offset: float
    y_axis_max: int

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
          series_{{series_spec.series_id}}["vals"] = {{series_spec.vals}};
          // options - stroke_width_to_use, fill_colour, y_lbls_str
          series_{{series_spec.series_id}}["options"] = {{series_spec.options}};
      series.push(series_{{series_spec.series_id}});
    {% endfor %}

    var conf = new Array();
        conf["axis_font_color"] = "{{axis_font}}";
        conf["axis_label_drop"] = {{axis_label_drop}};
        conf["axis_label_rotate"] = {{axis_label_rotate}};
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
        conf["tool_tip_border_color"] = "{{tool_tip_border}}";
        conf["x_axis_font_size"] = {{x_axis_font_size}};
        conf["x_axis_numbers_and_labels"] = {{x_axis_numbers_and_labels}};
        conf["x_axis_title"] = "{{x_axis_title}}";
        conf["x_gap"] = {{x_gap}};
        conf["y_axis_max"] = {{y_axis_max}};
        conf["y_axis_title"] = "{{y_axis_title}}";
        conf["y_axis_title_offset"] = {{y_axis_title_offset}};

    makeBarChart("bar_chart_{{chart_uuid}}", series, conf);
}
</script>

<div class="screen-float-only" style="margin-right: 10px; {{page_break}}">
{{indiv_title_html}}
    <div id="bar_chart_{{chart_uuid}}"
        style="width: {{width}}px; height: {{height}}px;">
    </div>
    {% if series_legend_label %}
        <p style="float: left; font-weight: bold; margin-right: 12px; margin-top: 9px;">
            {{series_legend_label}}:
        </p>
        <div id="legend_for_bar_chart_{{chart_uuid}}">
        </div>
    {% endif %}
</div>
"""

def get_x_gap(*, n_x_items: int, is_multi_chart: bool) -> int:
    if n_x_items <= 2:
        x_gap = 20
    elif n_x_items <= 5:
        x_gap = 10
    elif n_x_items <= 8:
        x_gap = 8
    elif n_x_items <= 10:
        x_gap = 6
    elif n_x_items <= 16:
        x_gap = 5
    else:
        x_gap = 4
    x_gap = x_gap * 0.8 if is_multi_chart else x_gap
    return x_gap

@get_common_charting_spec.register
def get_common_charting_spec(charting_spec: BarChartingSpec, style_spec: StyleSpec) -> CommonChartingSpec:
    """
    Get details that apply to all charts in bar chart set
    (often just one bar chart in set)

    Lots of interactive tweaking required to get charts to actually come out
    well under lots of interactive conditions (different numbers of columns etc.).

    Re: minor_ticks -- generally we don't want them
    as they result in lots of ticks between the groups in clustered bar charts
    each with a distracting and meaningless value
    e.g. if we have two groups 1 and 2 we don't want a tick for 0.8 and 0.9 etc.
    But if we don't have minor ticks when we have a massive number of clusters
    we get no ticks at all.
    Probably a dojo bug I can't fix, so I have to work around it.
    """
    ## colours
    color_mappings = style_spec.chart.color_mappings
    if charting_spec.is_single_series:
        color_mappings = fix_default_single_color_mapping(color_mappings)
    ## misc
    dojo_format_x_axis_numbers_and_labels = get_dojo_format_x_axis_numbers_and_labels(charting_spec.categories)
    has_minor_ticks_js_bool: JSBool = 'true' if charting_spec.n_x_items >= DOJO_MINOR_TICKS_NEEDED_PER_X_ITEM else 'false'
    series_legend_label = '' if charting_spec.is_single_series else charting_spec.series_legend_label
    border_width = style_spec.chart.border_width if charting_spec.show_borders else 0
    ## sizing
    ## width_after_left_margin
    max_x_label_width = (TEXT_WIDTH_N_CHARACTERS_WHEN_ROTATED if charting_spec.rotate_x_labels else charting_spec.max_x_axis_label_len)
    width_after_left_margin = get_width_after_left_margin(
        n_x_items=charting_spec.n_x_items, n_items_horizontally_per_x_item=charting_spec.n_series, min_pixels_per_sub_item=50,
        x_item_padding_pixels=2, sub_item_padding_pixels=5,
        x_axis_title=charting_spec.x_axis_title,
        widest_x_label_n_characters=max_x_label_width, avg_pixels_per_character=10.5,
        min_chart_width_one_item=200, min_chart_width_multi_item=400,
        is_multi_chart=charting_spec.is_multi_chart, multi_chart_size_scalar=0.9)
    ## y-axis offset
    x_labels = charting_spec.categories
    first_x_label = x_labels[0]
    widest_x_axis_label_n_characters = (
        TEXT_WIDTH_N_CHARACTERS_WHEN_ROTATED if charting_spec.rotate_x_labels else len(first_x_label))
    y_axis_max = charting_spec.max_y_val * 1.1
    widest_y_axis_label_n_characters = len(str(int(y_axis_max)))  ## e.g. 1000.5 -> 1000 -> '1000' -> 4
    y_axis_title_offset = get_y_axis_title_offset(
        widest_y_axis_label_n_characters=widest_y_axis_label_n_characters, avg_pixels_per_y_character=9)
    intrusion_of_first_x_axis_label_leftwards = get_intrusion_of_first_x_axis_label_leftwards(
        widest_x_axis_label_n_characters=widest_x_axis_label_n_characters, avg_pixels_per_x_character=5)
    ## misc sizing
    x_axis_font_size = get_x_axis_font_size(n_x_items=charting_spec.n_x_items, is_multi_chart=charting_spec.is_multi_chart)
    x_gap = get_x_gap(n_x_items=charting_spec.n_x_items, is_multi_chart=charting_spec.is_multi_chart)
    axis_label_drop = get_axis_label_drop(
        is_multi_chart=charting_spec.is_multi_chart, rotated_x_labels=charting_spec.rotate_x_labels,
        max_x_axis_label_lines=charting_spec.max_x_axis_label_lines)
    axis_label_rotate = -90 if charting_spec.rotate_x_labels else 0
    left_margin_offset = max(y_axis_title_offset, intrusion_of_first_x_axis_label_leftwards) - 20
    width = left_margin_offset + width_after_left_margin
    height = get_height(axis_label_drop=axis_label_drop,
        rotated_x_labels=charting_spec.rotate_x_labels, max_x_axis_label_len=charting_spec.max_x_axis_label_len)

    color_spec = CommonColorSpec(
        axis_font=style_spec.chart.axis_font_color,
        border_color=style_spec.chart.border_color,
        chart_background=style_spec.chart.chart_background_color,
        chart_title_font=style_spec.chart.chart_title_font_color,
        color_mappings=color_mappings,
        major_grid_line=style_spec.chart.major_grid_line_color,
        plot_background=style_spec.chart.plot_background_color,
        plot_font=style_spec.chart.plot_font_color,
        tool_tip_border=style_spec.chart.tool_tip_border_color,
    )
    misc_spec = CommonMiscSpec(
        axis_label_drop=axis_label_drop,
        axis_label_rotate=axis_label_rotate,
        border_width=border_width,
        connector_style=style_spec.dojo.connector_style,
        grid_line_width=style_spec.chart.grid_line_width,
        height=height,
        left_margin_offset=left_margin_offset,
        metric=charting_spec.metric,
        series_legend_label=series_legend_label,
        width=width,
        x_axis_numbers_and_labels=dojo_format_x_axis_numbers_and_labels,
        x_axis_font_size=x_axis_font_size,
        x_gap=x_gap,
        x_axis_title=charting_spec.x_axis_title,
        y_axis_max=y_axis_max,
        y_axis_title=charting_spec.y_axis_title,
        y_axis_title_offset=y_axis_title_offset,
    )
    options = CommonOptions(
        has_minor_ticks_js_bool=has_minor_ticks_js_bool,
        is_multi_chart=charting_spec.is_multi_chart,
        show_borders=charting_spec.show_borders,
        show_n_records=charting_spec.show_n_records,
    )
    return CommonChartingSpec(
        color_spec=color_spec,
        misc_spec=misc_spec,
        options=options,
    )

@get_indiv_chart_html.register
def get_indiv_chart_html(common_charting_spec: CommonChartingSpec, indiv_chart_spec: IndivChartSpec,
        *,  chart_counter: int) -> str:
    context = todict(common_charting_spec.color_spec, shallow=True)  ## not everything passed through is used in the template
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
        series_vals = str(data_series_spec.amounts)
        ## options e.g. {stroke: {color: "white", width: "0px"}, fill: "#e95f29", yLbls: ['66.38', ...]}
        fill_color = common_charting_spec.color_spec.colors[i]
        y_lbls_str = str(data_series_spec.tool_tips)
        options = (f"""{{stroke: {{color: "{common_charting_spec.color_spec.border_color}", width: "{common_charting_spec.misc_spec.border_width}px"}}, """
            f"""fill: "{fill_color}", yLbls: {y_lbls_str}}}""")
        dojo_series_specs.append(DojoSeriesSpec(series_id, series_label, series_vals, options))
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
