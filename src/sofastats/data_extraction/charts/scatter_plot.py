from collections.abc import Sequence
from dataclasses import dataclass

from sofastats.conf.main import SortOrder, SortOrderSpecs
from sofastats.stats_calc.utils import get_optimal_axis_bounds

@dataclass
class ScatterDataSeriesSpec:
    label: str | None
    xy_pairs: Sequence[tuple[float, float]]

@dataclass
class ScatterIndivChartSpec:
    series_field_name: str | None
    sort_orders: SortOrderSpecs | None
    series_sort_order: SortOrder | None
    data_series_specs: Sequence[ScatterDataSeriesSpec]
    label: str | None

    def __post_init__(self):
        n_records = 0
        for data_series_spec in self.data_series_specs:
            n_records += len(data_series_spec.xy_pairs)
        self.n_records = n_records

@dataclass
class ScatterChartingSpec:
    indiv_chart_specs: Sequence[ScatterIndivChartSpec]
    series_legend_label: str | None
    show_dot_borders: bool
    show_n_records: bool
    show_regression_line: bool
    x_axis_font_size: int
    x_axis_title: str
    y_axis_title: str

    def __post_init__(self):
        ## Derived attributes (could make actual fields using = fields(init=False) but OK as mere attributes)
        all_min_xs = []
        all_max_xs = []
        all_min_ys = []
        all_max_ys = []
        has_plenty_list = []
        for indiv_chart_spec in self.indiv_chart_specs:
            for data_series_spec in indiv_chart_spec.data_series_specs:
                xs = [xy_pair[0] for xy_pair in data_series_spec.xy_pairs]
                ys = [xy_pair[1] for xy_pair in data_series_spec.xy_pairs]
                ## xs
                indiv_x_axis_min_val = min(xs)
                all_min_xs.append(indiv_x_axis_min_val)
                indiv_max_x_val = max(xs)
                all_max_xs.append(indiv_max_x_val)
                ## ys
                indiv_min_y_val = min(ys)
                all_min_ys.append(indiv_min_y_val)
                indiv_max_y_val = max(ys)
                all_max_ys.append(indiv_max_y_val)
                ## has_ticks
                x_set = set(xs)
                has_plenty_unique_x_vals = len(x_set) >= 4
                has_plenty_list.append(has_plenty_unique_x_vals)
        ## If any of the series in any of the charts have plenty of distinct x-values
        ## keep the minor ticks - otherwise drop them
        self.has_minor_ticks = any(has_plenty_list)
        min_x_val = min(all_min_xs)
        max_x_val = max(all_max_xs)
        self.x_axis_min_val, self.x_axis_max_val = get_optimal_axis_bounds(min_x_val, max_x_val)
        min_y_val = min(all_min_ys)
        max_y_val = max(all_max_ys)
        self.y_axis_min_val, self.y_axis_max_val = get_optimal_axis_bounds(min_y_val, max_y_val)
        ## Derived attributes (could make actual fields using = fields(init=False) but OK as mere attributes)
        self.n_charts = len(self.indiv_chart_specs)
        self.is_multi_chart = self.n_charts > 1
        self.n_series = len(self.indiv_chart_specs[0].data_series_specs)
        self.is_single_series = (self.n_series == 1)
