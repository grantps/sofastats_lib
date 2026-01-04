from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal
import uuid

import jinja2

from sofastats.conf.main import TEXT_WIDTH_N_CHARACTERS_WHEN_ROTATED, ChartMetric, SortOrder
import sofastats.data_extraction.charts.amounts as from_data
from sofastats.data_extraction.charts.interfaces.common import IndivChartSpec
from sofastats.output.charts.common import get_common_charting_spec, get_html, get_indiv_chart_html
from sofastats.output.charts.interfaces import ChartingSpecAxes, DojoSeriesSpec, JSBool, LeftMarginOffsetSpec
from sofastats.output.charts.utils import (get_axis_label_drop, get_left_margin_offset, get_height,
    get_dojo_format_x_axis_numbers_and_labels, get_width_after_left_margin, get_x_axis_font_size,
    get_y_axis_title_offset)
from sofastats.output.interfaces import (
    DEFAULT_SUPPLIED_BUT_MANDATORY_ANYWAY, HTMLItemSpec, OutputItemType, CommonBarDesign)
from sofastats.output.styles.interfaces import ColourWithHighlight, StyleSpec
from sofastats.output.styles.utils import get_long_colour_list, get_style_spec
from sofastats.utils.maths import format_num
from sofastats.utils.misc import todict

MIN_PIXELS_PER_X_ITEM = 60
MIN_CLUSTER_WIDTH_PIXELS = 60
PADDING_PIXELS = 35
DOJO_MINOR_TICKS_NEEDED_PER_X_ITEM = 10  ## whatever works. Tested on cluster of Age vs Cars


@dataclass(frozen=False)
class SimpleBarChartDesign(CommonBarDesign):
    style_name: str = 'default'

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
            cur=self.cur, dbe_spec=self.dbe_spec, src_tbl_name=self.source_table_name,
            category_field_name=self.category_field_name, sort_orders=self.sort_orders,
            category_sort_order=self.category_sort_order,
            metric=self.metric, field_name=self.field_name,
            tbl_filt_clause=self.table_filter)
        ## chart details
        charting_spec = BarChartingSpec(
            categories=intermediate_charting_spec.sorted_categories,
            indiv_chart_specs=[intermediate_charting_spec.to_indiv_chart_spec(), ],
            series_legend_label=None,
            rotate_x_labels=self.rotate_x_labels,
            show_borders=self.show_borders,
            show_n_records=self.show_n_records,
            x_axis_font_size=self.x_axis_font_size,
            x_axis_title=intermediate_charting_spec.category_field_name,
            y_axis_title=self.y_axis_title,
        )
        ## output
        html = get_html(charting_spec, style_spec)  ## see get_indiv_chart_html() below
        return HTMLItemSpec(
            html_item_str=html,
            style_name=self.style_name,
            output_item_type=OutputItemType.CHART,
        )


@dataclass(frozen=False)
class MultiBarChartDesign(CommonBarDesign):
    style_name: str = 'default'

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
            cur=self.cur, dbe_spec=self.dbe_spec, src_tbl_name=self.source_table_name,
            category_field_name=self.category_field_name, chart_field_name=self.chart_field_name,
            sort_orders=self.sort_orders,
            category_sort_order=self.category_sort_order, chart_sort_order=self.chart_sort_order,
            metric=self.metric, field_name=self.field_name,
            tbl_filt_clause=self.table_filter)
        ## charts details
        charting_spec = BarChartingSpec(
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
            style_name=self.style_name,
            output_item_type=OutputItemType.CHART,
        )


@dataclass(frozen=False)
class ClusteredBarChartDesign(CommonBarDesign):
    style_name: str = 'default'

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
            cur=self.cur, dbe_spec=self.dbe_spec, src_tbl_name=self.source_table_name,
            category_field_name=self.category_field_name, series_field_name=self.series_field_name,
            sort_orders=self.sort_orders,
            category_sort_order=self.category_sort_order, series_sort_order=self.series_sort_order,
            metric=self.metric, field_name=self.field_name,
            tbl_filt_clause=self.table_filter)
        ## chart details
        charting_spec = BarChartingSpec(
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
            style_name=self.style_name,
            output_item_type=OutputItemType.CHART,
        )


@dataclass(frozen=False)
class MultiChartClusteredBarChartDesign(CommonBarDesign):
    style_name: str = 'default'

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
            cur=self.cur, dbe_spec=self.dbe_spec, src_tbl_name=self.source_table_name,
            category_field_name=self.category_field_name,
            series_field_name=self.series_field_name,
            chart_field_name=self.chart_field_name,
            sort_orders=self.sort_orders,
            category_sort_order=self.category_sort_order,
            series_sort_order=self.series_sort_order,
            chart_sort_order=self.chart_sort_order,
            metric=self.metric, field_name=self.field_name,
            tbl_filt_clause=self.table_filter)
        ## chart details
        charting_spec = BarChartingSpec(
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
            style_name=self.style_name,
            output_item_type=OutputItemType.CHART,
        )

@dataclass
class BarChartingSpec(ChartingSpecAxes):
    show_borders: bool
    metric: ChartMetric = ChartMetric.FREQ

@dataclass(frozen=True)
class CommonColourSpec:
    axis_font: str
    chart_bg: str
    colour_cases: Sequence[str]
    colours: Sequence[str]
    major_grid_line: str
    plot_bg: str
    plot_font: str
    plot_font_filled: str
    tooltip_border: str

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
    connector_style: str
    grid_line_width: int
    height: float  ## pixels
    left_margin_offset: float
    metric: ChartMetric
    series_legend_label: str
    stroke_width: int
    width: float  ## pixels
    x_axis_numbers_and_labels: str  ## Format required by Dojo e.g. [{value: 1, text: "Female"}, {value: 2, text: "Male"}]
    x_axis_font_size: float
    x_axis_title: str
    x_gap: int
    y_axis_title: str
    y_axis_title_offset: int
    y_axis_max: int

@dataclass(frozen=True)
class CommonChartingSpec:
    """
    Ready to combine with individual chart spec and feed into the Dojo JS engine.
    """
    colour_spec: CommonColourSpec
    misc_spec: CommonMiscSpec
    options: CommonOptions

tpl_chart = """\
<script type="text/javascript">

var highlight_{{chart_uuid}} = function(colour){
    var hlColour;
    switch (colour.toHex()){
        {% for colour_case in colour_cases %}\n            {{colour_case}}; break;{% endfor %}
        default:
            hlColour = hl(colour.toHex());
            break;
    }
    return new dojox.color.Color(hlColour);
}

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
        conf["axis_font_colour"] = "{{axis_font}}";
        conf["axis_label_drop"] = {{axis_label_drop}};
        conf["axis_label_rotate"] = {{axis_label_rotate}};
        conf["chart_bg_colour"] = "{{chart_bg}}";
        conf["connector_style"] = "{{connector_style}}";
        conf["grid_line_width"] = {{grid_line_width}};
        conf["has_minor_ticks"] = {{has_minor_ticks_js_bool}};
        conf["highlight"] = highlight_{{chart_uuid}};
        conf["left_margin_offset"] = {{left_margin_offset}};
        conf["major_grid_line_colour"] = "{{major_grid_line}}";
        conf["n_records"] = "{{n_records}}";
        conf["plot_bg_colour"] = "{{plot_bg}}";
        conf["plot_font_colour"] = "{{plot_font}}";
        conf["plot_font_colour_filled"] = "{{plot_font_filled}}";
        conf["tooltip_border_colour"] = "{{tooltip_border}}";
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
    colour_mappings = style_spec.chart.colour_mappings
    if charting_spec.is_single_series:
        colour_mappings = colour_mappings[:1]  ## only need the first
        ## This is an important special case because it affects the bar charts using the default style
        if colour_mappings[0].main == '#e95f29':  ## BURNT_ORANGE
            colour_mappings = [ColourWithHighlight('#e95f29', '#736354'), ]
    colours = get_long_colour_list(colour_mappings)
    colour_cases = [f'case "{colour_mapping.main}": hlColour = "{colour_mapping.highlight}"'
        for colour_mapping in colour_mappings]  ## actually only need first one for simple bar charts
    ## misc
    dojo_format_x_axis_numbers_and_labels = get_dojo_format_x_axis_numbers_and_labels(charting_spec.categories)
    has_minor_ticks_js_bool: JSBool = 'true' if charting_spec.n_x_items >= DOJO_MINOR_TICKS_NEEDED_PER_X_ITEM else 'false'
    series_legend_label = '' if charting_spec.is_single_series else charting_spec.series_legend_label
    stroke_width = style_spec.chart.stroke_width if charting_spec.show_borders else 0
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
        widest_x_axis_label_n_characters=widest_x_axis_label_n_characters,
        widest_y_axis_label_n_characters=widest_y_axis_label_n_characters,
        avg_pixels_per_character=10.5,
    )
    ## misc sizing
    x_axis_font_size = get_x_axis_font_size(n_x_items=charting_spec.n_x_items, is_multi_chart=charting_spec.is_multi_chart)
    x_gap = get_x_gap(n_x_items=charting_spec.n_x_items, is_multi_chart=charting_spec.is_multi_chart)
    axis_label_drop = get_axis_label_drop(
        is_multi_chart=charting_spec.is_multi_chart, rotated_x_labels=charting_spec.rotate_x_labels,
        max_x_axis_label_lines=charting_spec.max_x_axis_label_lines)
    axis_label_rotate = -90 if charting_spec.rotate_x_labels else 0
    left_margin_offset_spec = LeftMarginOffsetSpec(
        initial_offset=25, wide_offset=35, rotate_offset=15, multi_chart_offset=15)
    left_margin_offset = get_left_margin_offset(width_after_left_margin=width_after_left_margin,
        offsets=left_margin_offset_spec, is_multi_chart=charting_spec.is_multi_chart,
        y_axis_title_offset=y_axis_title_offset, rotated_x_labels=charting_spec.rotate_x_labels)
    width = left_margin_offset + width_after_left_margin
    height = get_height(axis_label_drop=axis_label_drop,
        rotated_x_labels=charting_spec.rotate_x_labels, max_x_axis_label_len=charting_spec.max_x_axis_label_len)

    colour_spec = CommonColourSpec(
        axis_font=style_spec.chart.axis_font_colour,
        chart_bg=style_spec.chart.chart_bg_colour,
        colour_cases=colour_cases,
        colours=colours,
        major_grid_line=style_spec.chart.major_grid_line_colour,
        plot_bg=style_spec.chart.plot_bg_colour,
        plot_font=style_spec.chart.plot_font_colour,
        plot_font_filled=style_spec.chart.plot_font_colour_filled,
        tooltip_border=style_spec.chart.tooltip_border_colour,
    )
    misc_spec = CommonMiscSpec(
        axis_label_drop=axis_label_drop,
        axis_label_rotate=axis_label_rotate,
        connector_style=style_spec.dojo.connector_style,
        grid_line_width=style_spec.chart.grid_line_width,
        height=height,
        left_margin_offset=left_margin_offset,
        metric=charting_spec.metric,
        series_legend_label=series_legend_label,
        stroke_width=stroke_width,
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
    indiv_title_html = f"<p><b>{indiv_chart_spec.label}</b></p>" if common_charting_spec.options.is_multi_chart else ''
    n_records = 'N = ' + format_num(indiv_chart_spec.n_records) if common_charting_spec.options.show_n_records else ''
    dojo_series_specs = []
    for i, data_series_spec in enumerate(indiv_chart_spec.data_series_specs):
        series_id = f"{i:>02}"
        series_label = data_series_spec.label
        series_vals = str(data_series_spec.amounts)
        ## options e.g. {stroke: {color: "white", width: "0px"}, fill: "#e95f29", yLbls: ['66.38', ...]}
        fill_colour = common_charting_spec.colour_spec.colours[i]
        y_lbls_str = str(data_series_spec.tool_tips)
        options = (f"""{{stroke: {{color: "white", width: "{common_charting_spec.misc_spec.stroke_width}px"}}, """
            f"""fill: "{fill_colour}", yLbls: {y_lbls_str}}}""")
        dojo_series_specs.append(DojoSeriesSpec(series_id, series_label, series_vals, options))
    indiv_context = {
        'chart_uuid': chart_uuid,
        'dojo_series_specs': dojo_series_specs,
        'indiv_title_html': indiv_title_html,
        'n_records': n_records,
        'page_break': page_break,
    }
    context.update(indiv_context)
    environment = jinja2.Environment()
    template = environment.from_string(tpl_chart)
    html_result = template.render(context)
    return html_result
