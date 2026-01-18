from collections.abc import Sequence
from dataclasses import dataclass
import uuid

import jinja2

from sofastats.conf.main import SortOrder
from sofastats.data_extraction.charts.amounts import (
    get_by_category_charting_spec, get_by_chart_category_charting_spec)
from sofastats.data_extraction.charts.interfaces.common import IndivChartSpec
from sofastats.output.charts.common import (
    get_common_charting_spec, get_html, get_indiv_chart_html, get_indiv_chart_title_html)
from sofastats.output.charts.interfaces import ChartingSpecNoAxes
from sofastats.output.interfaces import (
    DEFAULT_SUPPLIED_BUT_MANDATORY_ANYWAY, HTMLItemSpec, OutputItemType, CommonDesign)
from sofastats.output.styles.interfaces import ColorWithHighlight, StyleSpec
from sofastats.output.styles.utils import get_js_highlighting_function, get_long_color_list, get_style_spec
from sofastats.utils.misc import todict

@dataclass
class PieChartingSpec(ChartingSpecNoAxes):
    def __post_init__(self):
        super().__post_init__()
        if not self.is_single_series:
            raise TypeError("Pie Charts have to have only one data series per chart")

@dataclass(frozen=True)
class CommonColorSpec:
    chart_title_font: str
    color_mappings: Sequence[ColorWithHighlight]
    plot_background: str
    plot_font: str
    slice_colors: Sequence[str]
    tool_tip_border: str

@dataclass(frozen=True)
class CommonOptions:
    is_multi_chart: bool

@dataclass(frozen=True)
class CommonMiscSpec:
    connector_style: str
    height: float  ## pixels
    label_offset: int
    radius: float
    slice_font_size: int
    slice_labels: Sequence[str]
    slice_vals: Sequence[float]
    width: float  ## pixels

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

     slices = [
       {% for slice_str in slice_strs %}\n            {{slice_str}}{% endfor %}
     ];

     var conf = new Array();
         conf["connector_style"] = "{{connector_style}}";
         conf["n_records"] = "{{n_records}}";
         conf["plot_font_color"] = "{{plot_font}}";
         conf["plot_background_color"] = "{{plot_background}}";
         conf["radius"] = {{radius}};
         conf["slice_colors"] = {{slice_colors_as_displayed}};
         conf["slice_font_size"] = {{slice_font_size}};
         conf["tool_tip_border_color"] = "{{tool_tip_border}}";
         // distinct fields for pie charts
         conf["highlight"] = highlight_{{chart_uuid}};
         conf["label_offset"] = {{label_offset}};

     makePieChart("pie_chart_{{chart_uuid}}", slices, conf);
 }
 </script>

 <div class="screen-float-only" style="margin-right: 10px; {{page_break}}">
 {{indiv_title_html}}
     <div id="pie_chart_{{chart_uuid}}"
         style="width: {{width}}px; height: {{height}}px;">
     </div>
     {% if series_legend_label %}
         <p style="float: left; font-weight: bold; margin-right: 12px; margin-top: 9px;">
             {{series_legend_label}}:
         </p>
         <div id="legend_for_pie_chart_{{chart_uuid}}">
         </div>
     {% endif %}
 </div>
 """

@get_common_charting_spec.register
def get_common_charting_spec(charting_spec: PieChartingSpec, style_spec: StyleSpec) -> CommonChartingSpec:
    ## colours
    color_mappings = style_spec.chart.color_mappings
    slice_colors = get_long_color_list(color_mappings)
    ## misc
    height = 370 if charting_spec.is_multi_chart else 420
    label_offset = -20 if charting_spec.is_multi_chart else -30
    radius = 120 if charting_spec.is_multi_chart else 140
    slice_font_size = 14 if charting_spec.n_charts < 10 else 10
    slice_vals = charting_spec.indiv_chart_specs[0].data_series_specs[0].amounts
    if charting_spec.is_multi_chart:
        slice_font_size *= 0.8
    color_spec = CommonColorSpec(
        chart_title_font=style_spec.chart.chart_title_font_color,
        color_mappings=color_mappings,
        plot_background=style_spec.chart.plot_background_color,
        plot_font=style_spec.chart.plot_font_color,
        slice_colors=slice_colors,
        tool_tip_border=style_spec.chart.tool_tip_border_color,
    )
    misc_spec = CommonMiscSpec(
        connector_style=style_spec.dojo.connector_style,
        height=height,
        label_offset=label_offset,
        radius=radius,
        slice_font_size=slice_font_size,
        slice_labels=charting_spec.categories,
        slice_vals=slice_vals,
        width=450,
    )
    options = CommonOptions(
        is_multi_chart=charting_spec.is_multi_chart,
    )
    return CommonChartingSpec(
        color_spec=color_spec,
        misc_spec=misc_spec,
        options=options,
    )

@get_indiv_chart_html.register
def get_indiv_chart_html(common_charting_spec: CommonChartingSpec, indiv_chart_spec: IndivChartSpec,
        *,  chart_counter: int) -> str:
    """
    Note - to keep the same colours for the same slice categories
    it is important to keep them aligned even if some slices are not displayed
    (because 'y' value is 0).
    """
    context = todict(common_charting_spec.color_spec, shallow=True)
    context.update(todict(common_charting_spec.misc_spec, shallow=True))
    context.update(todict(common_charting_spec.options, shallow=True))
    chart_uuid = str(uuid.uuid4()).replace('-', '_')  ## needs to work in JS variable names
    page_break = 'page-break-after: always;' if chart_counter % 2 == 0 else ''
    title = indiv_chart_spec.label
    font_color = common_charting_spec.color_spec.chart_title_font
    indiv_title_html = (get_indiv_chart_title_html(chart_title=title, color=font_color)
        if common_charting_spec.options.is_multi_chart else '')
    ## slices
    only_series = indiv_chart_spec.data_series_specs[0]
    slice_labels = common_charting_spec.misc_spec.slice_labels
    slice_colors = common_charting_spec.color_spec.slice_colors
    slice_colors = slice_colors[:len(slice_labels)]
    slice_details = zip(
        slice_labels,
        only_series.amounts,  ## the actual frequencies e.g. 120 for avg NZ IQ
        slice_colors,
        only_series.tool_tips,
        strict=True)
    slice_strs = []
    slice_colors_as_displayed = []
    for slice_label, slice_val, color, tool_tip in slice_details:
        if slice_val == 0:
            continue
        slice_str = f"""{{"val": {slice_val}, "label": "{slice_label}", "tool_tip": "{tool_tip}"}},"""
        slice_strs.append(slice_str)
        slice_colors_as_displayed.append(color)
    slice_strs[-1] = slice_strs[-1].rstrip(',')
    js_highlighting_function = get_js_highlighting_function(
        color_mappings=common_charting_spec.color_spec.color_mappings, chart_uuid=chart_uuid)
    indiv_context = {
        'chart_uuid': chart_uuid,
        'indiv_title_html': indiv_title_html,
        'js_highlighting_function': js_highlighting_function,
        'page_break': page_break,
        'slice_colors_as_displayed': slice_colors_as_displayed,
        'slice_strs': slice_strs,
    }
    context.update(indiv_context)
    environment = jinja2.Environment()
    template = environment.from_string(tpl_chart)
    html_result = template.render(context)
    return html_result


@dataclass(frozen=False)
class PieChartDesign(CommonDesign):
    """
    Args:
        category_field_name: name of field in the x-axis
        category_sort_order: define order of categories in each chart e.g. `SortOrder.VALUES` or `SortOrder.CUSTOM`
        show_n_records: show the number of records the chart is based on
    """
    category_field_name: str = DEFAULT_SUPPLIED_BUT_MANDATORY_ANYWAY
    category_sort_order: SortOrder = SortOrder.VALUE

    show_n_records: bool = True,

    def to_html_design(self) -> HTMLItemSpec:
        # style
        style_spec = get_style_spec(style_name=self.style_name)
        ## data
        intermediate_charting_spec = get_by_category_charting_spec(
            cur=self.cur, dbe_spec=self.dbe_spec, source_table_name=self.source_table_name,
            category_field_name=self.category_field_name,
            sort_orders=self.sort_orders, category_sort_order=self.category_sort_order,
            table_filter_sql=self.table_filter_sql)
        ## charts details
        charting_spec = PieChartingSpec(
            categories=intermediate_charting_spec.sorted_categories,
            indiv_chart_specs=[intermediate_charting_spec.to_indiv_chart_spec(), ],
            show_n_records=self.show_n_records,
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
class MultiChartPieChartDesign(CommonDesign):
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

    show_n_records: bool = True,

    def to_html_design(self) -> HTMLItemSpec:
        # style
        style_spec = get_style_spec(style_name=self.style_name)
        ## data
        intermediate_charting_spec = get_by_chart_category_charting_spec(
            cur=self.cur, dbe_spec=self.dbe_spec, source_table_name=self.source_table_name,
            category_field_name=self.category_field_name, chart_field_name=self.chart_field_name,
            sort_orders=self.sort_orders,
            category_sort_order=self.category_sort_order, chart_sort_order=self.chart_sort_order,
            table_filter_sql=self.table_filter_sql)
        ## charts details
        charting_spec = PieChartingSpec(
            categories=intermediate_charting_spec.sorted_categories,
            indiv_chart_specs=intermediate_charting_spec.to_indiv_chart_specs(),
            show_n_records=self.show_n_records,
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
