## depends on conf (always OK), and utils and data_extraction which are lower level - so no problematic project dependencies :-)
from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Literal

from sofastats.data_extraction.charts.interfaces.common import IndivChartSpec
from sofastats.utils.dates import get_epoch_secs_from_datetime_str

JSBool = Literal['false', 'true']

## the lower-level components are needed by data_extraction e.g. IndivChartSpec

@dataclass(frozen=False, kw_only=True)
class ChartingSpec:
    categories: Sequence[Any]
    indiv_chart_specs: Sequence[IndivChartSpec]
    show_n_records: bool
    decimal_points: int = 3

    def __post_init__(self):
        ## Validation
        ## Check number of categories matches number of data items in every series
        n_categories = len(self.categories)
        for indiv_chart_spec in self.indiv_chart_specs:
            for data_series_spec in indiv_chart_spec.data_series_specs:
                n_data_items = len(data_series_spec.data_items)
                if n_data_items != n_categories:
                    raise Exception(
                        "Must be same number of categories as data items in every series in every individual chart "
                        f"but {n_categories=} while {n_data_items=}")
        ## Derived attributes (could make actual fields using = fields(init=False) but OK as mere attributes)
        self.n_charts = len(self.indiv_chart_specs)
        self.is_multi_chart = self.n_charts > 1
        self.n_series = len(self.indiv_chart_specs[0].data_series_specs)
        self.is_single_series = (self.n_series == 1)

@dataclass
class ChartingSpecAxes(ChartingSpec):

    series_legend_label: str | None
    rotate_x_labels: bool
    x_axis_font_size: int
    x_axis_title: str
    y_axis_title: str

    def __post_init__(self):
        """
        Check number of categories matches number of data items in every series
        """
        super().__post_init__()
        ## derived attributes
        self.n_x_items = len(self.categories)

        max_x_axis_label_len = 0
        max_x_axis_label_lines = 0
        for category in self.categories:
            x_axis_label_len = len(str(category))
            if x_axis_label_len > max_x_axis_label_len:
                max_x_axis_label_len = x_axis_label_len
            x_label_lines = len(str(category).split('<br>'))
            if x_label_lines > max_x_axis_label_lines:
                max_x_axis_label_lines = x_label_lines

        max_y_val = 0
        for indiv_chart_spec in self.indiv_chart_specs:
            for data_series_spec in indiv_chart_spec.data_series_specs:
                for data_item in data_series_spec.data_items:
                    if data_item is None:
                        continue
                    y_val = data_item.amount
                    if y_val > max_y_val:
                        max_y_val = y_val

        self.max_x_axis_label_len = max_x_axis_label_len  ## may be needed to set chart height if labels are rotated
        self.max_x_axis_label_lines = max_x_axis_label_lines  ## used to set axis label drop
        self.max_y_val = max_y_val

@dataclass
class AreaChartingSpec(ChartingSpecAxes):
    is_time_series: bool
    show_major_ticks_only: bool
    show_markers: bool

@dataclass
class LineChartingSpec(ChartingSpecAxes):
    is_time_series: bool
    show_major_ticks_only: bool
    show_markers: bool
    show_smooth_line: bool
    show_trend_line: bool

    def __post_init__(self):
        super().__post_init__()
        if (self.show_smooth_line or self.show_trend_line) and not self.is_single_series:
            raise Exception("Only single-series line charts can have a trend line or the smoothed option.")

@dataclass
class ChartingSpecNoAxes(ChartingSpec):
    def __post_init__(self):
        super().__post_init__()


## DOJO chart specs
## =====================================================================================================================

class PlotStyle(StrEnum):
    """
    Line / Area chart plot style (markers etc.)
    Self-defined plot names added with addPlot in the sofastats chart js file.
    Each has different settings re: tension and markers.
    """
    UNMARKED = 'unmarked'
    DEFAULT = 'default'
    CURVED = 'curved'

@dataclass(frozen=True)
class DojoSeriesSpec:
    """
    Used for DOJO charts which have series e.g. a bar chart or a line chart.
    Box plots and scatter plots have different and specific specs of their own for DOJO series.
    """
    series_id: str  ## e.g. 01
    label: str
    vals: Sequence[float | str]  ## str if time series
    options: str  ## e.g. stroke, color, width etc. - things needed in a generic DOJO series


class LineArea:
    """
    Used by both Line AND Area charts so not in the individual modules as you would otherwise expect
    """

    MIN_PIXELS_PER_X_ITEM = 10
    DOJO_MINOR_TICKS_NEEDED_PER_X_ITEM = 8
    DOJO_MICRO_TICKS_NEEDED_PER_X_ITEM = 100

    DUMMY_TOOL_TIPS = ['', ]  ## no labels or markers on trend line so dummy tool tips OK

    tpl_chart = """
    <script type="text/javascript">

    make_chart_{{chart_uuid}} = function(){

        var series = new Array();
        {% for series_spec in dojo_series_specs %}
          var series_{{series_spec.series_id}} = new Array();
              series_{{series_spec.series_id}}["label"] = "{{series_spec.label}}";
              series_{{series_spec.series_id}}["vals"] = {{series_spec.vals}};
              // options - line_colour, fill_colour, y_labels_str
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
            conf["left_margin_offset"] = {{left_margin_offset}};
            conf["major_grid_line_color"] = "{{major_grid_line}}";
            conf["has_minor_ticks"] = {{has_minor_ticks_js_bool}};
            conf["n_records"] = "{{n_records}}";
            conf["plot_background_color"] = "{{plot_background}}";
            conf["plot_font_color"] = "{{plot_font}}";
            conf["tool_tip_border_color"] = "{{tool_tip_border}}";
            conf["x_axis_font_size"] = {{x_axis_font_size}};
            conf["x_axis_numbers_and_labels"] = {{x_axis_numbers_and_labels}};
            conf["y_axis_max"] = {{y_axis_max}};
            conf["x_axis_title"] = "{{x_axis_title}}";
            conf["y_axis_title"] = "{{y_axis_title}}";
            conf["y_axis_title_offset"] = {{y_axis_title_offset}};
            // distinct fields for line charts
            conf["has_micro_ticks"] = {{has_micro_ticks_js_bool}};
            conf["is_time_series"] = {{is_time_series_js_bool}};

        {{chart_js_fn_name}}("line_area_chart_{{chart_uuid}}", series, conf);
    }
    </script>

    <div class="screen-float-only" style="margin-right: 10px; {{page_break}}">
    {{indiv_title_html}}
        <div id="line_area_chart_{{chart_uuid}}"
            style="width: {{width}}px; height: {{height}}px;">
        </div>
        {% if series_legend_label %}
            <p style="float: left; font-weight: bold; margin-right: 12px; margin-top: 9px;">
                {{series_legend_label}}:
            </p>
            <div id="legend_for_line_area_chart_{{chart_uuid}}">
            </div>
        {% endif %}
    </div>
    """

    @dataclass(frozen=True)
    class CommonColorSpec:
        axis_font: str
        chart_background: str
        chart_title_font: str
        major_grid_line: str
        plot_background: str
        plot_font: str
        tool_tip_border: str

    @dataclass(frozen=True)
    class CommonOptions:
        has_micro_ticks_js_bool: Literal['true', 'false']
        has_minor_ticks_js_bool: Literal['true', 'false']
        is_multi_chart: bool
        is_single_series: bool
        is_time_series: bool
        is_time_series_js_bool: Literal['true', 'false']
        show_markers: bool
        show_n_records: bool
        # show_smooth_line: bool  ## line
        # show_trend_line: bool  ## line

    @dataclass(frozen=True)
    class CommonMiscSpec:
        chart_js_fn_name: str
        axis_label_drop: int
        axis_label_rotate: int
        connector_style: str
        grid_line_width: int
        height: float  ## pixels
        left_margin_offset: float
        series_legend_label: str
        x_axis_font_size: float
        x_axis_numbers_and_labels: str  ## Format required by Dojo e.g. [{value: 1, text: "Female"}, {value: 2, text: "Male"}]
        x_axis_categories: Sequence[Any] | None
        x_axis_title: str
        y_axis_title: str
        y_axis_max: float
        y_axis_title_offset: int
        width: float  ## pixels

    @staticmethod
    def get_time_series_vals(x_axis_datetimes: Sequence[str], y_vals: Sequence[float], x_axis_title: str) -> str:
        """
        The time series values are what is displayed on the chart, not the axis.
        For the axis, we don't want to show any labels.
        """
        xs = []
        try:
            for x_axis_datetime in x_axis_datetimes:
                xs.append(get_epoch_secs_from_datetime_str(x_axis_datetime) * 1_000)
        except Exception as e:
            raise Exception(f"Problem processing x-axis specs for {x_axis_title}. Orig error: {e}")
        ys = y_vals
        xys = zip(xs, ys, strict=True)
        series_vals = str([{'x': xy[0], 'y': xy[1]} for xy in xys])
        return series_vals
