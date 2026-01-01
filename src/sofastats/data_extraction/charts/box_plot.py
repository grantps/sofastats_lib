from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

import pandas as pd

from sofastats.conf.main import DbeSpec, SortOrder, SortOrderSpecs
from sofastats.data_extraction.db import ExtendedCursor
from sofastats.stats_calc.interfaces import BoxResult, BoxplotType
from sofastats.data_extraction.utils import to_sorted_values
from sofastats.stats_calc.utils import get_optimal_axis_bounds

@dataclass(frozen=False)
class BoxplotCategoryItemValsSpec:
    category_val: float | str  ## e.g. 1, or Japan
    vals: Sequence[float]

@dataclass(frozen=False)
class BoxplotSeriesItemCategoryValsSpecs:
    series_val: float | str  ## e.g. 1, or Male
    category_vals_specs: Sequence[BoxplotCategoryItemValsSpec]

@dataclass(frozen=False)
class BoxplotDataItem:
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
    indiv_box_label: str | None = None  ## derived later from series label and category spec labels in BoxplotChartingSpec
    center: float | None = None  ## derived later from offset depending on which item on series (move rightwards) in BoxplotIndivChartSpec

@dataclass
class BoxplotDataSeriesSpec:
    label: str | None
    box_items: Sequence[BoxplotDataItem | None]  ## Use None to indicate a gap for a particular series e.g. US missing
    ## offset - set in BoxplotIndivChartSpec

@dataclass
class BoxplotIndivChartSpec:
    data_series_specs: Sequence[BoxplotDataSeriesSpec]
    n_records: int

    def __post_init__(self):
        n_series = len(self.data_series_specs)
        n_gaps = n_series - 1
        shrinkage = n_series * 0.6
        gap = 0.4 / shrinkage
        self.bar_width = 0.15 / shrinkage
        ## offset (left or right of whatever center is, offset is the same for all boxes in series)
        ## and actual center (different for every box in chart so boxes don't overlap / collide etc)
        offset_start = -((gap * n_gaps) / 2)  ## if only one box, offset = 0 i.e. middle
        for series_i, data_series_spec in enumerate(self.data_series_specs):
            data_series_spec.offset = offset_start + (series_i * gap)
            for box_n, box_item in enumerate(data_series_spec.box_items, 1):
                if not box_item:
                    continue
                box_item.center = box_n + data_series_spec.offset

@dataclass(frozen=False)
class BoxplotCategoryValsSpecs:
    field_name: str
    category_field_name: str  ## e.g. Country
    series_field_name: str | None
    chart_name: str | None
    category_vals_specs: Sequence[BoxplotCategoryItemValsSpec]
    category_sort_order: SortOrder
    boxplot_type: BoxplotType

    def to_indiv_chart_spec(self, *, dp: int = 3) -> BoxplotIndivChartSpec:
        n_records = 0
        box_items = []
        for category_vals_spec in self.category_vals_specs:
            n_records += len(category_vals_spec.vals)
            box_result = BoxResult(category_vals_spec.vals, self.boxplot_type)
            box_item = BoxplotDataItem(
                box_bottom=box_result.box_bottom,
                box_bottom_rounded=round(box_result.box_bottom, dp),
                bottom_whisker=box_result.bottom_whisker,
                bottom_whisker_rounded=round(box_result.bottom_whisker, dp),
                median=box_result.median,
                median_rounded=round(box_result.median, dp),
                outliers=box_result.outliers,
                outliers_rounded=[round(outlier, dp) for outlier in box_result.outliers],
                box_top=box_result.box_top,
                box_top_rounded=round(box_result.box_top, dp),
                top_whisker=box_result.top_whisker,
                top_whisker_rounded=round(box_result.top_whisker, dp)
            )
            box_items.append(box_item)
        data_series_spec = BoxplotDataSeriesSpec(
            label=None,
            box_items=box_items,
        )
        indiv_chart_spec = BoxplotIndivChartSpec(
            data_series_specs=[data_series_spec, ],
            n_records=n_records,
        )
        return indiv_chart_spec

def get_by_category_charting_spec(*, cur: ExtendedCursor, dbe_spec: DbeSpec, src_tbl_name: str,
        field_name: str, category_field_name: str,
        sort_orders: SortOrderSpecs,
        category_sort_order: SortOrder = SortOrder.VALUE,
        boxplot_type: BoxplotType = BoxplotType.INSIDE_1_POINT_5_TIMES_IQR,
        tbl_filt_clause: str | None = None,) -> BoxplotCategoryValsSpecs:
    ## prepare items
    field_name_quoted = dbe_spec.entity_quoter(field_name)
    category_field_name_quoted = dbe_spec.entity_quoter(category_field_name)
    src_tbl_name_quoted = dbe_spec.entity_quoter(src_tbl_name)
    and_tbl_filt_clause = f"AND ({tbl_filt_clause})" if tbl_filt_clause else ''
    ## assemble SQL
    sql = f"""\
    SELECT
        {category_field_name_quoted} AS
      category_val,
      {field_name_quoted}
    FROM {src_tbl_name_quoted}
    WHERE {category_field_name_quoted} IS NOT NULL
    AND {field_name_quoted} IS NOT NULL
    {and_tbl_filt_clause}
    ORDER BY {category_field_name_quoted}, {field_name_quoted}
    """
    ## get data
    cur.exe(sql)
    data = cur.fetchall()
    cols = ['category_val', 'field_val']
    df = pd.DataFrame(data, columns=cols)
    ## build result
    category_vals_specs = []
    orig_category_vals = df['category_val'].unique()
    sorted_category_vals = to_sorted_values(orig_vals=orig_category_vals,
        field_name=category_field_name, sort_orders=sort_orders, sort_order=category_sort_order)
    for category_val in sorted_category_vals:
        vals = df.loc[df['category_val'] == category_val, 'field_val'].tolist()
        category_vals_spec = BoxplotCategoryItemValsSpec(category_val=category_val, vals=vals)
        category_vals_specs.append(category_vals_spec)
    result = BoxplotCategoryValsSpecs(
        field_name=field_name,
        category_field_name=category_field_name,
        series_field_name='',
        chart_name=None,
        category_vals_specs=category_vals_specs,
        category_sort_order=category_sort_order,
        boxplot_type=boxplot_type,
    )
    return result

@dataclass(frozen=False)
class BoxplotSeriesCategoryValsSpecs:
    field: str
    category_field: str  ## e.g. Country
    series_field: str | None  ## e.g. Gender
    series_category_vals_specs: Sequence[BoxplotSeriesItemCategoryValsSpecs]
    category_sort_order: SortOrder
    boxplot_type: BoxplotType

    def to_indiv_chart_spec(self, *, dp: int = 3):
        n_records = 0
        data_series_specs = []
        for series_item_category_vals_specs in self.series_category_vals_specs:
            box_items = []
            for category_vals_spec in series_item_category_vals_specs.category_vals_specs:
                n_records += len(category_vals_spec.vals)
                box_result = BoxResult(category_vals_spec.vals, self.boxplot_type)
                box_item = BoxplotDataItem(
                    box_bottom=box_result.box_bottom,
                    box_bottom_rounded=round(box_result.box_bottom, dp),
                    bottom_whisker=box_result.bottom_whisker,
                    bottom_whisker_rounded=round(box_result.bottom_whisker, dp),
                    median=box_result.median,
                    median_rounded=round(box_result.median, dp),
                    outliers=box_result.outliers,
                    outliers_rounded=[round(outlier, dp) for outlier in box_result.outliers],
                    box_top=box_result.box_top,
                    box_top_rounded=round(box_result.box_top, dp),
                    top_whisker=box_result.top_whisker,
                    top_whisker_rounded=round(box_result.top_whisker, dp)
                )
                box_items.append(box_item)
            data_series_spec = BoxplotDataSeriesSpec(
                label=series_item_category_vals_specs.series_val,
                box_items=box_items,
            )
            data_series_specs.append(data_series_spec)
        indiv_chart_spec = BoxplotIndivChartSpec(
            data_series_specs=data_series_specs,
            n_records=n_records,
        )
        return indiv_chart_spec

def get_by_series_category_charting_spec(*, cur: ExtendedCursor, dbe_spec: DbeSpec, src_tbl_name: str,
        field_name: str,
        category_field_name: str,
        series_field_name: str,
        sort_orders: SortOrderSpecs,
        category_sort_order: SortOrder = SortOrder.VALUE,
        series_sort_order: SortOrder = SortOrder.VALUE,
        boxplot_type: BoxplotType = BoxplotType.INSIDE_1_POINT_5_TIMES_IQR,
        tbl_filt_clause: str | None = None) -> BoxplotSeriesCategoryValsSpecs:
    ## prepare items
    field_name_quoted = dbe_spec.entity_quoter(field_name)
    category_field_name_quoted = dbe_spec.entity_quoter(category_field_name)
    series_field_name_quoted = dbe_spec.entity_quoter(series_field_name)
    and_tbl_filt_clause = f"AND ({tbl_filt_clause})" if tbl_filt_clause else ''
    src_tbl_name_quoted = dbe_spec.entity_quoter(src_tbl_name)
    ## assemble SQL
    sql = f"""\
    SELECT
        {series_field_name_quoted} AS
      series_val,
        {category_field_name_quoted} AS
      category_val,
      {field_name_quoted}
    FROM {src_tbl_name_quoted}
    WHERE {series_field_name_quoted} IS NOT NULL
    AND {category_field_name_quoted} IS NOT NULL
    AND {field_name_quoted} IS NOT NULL
    {and_tbl_filt_clause}
    ORDER BY {series_field_name_quoted}, {category_field_name_quoted}, {field_name_quoted}
    """
    ## get data
    cur.exe(sql)
    data = cur.fetchall()
    cols = ['series_val', 'category_val', 'field_val']
    df = pd.DataFrame(data, columns=cols)
    ## build result
    series_category_vals_specs_dict = defaultdict(list)
    orig_series_vals = df['series_val'].unique()
    sorted_series_vals = to_sorted_values(orig_vals=orig_series_vals,
        field_name=series_field_name, sort_orders=sort_orders, sort_order=series_sort_order)
    for series_val in sorted_series_vals:
        orig_category_vals = df.loc[df['series_val'] == series_val, 'category_val'].unique()
        sorted_category_vals = to_sorted_values(orig_vals=orig_category_vals,
            field_name=category_field_name, sort_orders=sort_orders, sort_order=category_sort_order)
        for category_val in sorted_category_vals:
            vals = df.loc[
                (df['series_val'] == series_val) & (df['category_val'] == category_val), 'field_val'].tolist()
            ## Gather by series
            category_vals_spec = BoxplotCategoryItemValsSpec(category_val=category_val, vals=vals)
            series_category_vals_specs_dict[series_val].append(category_vals_spec)
    ## make item for each series
    series_category_vals_specs = []
    for series_val, category_vals_specs in series_category_vals_specs_dict.items():
        series_category_vals_spec = BoxplotSeriesItemCategoryValsSpecs(
            series_val=series_val,
            category_vals_specs=category_vals_specs,
        )
        series_category_vals_specs.append(series_category_vals_spec)
    result = BoxplotSeriesCategoryValsSpecs(
        field=field_name,
        category_field=category_field_name,
        series_field=series_field_name,
        series_category_vals_specs=series_category_vals_specs,
        category_sort_order=category_sort_order,
        boxplot_type=boxplot_type,
    )
    return result

@dataclass
class BoxplotChartingSpec:
    categories: Sequence[Any]
    indiv_chart_specs: Sequence[BoxplotIndivChartSpec]  ## even though only ever one follow the standard pattern so get_html works for all chart types the same way
    series_legend_label: str | None
    rotate_x_labels: bool
    show_n_records: bool
    x_axis_title: str
    y_axis_title: str

    def __post_init__(self):
        if len(self.indiv_chart_specs) != 1:
            raise Exception("Boxplot charts can only have one individual chart")
        self.has_minor_ticks = len(self.categories) > 10
        self.n_series = len(self.indiv_chart_specs[0].data_series_specs)
        self.is_single_series = (self.n_series == 1)
        self.n_x_items = len(self.categories)
        ## get max x axis val
        self.x_axis_max_val = len(self.categories) + 0.5
        ## get min and max y values
        all_min_ys = []
        all_max_ys = []
        for data_series_spec in self.indiv_chart_specs[0].data_series_specs:
            for box_item in data_series_spec.box_items:
                if not box_item:
                    continue
                items_with_low_ys = [box_item.bottom_whisker, ]
                items_with_high_ys = [box_item.top_whisker, ]
                if box_item.outliers:
                    items_with_low_ys += box_item.outliers
                    items_with_high_ys += box_item.outliers
                box_min_y_val = min(items_with_low_ys)
                box_max_y_val = max(items_with_high_ys)
                all_min_ys.append(box_min_y_val)
                all_max_ys.append(box_max_y_val)
        min_y_val = min(all_min_ys)
        max_y_val = max(all_max_ys)
        self.y_axis_min_val, self.y_axis_max_val = get_optimal_axis_bounds(min_y_val, max_y_val)
        ## misc
        max_x_axis_label_len = 0
        max_x_axis_label_lines = 0
        for category in self.categories:
            x_axis_label_len = len(category)
            if x_axis_label_len > max_x_axis_label_len:
                max_x_axis_label_len = x_axis_label_len
            x_label_lines = len(str(category).split('<br>'))
            if x_label_lines > max_x_axis_label_lines:
                max_x_axis_label_lines = x_label_lines
        self.max_x_axis_label_len = max_x_axis_label_len
        self.max_x_axis_label_lines = max_x_axis_label_lines  ## used to set axis label drop
        ## set box labels
        for indiv_chart_spec in self.indiv_chart_specs:
            for data_series_spec in indiv_chart_spec.data_series_specs:
                series_label = data_series_spec.label
                for box_item, category in zip(data_series_spec.box_items, self.categories, strict=True):
                    if box_item:
                        if series_label:
                            box_item.indiv_box_label = f"{series_label}, {category}"
                        else:
                            box_item.indiv_box_label = category
