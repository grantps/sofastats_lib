from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal
import uuid

import jinja2

from sofastats.conf.main import HISTO_AVG_CHAR_WIDTH_PIXELS, SortOrder
from sofastats.data_extraction.charts.histogram import (
    HistoIndivChartSpec, get_by_chart_charting_spec, get_by_vals_charting_spec)
from sofastats.output.charts.common import (
    get_common_charting_spec, get_html, get_indiv_chart_html, get_indiv_chart_title_html)
from sofastats.output.charts.interfaces import JSBool
from sofastats.output.interfaces import (
    DEFAULT_SUPPLIED_BUT_MANDATORY_ANYWAY, HTMLItemSpec, OutputItemType, CommonDesign)
from sofastats.output.styles.interfaces import ColorWithHighlight, StyleSpec
from sofastats.output.styles.utils import fix_default_single_color_mapping, get_js_highlighting_function, get_style_spec
from sofastats.utils.maths import format_num
from sofastats.utils.misc import todict

MIN_CHART_WIDTH = 700
MIN_PIXELS_PER_BAR = 30
PADDING_PIXELS = 5

@dataclass(frozen=True, kw_only=True)
class HistogramConf:
    var_label: str
    chart_label: str | None
    inner_background_color: str
    bar_color: str
    line_color: str
    label_chart_from_var_if_needed: bool = True

@dataclass(frozen=True)
class CommonColorSpec:
    axis_font: str
    chart_background: str
    chart_title_font: str
    color_mappings: Sequence[ColorWithHighlight]
    fill: str
    major_grid_line: str
    normal_curve: str
    plot_background: str
    plot_font: str
    tool_tip_border: str

@dataclass(frozen=True)
class CommonOptions:
    has_minor_ticks_js_bool: Literal['true', 'false']
    is_multi_chart: bool
    show_borders: bool
    show_n_records: bool
    show_normal_curve_js_bool: Literal['true', 'false']

@dataclass(frozen=True)
class CommonMiscSpec:
    bin_labels: Sequence[str]  ## e.g. ["1 to < 6.0", ... "91.0 to <= 96.0"]
    blank_x_axis_numbers_and_labels: str
    border_width: int
    connector_style: str
    grid_line_width: int
    height: float  ## pixels
    left_margin_offset: int
    normal_curve_width: int
    var_label: str
    width: float  ## pixels
    x_axis_font_size: float
    x_axis_max_val: float
    x_axis_min_val: float
    y_axis_max_val: float
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

tpl_chart = """
<script type="text/javascript">

{{js_highlighting_function}}

make_chart_{{chart_uuid}} = function(){

    var data_spec = new Array();
        data_spec["series_label"] = "{{var_label}}";
        data_spec["y_vals"] = {{y_vals}};
        data_spec["norm_y_vals"] = {{norm_y_vals}};
        data_spec["bin_labels"] = {{bin_labels}};
        data_spec["style"] = {
            stroke: {
                color: "{{border_color}}", width: "{{border_width}}px"
            },
            fill: "{{fill}}"
        };
        data_spec["norm_style"] = {
            plot: "normal",
            stroke: {
                color: "{{normal_curve}}",
                width: "{{normal_curve_width}}px"
            },
            fill: "{{fill}}"
        };

    var conf = new Array();
        conf["axis_font_color"] = "{{axis_font}}";
        conf["blank_x_axis_numbers_and_labels"] = {{blank_x_axis_numbers_and_labels}};
        conf["chart_background_color"] = "{{chart_background}}";
        conf["connector_style"] = "{{connector_style}}";
        conf["grid_line_width"] = {{grid_line_width}};
        conf["has_minor_ticks"] = {{has_minor_ticks_js_bool}};
        conf["highlight"] = highlight_{{chart_uuid}};
        conf["left_margin_offset"] = {{left_margin_offset}};
        conf["major_grid_line_color"] = "{{major_grid_line}}";
        conf["n_records"] = "{{n_records}}";
        conf["normal_curve_color"] = "{{normal_curve}}";
        conf["plot_background_color"] = "{{plot_background}}";
        conf["plot_font_color"] = "{{plot_font}}";
        conf["show_normal_curve"] = {{show_normal_curve_js_bool}};
        conf["tool_tip_border_color"] = "{{tool_tip_border}}";
        conf["x_axis_font_size"] = {{x_axis_font_size}};
        conf["x_axis_max_val"] = {{x_axis_max_val}};
        conf["x_axis_min_val"] = {{x_axis_min_val}};
        conf["y_axis_max_val"] = {{y_axis_max_val}};
        conf["y_axis_title"] = "{{y_axis_title}}";
        conf["y_axis_title_offset"] = {{y_axis_title_offset}};

     makeHistogram("histogram_{{chart_uuid}}", data_spec, conf);
 }
 </script>

 <div class="screen-float-only" style="margin-right: 10px; {{page_break}}">
 {{indiv_title_html}}
     <div id="histogram_{{chart_uuid}}"
         style="width: {{width}}px; height: {{height}}px;">
     </div>
 </div>
 """

def get_width(var_label: str, *, n_bins: int,
        x_axis_min_val: float, x_axis_max_val: float, is_multi_chart: bool) -> float:
    max_label_width = max(len(str(round(x, 0))) for x in (x_axis_min_val, x_axis_max_val))
    min_bin_width = max(max_label_width * HISTO_AVG_CHAR_WIDTH_PIXELS, MIN_PIXELS_PER_BAR)
    width_x_axis_title = len(var_label) * HISTO_AVG_CHAR_WIDTH_PIXELS + PADDING_PIXELS
    width = max([n_bins * min_bin_width, width_x_axis_title, MIN_CHART_WIDTH])
    if is_multi_chart:
        width = width * 0.9  ## vulnerable to x-axis labels vanishing on minor ticks
    return width

@dataclass
class HistoChartingSpec:
    bin_labels: Sequence[str]
    indiv_chart_specs: Sequence[HistoIndivChartSpec]
    show_borders: bool
    show_n_records: bool
    show_normal_curve: bool
    var_label: str | None
    x_axis_font_size: int
    x_axis_max_val: float
    x_axis_min_val: float

    def __post_init__(self):
        self.n_bins = len(self.bin_labels)
        self.n_charts = len(self.indiv_chart_specs)
        self.is_multi_chart = self.n_charts > 1
        y_axis_max_val = 0
        for indiv_chart_spec in self.indiv_chart_specs:
            indiv_chart_max_y_val = max(
                max(indiv_chart_spec.y_vals),
                max(indiv_chart_spec.norm_y_vals),
            )
            if indiv_chart_max_y_val > y_axis_max_val:
                y_axis_max_val = indiv_chart_max_y_val
        self.y_axis_max_val = y_axis_max_val

@get_common_charting_spec.register
def get_common_charting_spec(charting_spec: HistoChartingSpec, style_spec: StyleSpec) -> CommonChartingSpec:
    ## colours
    color_mappings = style_spec.chart.color_mappings[:1]  ## only need the first
    color_mappings = fix_default_single_color_mapping(color_mappings)
    first_color = color_mappings[0].main
    ## misc
    blank_dojo_format_x_axis_numbers_and_labels = (
        '[' + ', '.join(f"{{value: {n}, text: ''}}" for n in range(1, charting_spec.n_bins + 1)) + ']')
    height = 300 if charting_spec.is_multi_chart else 350
    y_axis_title_offset = 45
    left_margin_offset = 25
    border_width = style_spec.chart.border_width if charting_spec.show_borders else 0
    normal_curve_width = 4
    show_normal_curve_js_bool: JSBool = 'true' if charting_spec.show_normal_curve else 'false'
    width = get_width(charting_spec.var_label, n_bins=charting_spec.n_bins,
        x_axis_min_val=charting_spec.x_axis_min_val, x_axis_max_val=charting_spec.x_axis_max_val,
        is_multi_chart=charting_spec.is_multi_chart)
    x_axis_font_size = charting_spec.x_axis_font_size
    if charting_spec.is_multi_chart:
        x_axis_font_size *= 0.8
    color_spec = CommonColorSpec(
        axis_font=style_spec.chart.axis_font_color,
        chart_background=style_spec.chart.chart_background_color,
        chart_title_font=style_spec.chart.chart_title_font_color,
        color_mappings=color_mappings,
        fill=first_color,
        major_grid_line=style_spec.chart.major_grid_line_color,
        normal_curve=style_spec.chart.normal_curve_color,
        plot_background=style_spec.chart.plot_background_color,
        plot_font=style_spec.chart.plot_font_color,
        tool_tip_border=style_spec.chart.tool_tip_border_color,
    )
    misc_spec = CommonMiscSpec(
        bin_labels=charting_spec.bin_labels,
        blank_x_axis_numbers_and_labels=blank_dojo_format_x_axis_numbers_and_labels,
        border_width=border_width,
        connector_style=style_spec.dojo.connector_style,
        grid_line_width=style_spec.chart.grid_line_width,
        height=height,
        left_margin_offset=left_margin_offset,
        x_axis_min_val=charting_spec.x_axis_min_val,
        normal_curve_width=normal_curve_width,
        var_label=charting_spec.var_label,
        width=width,
        x_axis_font_size=charting_spec.x_axis_font_size,
        x_axis_max_val=charting_spec.x_axis_max_val,
        y_axis_max_val=charting_spec.y_axis_max_val,
        y_axis_title='Frequency',
        y_axis_title_offset=y_axis_title_offset,
    )
    options = CommonOptions(
        has_minor_ticks_js_bool='true',
        is_multi_chart=charting_spec.is_multi_chart,
        show_borders=charting_spec.show_borders,
        show_n_records=charting_spec.show_n_records,
        show_normal_curve_js_bool=show_normal_curve_js_bool,
    )
    return CommonChartingSpec(
        color_spec=color_spec,
        misc_spec=misc_spec,
        options=options,
    )

@get_indiv_chart_html.register
def get_indiv_chart_html(common_charting_spec: CommonChartingSpec, indiv_chart_spec: HistoIndivChartSpec,
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
    js_highlighting_function = get_js_highlighting_function(
        color_mappings=common_charting_spec.color_spec.color_mappings, chart_uuid=chart_uuid)
    indiv_context = {
        'chart_uuid': chart_uuid,
        'indiv_title_html': indiv_title_html,
        'js_highlighting_function': js_highlighting_function,
        'n_records': n_records,
        'norm_y_vals': indiv_chart_spec.norm_y_vals,
        'page_break': page_break,
        'y_vals': indiv_chart_spec.y_vals,
    }
    context.update(indiv_context)
    environment = jinja2.Environment()
    template = environment.from_string(tpl_chart)
    html_result = template.render(context)
    return html_result

@dataclass(frozen=False)
class HistogramChartDesign(CommonDesign):
    """
    Args:
        field_name: field summarised in each box
        show_borders: show a coloured border around the bars
        show_n_records: show the number of records the chart is based on
        show_normal_curve: if `True` display normal curve on the chart
        x_axis_font_size: font size for x-axis labels
    """
    field_name: str = DEFAULT_SUPPLIED_BUT_MANDATORY_ANYWAY

    show_borders: bool = False
    show_n_records: bool = True
    show_normal_curve: bool = True
    x_axis_font_size: int = 12

    def to_html_design(self) -> HTMLItemSpec:
        # style
        style_spec = get_style_spec(style_name=self.style_name)
        ## data
        intermediate_charting_spec = get_by_vals_charting_spec(
            cur=self.cur, dbe_spec=self.dbe_spec, source_table_name=self.source_table_name,
            field_name=self.field_name, table_filter_sql=self.table_filter_sql, decimal_points=self.decimal_points)
        bin_labels = intermediate_charting_spec.to_bin_labels()
        x_axis_min_val, x_axis_max_val = intermediate_charting_spec.to_x_axis_range()
        ## charts details
        indiv_chart_specs = intermediate_charting_spec.to_indiv_chart_specs()
        charting_spec = HistoChartingSpec(
            bin_labels=bin_labels,
            indiv_chart_specs=indiv_chart_specs,
            show_borders=self.show_borders,
            show_n_records=self.show_n_records,
            show_normal_curve=self.show_normal_curve,
            var_label=intermediate_charting_spec.field_name,
            x_axis_font_size=self.x_axis_font_size,
            x_axis_max_val=x_axis_max_val,
            x_axis_min_val=x_axis_min_val,
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
class MultiChartHistogramChartDesign(CommonDesign):
    """
    Args:
        chart_field_name: the field name defining the charts e.g. a `chart_field_name` of 'Country'
            might separate generate charts for 'USA', 'NZ', 'Denmark', and 'South Korea'.
        chart_sort_order: define order of charts e.g. `SortOrder.VALUES` or `SortOrder.CUSTOM`
    """
    field_name: str = DEFAULT_SUPPLIED_BUT_MANDATORY_ANYWAY
    chart_field_name: str = DEFAULT_SUPPLIED_BUT_MANDATORY_ANYWAY
    chart_sort_order: SortOrder = SortOrder.VALUE

    show_borders: bool = False
    show_n_records: bool = True
    show_normal_curve: bool = True
    x_axis_font_size: int = 12

    def to_html_design(self) -> HTMLItemSpec:
        # style
        style_spec = get_style_spec(style_name=self.style_name)
        ## data
        intermediate_charting_spec = get_by_chart_charting_spec(
            cur=self.cur, dbe_spec=self.dbe_spec, source_table_name=self.source_table_name,
            field_name=self.field_name,
            chart_field_name=self.chart_field_name,
            sort_orders=self.sort_orders,
            chart_sort_order=self.chart_sort_order,
            table_filter_sql=self.table_filter_sql,
            decimal_points=self.decimal_points,
        )
        x_axis_min_val, x_axis_max_val = intermediate_charting_spec.to_x_axis_range()
        ## charts details
        indiv_chart_specs = intermediate_charting_spec.to_indiv_chart_specs()
        charting_spec = HistoChartingSpec(
            bin_labels=intermediate_charting_spec.to_bin_labels(),
            indiv_chart_specs=indiv_chart_specs,
            show_borders=self.show_borders,
            show_n_records=self.show_n_records,
            show_normal_curve=self.show_normal_curve,
            var_label=intermediate_charting_spec.field_name,
            x_axis_font_size=self.x_axis_font_size,
            x_axis_max_val=x_axis_max_val,
            x_axis_min_val=x_axis_min_val,
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
