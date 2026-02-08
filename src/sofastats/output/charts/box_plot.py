from collections.abc import Sequence
from dataclasses import dataclass
import uuid

import jinja2

from sofastats.conf.main import TEXT_WIDTH_N_CHARACTERS_WHEN_ROTATED, SortOrder, SortOrderSpecs
from sofastats.data_extraction.charts.box_plot import (BoxplotDataSeriesSpec, BoxplotChartingSpec,
    BoxplotIndivChartSpec, get_by_category_charting_spec, get_by_series_category_charting_spec)
from sofastats.output.charts.common import get_common_charting_spec, get_html, get_indiv_chart_html
from sofastats.output.charts.interfaces import JSBool
from sofastats.output.charts.utils import (get_axis_label_drop, get_height, get_dojo_format_x_axis_numbers_and_labels,
    get_intrusion_of_first_x_axis_label_leftwards, get_width_after_left_margin, get_x_axis_font_size,
    get_y_axis_title_offset)
from sofastats.output.interfaces import (
    DEFAULT_SUPPLIED_BUT_MANDATORY_ANYWAY, HTMLItemSpec, OutputItemType, CommonDesign)
from sofastats.output.styles.interfaces import ColorWithHighlight, ColorShiftJSFunctionName, StyleSpec
from sofastats.output.styles.utils import (
    get_js_highlighting_function, get_long_color_list, get_style_spec)
from sofastats.stats_calc.interfaces import BoxplotType
from sofastats.utils.item_sorting import sort_values_by_value_or_custom_if_possible
from sofastats.utils.maths import format_num
from sofastats.utils.misc import todict

@dataclass(frozen=True)
class DojoBoxSpec:
    """
    Has huge overlap with non_standard.BoxplotDataItem
    """
    center: float
    indiv_box_label: str
    box_bottom: float
    box_bottom_rounded: float
    bottom_whisker: float
    bottom_whisker_rounded: float
    median: float
    median_rounded: float
    outliers: Sequence[float] | None
    outliers_rounded: Sequence[float] | None
    box_top: float
    box_top_rounded: float
    top_whisker: float
    top_whisker_rounded: float

@dataclass(frozen=True)
class BoxplotDojoSeriesSpec:
    """
    Used for DOJO box-plots (which have series).
    Scatter-plots, and more general charts with series (e.g. bar charts and line charts),
    have different specs of their own for DOJO series.
    """
    border_color: str
    box_specs: Sequence[DojoBoxSpec]
    label: str
    series_id: str  ## e.g. 01

tpl_chart = """\
<script type="text/javascript">

{{js_highlighting_function}}

make_chart_{{chart_uuid}} = function(){
    // add each box to single multi-series
    var series_conf = new Array();  // for legend settings via dummy (invisible) chart
    var series = new Array();

    {% for series_spec in dojo_series_specs %}

        var series_conf_{{series_spec.series_id}} = new Array();
        series_conf_{{series_spec.series_id}} = {
          seriesLabel: "{{series_spec.label}}",
          seriesStyle: {
              stroke: {
                  color: getBrightHex("{{series_spec.border_color}}"),
                  width: "{{border_width}}px"
              },
              fill: "{{series_spec.border_color}}"
          }
        };
        series_conf.push(series_conf_{{series_spec.series_id}});

        // all of the actual series data (i.e. not just the legend details) is box-level i.e. nested under series

        {% for box_spec in series_spec.box_specs %}
            var box_{{series_spec.series_id}}_{{loop.index0}} = new Array();
            box_{{series_spec.series_id}}_{{loop.index0}}['stroke'] = getBrightHex("{{series_spec.border_color}}");
            box_{{series_spec.series_id}}_{{loop.index0}}['center'] = "{{box_spec.center}}";
            box_{{series_spec.series_id}}_{{loop.index0}}['fill'] = "{{series_spec.border_color}}";
            box_{{series_spec.series_id}}_{{loop.index0}}['width'] = {{bar_width}};
            box_{{series_spec.series_id}}_{{loop.index0}}['indiv_boxlbl'] = "{{box_spec.indiv_box_label}}";

            var summary_data_{{series_spec.series_id}}_{{loop.index0}} = new Array();
            summary_data_{{series_spec.series_id}}_{{loop.index0}}['bottom_whisker'] = {{box_spec.bottom_whisker}};
            summary_data_{{series_spec.series_id}}_{{loop.index0}}['bottom_whisker_rounded'] = {{box_spec.bottom_whisker_rounded}};
            summary_data_{{series_spec.series_id}}_{{loop.index0}}['box_bottom'] = {{box_spec.box_bottom}};
            summary_data_{{series_spec.series_id}}_{{loop.index0}}['box_bottom_rounded'] = {{box_spec.box_bottom_rounded}};
            summary_data_{{series_spec.series_id}}_{{loop.index0}}['median'] = {{box_spec.median}};
            summary_data_{{series_spec.series_id}}_{{loop.index0}}['median_rounded'] = {{box_spec.median_rounded}};
            summary_data_{{series_spec.series_id}}_{{loop.index0}}['box_top'] = {{box_spec.box_top}};
            summary_data_{{series_spec.series_id}}_{{loop.index0}}['box_top_rounded'] = {{box_spec.box_top_rounded}};
            summary_data_{{series_spec.series_id}}_{{loop.index0}}['top_whisker'] = {{box_spec.top_whisker}};
            summary_data_{{series_spec.series_id}}_{{loop.index0}}['top_whisker_rounded'] = {{box_spec.top_whisker_rounded}};
            summary_data_{{series_spec.series_id}}_{{loop.index0}}['outliers'] = {{box_spec.outliers}};
            summary_data_{{series_spec.series_id}}_{{loop.index0}}['outliers_rounded'] = {{box_spec.outliers_rounded}};
            box_{{series_spec.series_id}}_{{loop.index0}}['summary_data'] = summary_data_{{series_spec.series_id}}_{{loop.index0}};

            series.push(box_{{series_spec.series_id}}_{{loop.index0}});

        {% endfor %}

    {% endfor %}  // series_spec

    var conf = new Array();
        conf["axis_font_color"] = "{{axis_font}}";
        conf["axis_label_drop"] = {{axis_label_drop}};
        conf["axis_label_rotate"] = {{axis_label_rotate}};
        conf["border_width"] = {{border_width}};
        conf["chart_background_color"] = "{{chart_background}}";
        conf["connector_style"] = "{{tool_tip_name}}";
        conf["grid_line_width"] = {{grid_line_width}};
        conf["has_minor_ticks"] = {{has_minor_ticks_js_bool}};
        conf["highlight"] = highlight_{{chart_uuid}};
        conf["left_margin_offset"] = {{left_margin_offset}};
        conf["n_records"] = "{{n_records}}";
        conf["plot_background_color"] = "{{plot_background}}";
        conf["plot_font_color"] = "{{plot_font}}";
        conf["tool_tip_border_color"] = "{{tool_tip_border}}";
        conf["x_axis_numbers_and_labels"] = {{x_axis_numbers_and_labels}};
        conf["x_axis_title"] = "{{x_axis_title}}";
        conf["x_axis_font_size"] = {{x_axis_font_size}};
        conf["x_axis_max_val"] = {{x_axis_max_val}};
        conf["y_axis_max_val"] = {{y_axis_max_val}};
        conf["y_axis_min_val"] = {{y_axis_min_val}};
        conf["y_axis_title"] = "{{y_axis_title}}";
        conf["y_axis_title_offset"] = {{y_axis_title_offset}};

    makeBoxAndWhisker("boxplot_{{chart_uuid}}", series, series_conf, conf);
}
</script>

<div class="screen-float-only" style="margin-right: 10px; {{page_break}}">
{{indiv_title_html}}
    <div id="boxplot_{{chart_uuid}}"
        style="width: {{width}}px; height: {{height}}px;">
    </div>
    {% if series_legend_label %}
        <p style="float: left; font-weight: bold; margin-right: 12px; margin-top: 9px;">
            {{series_legend_label}}:
        </p>
        <div id="dummy_boxplot_{{chart_uuid}}"
            style="float: right; width: 100px; height: 100px; visibility: hidden;">
        </div>
        <div id="legend_for_boxplot_{{chart_uuid}}">
        </div>
    {% endif %}
</div>
"""

@dataclass(frozen=False)
class CommonColorSpec:
    axis_font: str
    chart_background: str
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
    has_minor_ticks_js_bool: JSBool
    show_n_records: bool

@dataclass(frozen=True)
class CommonMiscSpec:
    axis_label_drop: int
    axis_label_rotate: int
    border_width: int
    grid_line_width: int
    height: float  ## pixels
    left_margin_offset: float
    series_legend_label: str
    tool_tip_name: str
    width: float  ## pixels
    x_axis_numbers_and_labels: str  ## Format required by Dojo e.g. [{value: 1, text: "Female"}, {value: 2, text: "Male"}]
    x_axis_font_size: float
    x_axis_max_val: float
    x_axis_title: str
    y_axis_title: str
    y_axis_title_offset: float
    y_axis_max_val: float
    y_axis_min_val: float

@dataclass(frozen=True)
class CommonChartingSpec:
    """
    Ready to combine with individual chart spec and feed into the Dojo JS engine.
    """
    color_spec: CommonColorSpec
    misc_spec: CommonMiscSpec
    options: CommonOptions

@get_common_charting_spec.register
def get_common_charting_spec(charting_spec: BoxplotChartingSpec, style_spec: StyleSpec) -> CommonChartingSpec:
    color_mappings = style_spec.chart.color_mappings
    ## misc
    axis_label_drop = get_axis_label_drop(
        is_multi_chart=False, rotated_x_labels=charting_spec.rotate_x_labels,
        max_x_axis_label_lines=charting_spec.max_x_axis_label_lines)
    axis_label_rotate = -90 if charting_spec.rotate_x_labels else 0
    has_minor_ticks_js_bool: JSBool = 'true' if charting_spec.has_minor_ticks else 'false'
    series_legend_label = '' if charting_spec.is_single_series else charting_spec.series_legend_label
    dojo_format_x_axis_numbers_and_labels = get_dojo_format_x_axis_numbers_and_labels(charting_spec.categories)
    ## sizing
    height = get_height(axis_label_drop=axis_label_drop,
        rotated_x_labels=charting_spec.rotate_x_labels, max_x_axis_label_len=charting_spec.max_x_axis_label_len)
    max_x_label_width = (
        TEXT_WIDTH_N_CHARACTERS_WHEN_ROTATED if charting_spec.rotate_x_labels else charting_spec.max_x_axis_label_len)
    width_after_left_margin = get_width_after_left_margin(
        n_x_items=charting_spec.n_x_items, n_items_horizontally_per_x_item=charting_spec.n_series, min_pixels_per_sub_item=50,
        x_item_padding_pixels=2, sub_item_padding_pixels=5,
        x_axis_title=charting_spec.x_axis_title,
        widest_x_label_n_characters=max_x_label_width, avg_pixels_per_character=8,
        min_chart_width_one_item=200, min_chart_width_multi_item=400,
        is_multi_chart=False,  ## haven't made multi-chart box-plots
        multi_chart_size_scalar=0.9)
    ## y-axis offset
    x_labels = charting_spec.categories
    first_x_label = x_labels[0]
    widest_x_axis_label_n_characters = (
        TEXT_WIDTH_N_CHARACTERS_WHEN_ROTATED if charting_spec.rotate_x_labels else len(first_x_label))
    y_axis_max = charting_spec.y_axis_max_val * 1.1
    widest_y_axis_label_n_characters = len(str(int(y_axis_max)))  ## e.g. 1000.5 -> 1000 -> '1000' -> 4
    y_axis_title_offset = get_y_axis_title_offset(
        widest_y_axis_label_n_characters=widest_y_axis_label_n_characters, avg_pixels_per_y_character=8)
    intrusion_of_first_x_axis_label_leftwards = get_intrusion_of_first_x_axis_label_leftwards(
        widest_x_axis_label_n_characters=widest_x_axis_label_n_characters, avg_pixels_per_x_character=5)
    left_margin_offset = max(y_axis_title_offset, intrusion_of_first_x_axis_label_leftwards) - 35
    ## other sizing
    x_axis_font_size = get_x_axis_font_size(n_x_items=charting_spec.n_x_items, is_multi_chart=False)
    width = left_margin_offset + width_after_left_margin

    color_spec = CommonColorSpec(
        axis_font=style_spec.chart.axis_font_color,
        chart_background=style_spec.chart.chart_background_color,
        color_mappings=color_mappings,
        major_grid_line=style_spec.chart.major_grid_line_color,
        plot_background=style_spec.chart.plot_background_color,
        plot_font=style_spec.chart.plot_font_color,
        tool_tip_border=style_spec.chart.tool_tip_border_color,
    )
    misc_spec = CommonMiscSpec(
        axis_label_drop=axis_label_drop,
        axis_label_rotate=axis_label_rotate,
        border_width=style_spec.chart.border_width,
        grid_line_width=style_spec.chart.grid_line_width,
        height=height,
        left_margin_offset=left_margin_offset,
        series_legend_label=series_legend_label,
        tool_tip_name=style_spec.dojo.tool_tip_name,
        width=width,
        x_axis_numbers_and_labels=dojo_format_x_axis_numbers_and_labels,
        x_axis_font_size=x_axis_font_size,
        x_axis_max_val=charting_spec.x_axis_max_val,
        x_axis_title=charting_spec.x_axis_title,
        y_axis_max_val=y_axis_max,
        y_axis_min_val=charting_spec.y_axis_min_val,
        y_axis_title=charting_spec.y_axis_title,
        y_axis_title_offset=y_axis_title_offset,
    )
    options = CommonOptions(
        has_minor_ticks_js_bool=has_minor_ticks_js_bool,
        show_n_records=charting_spec.show_n_records,
    )
    return CommonChartingSpec(
        color_spec=color_spec,
        misc_spec=misc_spec,
        options=options,
    )

def to_sorted_data_series_specs(*, data_series_specs: Sequence[BoxplotDataSeriesSpec], series_field_name: str,
        sort_orders: SortOrderSpecs, series_sort_order: SortOrder) -> list[BoxplotDataSeriesSpec]:
    if series_sort_order == SortOrder.VALUE:
        def sort_me(data_series_spec):
            return data_series_spec.label

        reverse = False
    elif series_sort_order == SortOrder.CUSTOM:
        ## use supplied sort order
        try:
            values_in_order = sort_orders[series_field_name]
        except KeyError:
            raise Exception(
                f"You wanted the values in variable '{series_field_name}' to have a custom sort order "
                "but I couldn't find a sort order from what you supplied. "
                "Please fix the sort order details or use another approach to sorting.")
        value2order = {val: order for order, val in enumerate(values_in_order)}

        def sort_me(data_series_spec):
            amount_spec_val = data_series_spec.label
            try:
                idx_for_ordered_position = value2order[amount_spec_val]
            except KeyError:
                raise Exception(
                    f"The custom sort order you supplied for values in variable '{series_field_name}' "
                    f"didn't include value '{amount_spec_val}' so please fix that and try again.")
            return idx_for_ordered_position

        reverse = False
    else:
        raise Exception(
            f"Unexpected series_sort_order ({series_sort_order})"
            "\nINCREASING and DECREASING is for ordering by frequency which makes no sense for series."
        )
    sorted_amount_specs = sorted(data_series_specs, key=sort_me, reverse=reverse)
    return sorted_amount_specs

@get_indiv_chart_html.register
def get_indiv_chart_html(common_charting_spec: CommonChartingSpec, indiv_chart_spec: BoxplotIndivChartSpec,
        *,  chart_counter: int) -> str:
    """
    For box-plots there is only ever one chart so the series values for a single chart are the full set.
    """
    context = todict(common_charting_spec.color_spec, shallow=True)
    context.update(todict(common_charting_spec.misc_spec, shallow=True))
    context.update(todict(common_charting_spec.options, shallow=True))
    chart_uuid = str(uuid.uuid4()).replace('-', '_')  ## needs to work in JS variable names
    page_break = 'page-break-after: always;' if chart_counter % 2 == 0 else ''

    border_width = common_charting_spec.misc_spec.border_width
    bar_width = indiv_chart_spec.bar_width
    n_records = 'N = ' + format_num(indiv_chart_spec.n_records) if common_charting_spec.options.show_n_records else ''

    dojo_series_specs = []
    if len(indiv_chart_spec.data_series_specs) == 1:
        sorted_data_series_specs = indiv_chart_spec.data_series_specs
    else:
        sorted_data_series_specs = to_sorted_data_series_specs(
            data_series_specs=indiv_chart_spec.data_series_specs, series_field_name=indiv_chart_spec.series_field_name,
            sort_orders=indiv_chart_spec.sort_orders, series_sort_order=indiv_chart_spec.series_sort_order)
    for i, data_series_spec in enumerate(sorted_data_series_specs):
        series_id = f"{i:>02}"
        border_color = common_charting_spec.color_spec.colors[i]  ## the border drives the colour of box plots - the fill is slightly paler, and the hover fill is in between
        box_specs = []


        ## TODO: control sort order here


        for box_item in data_series_spec.box_items:
            if not box_item:
                continue
            has_outliers = bool(box_item.outliers)
            if has_outliers:
                outliers = box_item.outliers
                outliers_rounded = box_item.outliers_rounded
            else:
                outliers = []
                outliers_rounded = []
            box_spec = DojoBoxSpec(
                center=box_item.center,
                indiv_box_label=box_item.indiv_box_label,
                box_bottom=box_item.box_bottom,
                box_bottom_rounded=box_item.box_bottom_rounded,
                bottom_whisker=box_item.bottom_whisker,
                bottom_whisker_rounded=box_item.bottom_whisker_rounded,
                median=box_item.median,
                median_rounded=box_item.median_rounded,
                outliers=outliers,
                outliers_rounded=outliers_rounded,
                box_top=box_item.box_top,
                box_top_rounded=box_item.box_top_rounded,
                top_whisker=box_item.top_whisker,
                top_whisker_rounded=box_item.top_whisker_rounded,
            )
            box_specs.append(box_spec)
        series_spec = BoxplotDojoSeriesSpec(
            border_color=border_color,
            box_specs=box_specs,
            label=data_series_spec.label,
            series_id=series_id,
        )
        dojo_series_specs.append(series_spec)
    js_highlighting_function = get_js_highlighting_function(
        color_mappings=common_charting_spec.color_spec.color_mappings, chart_uuid=chart_uuid,
        fn_used_to_make_fill=None, fn_desired_on_highlight_color=ColorShiftJSFunctionName.HALF_BRIGHT,
    )
    indiv_context = {
        'bar_width': bar_width,
        'border_width': border_width,
        'chart_uuid': chart_uuid,
        'dojo_series_specs': dojo_series_specs,
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
class BoxplotChartDesign(CommonDesign):
    """
    Args:
        field_name: field summarised in each box
        category_field_name: name of field in the x-axis
        category_sort_order: define order of categories in each chart e.g. `SortOrder.VALUES` or `SortOrder.CUSTOM`
        box_plot_type: options for what the boxes represent and whether outliers are displayed or not.
        rotate_x_labels: make x-axis labels vertical
        show_n_records: show the number of records the chart is based on
        x_axis_font_size: font size for x-axis labels
    """
    field_name: str = DEFAULT_SUPPLIED_BUT_MANDATORY_ANYWAY
    category_field_name: str = DEFAULT_SUPPLIED_BUT_MANDATORY_ANYWAY
    category_sort_order: SortOrder = SortOrder.VALUE

    box_plot_type: BoxplotType = BoxplotType.INSIDE_1_POINT_5_TIMES_IQR
    rotate_x_labels: bool = False
    show_n_records: bool = True
    x_axis_font_size: int = 12

    def to_html_design(self) -> HTMLItemSpec:
        # style
        style_spec = get_style_spec(style_name=self.style_name)
        ## data
        intermediate_charting_spec = get_by_category_charting_spec(
            cur=self.cur, dbe_spec=self.dbe_spec, source_table_name=self.source_table_name,
            field_name=self.field_name,
            category_field_name=self.category_field_name,
            sort_orders=self.sort_orders,
            category_sort_order=self.category_sort_order,
            table_filter_sql=self.table_filter_sql,
            box_plot_type=self.box_plot_type)
        ## charts details
        unsorted_categories = [
            category_vals_spec.category_val for category_vals_spec in intermediate_charting_spec.category_vals_specs]
        categories = sort_values_by_value_or_custom_if_possible(variable_name=self.category_field_name, values=unsorted_categories,
                                                                sort_orders=self.sort_orders, sort_order=self.category_sort_order)
        indiv_chart_spec = intermediate_charting_spec.to_indiv_chart_spec()
        charting_spec = BoxplotChartingSpec(
            categories=categories,
            indiv_chart_specs=[indiv_chart_spec, ],
            series_legend_label=None,
            rotate_x_labels=self.rotate_x_labels,
            show_n_records=self.show_n_records,
            x_axis_title=intermediate_charting_spec.category_field_name,
            y_axis_title=intermediate_charting_spec.field_name,
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
class ClusteredBoxplotChartDesign(CommonDesign):
    """
    Args:
        series_field_name: the field name defining the series e.g. a `series_field_name` of 'Country'
            might separate generate boxes within each category cluster for 'USA', 'NZ', 'Denmark', and 'South Korea'.
        series_sort_order: define order of series within each category cluster e.g. `SortOrder.VALUES` or `SortOrder.CUSTOM`
    """
    field_name: str = DEFAULT_SUPPLIED_BUT_MANDATORY_ANYWAY
    category_field_name: str = DEFAULT_SUPPLIED_BUT_MANDATORY_ANYWAY
    category_sort_order: SortOrder = SortOrder.VALUE
    series_field_name: str = DEFAULT_SUPPLIED_BUT_MANDATORY_ANYWAY
    series_sort_order: SortOrder = SortOrder.VALUE

    box_plot_type: BoxplotType = BoxplotType.INSIDE_1_POINT_5_TIMES_IQR
    rotate_x_labels: bool = False
    show_n_records: bool = True
    x_axis_font_size: int = 12

    def to_html_design(self) -> HTMLItemSpec:
        # style
        style_spec = get_style_spec(style_name=self.style_name)
        ## data
        intermediate_charting_spec = get_by_series_category_charting_spec(
            cur=self.cur, dbe_spec=self.dbe_spec, source_table_name=self.source_table_name,
            field_name=self.field_name,
            category_field_name=self.category_field_name,
            series_field_name=self.series_field_name,
            sort_orders=self.sort_orders,
            category_sort_order=self.category_sort_order,
            series_sort_order=self.series_sort_order,
            table_filter_sql=self.table_filter_sql,
            box_plot_type=self.box_plot_type)
        ## charts details
        all_unsorted_category_values = set()
        for boxplot_series_item_category_vals_specs in intermediate_charting_spec.series_category_vals_specs:
            for category_vals_spec in boxplot_series_item_category_vals_specs.category_vals_specs:
                all_unsorted_category_values.add(category_vals_spec.category_val)
        all_unsorted_category_values = sorted(all_unsorted_category_values)
        categories = sort_values_by_value_or_custom_if_possible(
            variable_name=self.category_field_name, values=all_unsorted_category_values,
            sort_orders=self.sort_orders, sort_order=self.category_sort_order)
        indiv_chart_spec = intermediate_charting_spec.to_indiv_chart_spec(dp=self.decimal_points)
        charting_spec = BoxplotChartingSpec(
            categories=categories,
            indiv_chart_specs=[indiv_chart_spec, ],
            series_legend_label=intermediate_charting_spec.series_field_name,
            rotate_x_labels=self.rotate_x_labels,
            show_n_records=self.show_n_records,
            x_axis_title=intermediate_charting_spec.category_field_name,
            y_axis_title=intermediate_charting_spec.field,
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
