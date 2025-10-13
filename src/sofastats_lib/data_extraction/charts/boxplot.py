from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass
from itertools import groupby  ## actually quite performant

from sofastats_lib.conf.main import DbeSpec, SortOrder
from sofastats_lib.data_extraction.db import ExtendedCursor
from sofastats_lib.data_extraction.charts.interfaces import CategorySpec
from sofastats_lib.stats_calc.interfaces import BoxResult, BoxplotType
from sofastats_lib.stats_calc.utils import get_optimal_axis_bounds

@dataclass(frozen=False)
class BoxplotCategoryItemValsSpec:
    category_val: float | str  ## e.g. 1
    category_val_lbl: str  ## e.g. Japan
    vals: Sequence[float]

@dataclass(frozen=False)
class BoxplotSeriesItemCategoryValsSpecs:
    series_val: float | str  ## e.g. 1
    series_val_lbl: str  ## e.g. Male
    category_vals_specs: Sequence[BoxplotCategoryItemValsSpec]

def get_sorted_category_specs(
        category_vals_specs: Sequence[BoxplotCategoryItemValsSpec], category_sort_order: SortOrder):
    """
    category_specs = [
        CategorySpec(val=1, lbl='New Zealand'),
        CategorySpec(val=2, lbl='United States'),
        CategorySpec(val=3, lbl='Canada'),
    ]
    """
    category_specs = []
    for category_vals_spec in category_vals_specs:
        category_spec = CategorySpec(
            val=category_vals_spec.category_val,
            lbl=category_vals_spec.category_val_lbl,
        )
        category_specs.append(category_spec)
    if category_sort_order == SortOrder.VALUE:
        sorted_category_specs = sorted(category_specs, key=lambda x: x.val)
    elif category_sort_order == SortOrder.LABEL:
        sorted_category_specs = sorted(category_specs, key=lambda x: x.lbl)
    else:
        raise ValueError("Boxplot categories can only be sorted by value or label")
    return sorted_category_specs

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
    indiv_box_lbl: str | None = None  ## derived later from series lbl and category spec lbls in BoxplotChartingSpec
    center: float | None = None  ## derived later from offset depending on which item on series (move rightwards) in BoxplotIndivChartSpec

@dataclass
class BoxplotDataSeriesSpec:
    lbl: str | None
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
    chart_lbl: str | None
    series_fld_lbl: str | None
    category_fld_lbl: str  ## e.g. Country
    fld_lbl: str
    category_vals_specs: Sequence[BoxplotCategoryItemValsSpec]
    category_sort_order: SortOrder
    boxplot_type: BoxplotType

    def to_sorted_category_specs(self):
        return get_sorted_category_specs(self.category_vals_specs, self.category_sort_order)

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
            lbl=None,
            box_items=box_items,
        )
        indiv_chart_spec = BoxplotIndivChartSpec(
            data_series_specs=[data_series_spec, ],
            n_records=n_records,
        )
        return indiv_chart_spec

def get_by_category_charting_spec(*, cur: ExtendedCursor, dbe_spec: DbeSpec, src_tbl_name: str,
        category_fld_name: str, category_fld_lbl: str,
        fld_name: str, fld_lbl: str,
        tbl_filt_clause: str | None = None,
        category_vals2lbls: dict | None = None,
        category_sort_order: SortOrder = SortOrder.VALUE,
        boxplot_type: BoxplotType = BoxplotType.INSIDE_1_POINT_5_TIMES_IQR) -> BoxplotCategoryValsSpecs:
    category_vals2lbls = {} if category_vals2lbls is None else category_vals2lbls
    ## prepare items
    and_tbl_filt_clause = f"AND ({tbl_filt_clause})" if tbl_filt_clause else ''
    category_fld_name_quoted = dbe_spec.entity_quoter(category_fld_name)
    src_tbl_name_quoted = dbe_spec.entity_quoter(src_tbl_name)
    fld_name_quoted = dbe_spec.entity_quoter(fld_name)
    ## assemble SQL
    sql = f"""\
    SELECT
        {category_fld_name_quoted} AS
      category_val,
      {fld_name_quoted}
    FROM {src_tbl_name_quoted}
    WHERE {category_fld_name_quoted} IS NOT NULL
    AND {fld_name_quoted} IS NOT NULL
    {and_tbl_filt_clause}
    ORDER BY {category_fld_name_quoted}, {fld_name_quoted}
    """
    ## get data
    cur.exe(sql)
    sorted_data = cur.fetchall()
    ## build result
    category_vals_specs = []
    for category_val, raw_vals in groupby(sorted_data, lambda t: t[0]):
        vals = [measure_val for _cat_val, measure_val in raw_vals]
        category_vals_spec = BoxplotCategoryItemValsSpec(
            category_val=category_val, category_val_lbl=category_vals2lbls.get(category_val, str(category_val)),
            vals=vals,
        )
        category_vals_specs.append(category_vals_spec)
    result = BoxplotCategoryValsSpecs(
        chart_lbl=None,
        series_fld_lbl='',
        category_fld_lbl=category_fld_lbl,
        fld_lbl=fld_lbl,
        category_vals_specs=category_vals_specs,
        category_sort_order=category_sort_order,
        boxplot_type=boxplot_type,
    )
    return result

@dataclass(frozen=False)
class BoxplotSeriesCategoryValsSpecs:
    series_fld_lbl: str | None  ## e.g. Gender
    category_fld_lbl: str  ## e.g. Country
    fld_lbl: str
    series_category_vals_specs: Sequence[BoxplotSeriesItemCategoryValsSpecs]
    category_sort_order: SortOrder
    boxplot_type: BoxplotType

    def to_sorted_category_specs(self):
        first_series_category_vals_specs = self.series_category_vals_specs[0].category_vals_specs  ## same for all of them so look at first chart
        return get_sorted_category_specs(first_series_category_vals_specs, self.category_sort_order)

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
                lbl=series_item_category_vals_specs.series_val_lbl,
                box_items=box_items,
            )
            data_series_specs.append(data_series_spec)
        indiv_chart_spec = BoxplotIndivChartSpec(
            data_series_specs=data_series_specs,
            n_records=n_records,
        )
        return indiv_chart_spec

def get_by_series_category_charting_spec(*, cur: ExtendedCursor, dbe_spec: DbeSpec, src_tbl_name: str,
        series_fld_name: str, series_fld_lbl: str,
        category_fld_name: str, category_fld_lbl: str,
        fld_name: str, fld_lbl: str,
        tbl_filt_clause: str | None = None,
        series_vals2lbls: dict | None = None,
        category_vals2lbls: dict | None = None,
        category_sort_order: SortOrder = SortOrder.VALUE,
        boxplot_type: BoxplotType = BoxplotType.INSIDE_1_POINT_5_TIMES_IQR) -> BoxplotSeriesCategoryValsSpecs:
    category_vals2lbls = {} if category_vals2lbls is None else category_vals2lbls
    ## prepare items
    and_tbl_filt_clause = f"AND ({tbl_filt_clause})" if tbl_filt_clause else ''
    category_vals2lbls = {} if category_vals2lbls is None else category_vals2lbls
    fld_name_quoted = dbe_spec.entity_quoter(fld_name)
    series_fld_name_quoted = dbe_spec.entity_quoter(series_fld_name)
    category_fld_name_quoted = dbe_spec.entity_quoter(category_fld_name)
    src_tbl_name_quoted = dbe_spec.entity_quoter(src_tbl_name)
    ## assemble SQL
    sql = f"""\
    SELECT
        {series_fld_name_quoted} AS
      series_val,
        {category_fld_name_quoted} AS
      category_val,
      {fld_name_quoted}
    FROM {src_tbl_name_quoted}
    WHERE {series_fld_name_quoted} IS NOT NULL
    AND {category_fld_name_quoted} IS NOT NULL
    AND {fld_name_quoted} IS NOT NULL
    {and_tbl_filt_clause}
    ORDER BY {series_fld_name_quoted}, {category_fld_name_quoted}, {fld_name_quoted}
    """
    ## get data
    cur.exe(sql)
    sorted_data = cur.fetchall()
    ## build result
    series_category_vals_specs_dict = defaultdict(list)
    for (series_val, category_val), raw_vals in groupby(sorted_data, lambda t: t[:2]):
        ## Gather by series
        vals = [measure_val for _chart_val, _cat_val, measure_val in raw_vals]
        category_vals_spec = BoxplotCategoryItemValsSpec(
            category_val=category_val, category_val_lbl=category_vals2lbls.get(category_val, str(category_val)),
            vals=vals,
        )
        series_category_vals_specs_dict[series_val].append(category_vals_spec)
    ## make item for each series
    series_category_vals_specs = []
    for series_val, category_vals_specs in series_category_vals_specs_dict.items():
        series_category_vals_spec = BoxplotSeriesItemCategoryValsSpecs(
            series_val=series_val,
            series_val_lbl=series_vals2lbls.get(series_val, series_val),
            category_vals_specs=category_vals_specs,
        )
        series_category_vals_specs.append(series_category_vals_spec)
    result = BoxplotSeriesCategoryValsSpecs(
        series_fld_lbl=series_fld_lbl,
        category_fld_lbl=category_fld_lbl,
        fld_lbl=fld_lbl,
        series_category_vals_specs=series_category_vals_specs,
        category_sort_order=category_sort_order,
        boxplot_type=boxplot_type,
    )
    return result

@dataclass
class BoxplotChartingSpec:
    category_specs: Sequence[CategorySpec]
    indiv_chart_specs: Sequence[BoxplotIndivChartSpec]  ## even though only ever one follow the standard pattern so get_html works for all chart types the same way
    legend_lbl: str | None
    rotate_x_lbls: bool
    show_n_records: bool
    x_axis_title: str
    y_axis_title: str

    def __post_init__(self):
        if len(self.indiv_chart_specs) != 1:
            raise Exception("Boxplot charts can only have one individual chart")
        self.has_minor_ticks = len(self.category_specs) > 10
        self.n_series = len(self.indiv_chart_specs[0].data_series_specs)
        self.is_single_series = (self.n_series == 1)
        self.n_x_items = len(self.category_specs)
        ## get max x axis val
        self.x_axis_max_val = len(self.category_specs) + 0.5
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
        max_x_axis_lbl_len = 0
        max_x_axis_lbl_lines = 0
        for category_spec in self.category_specs:
            x_axis_lbl_len = len(category_spec.lbl)
            if x_axis_lbl_len > max_x_axis_lbl_len:
                max_x_axis_lbl_len = x_axis_lbl_len
            x_lbl_lines = len(category_spec.lbl.split('<br>'))
            if x_lbl_lines > max_x_axis_lbl_lines:
                max_x_axis_lbl_lines = x_lbl_lines
        self.max_x_axis_lbl_len = max_x_axis_lbl_len
        self.max_x_axis_lbl_lines = max_x_axis_lbl_lines  ## used to set axis lbl drop
        ## set box labels
        for indiv_chart_spec in self.indiv_chart_specs:
            for data_series_spec in indiv_chart_spec.data_series_specs:
                series_lbl = data_series_spec.lbl
                for box_item, category_spec in zip(data_series_spec.box_items, self.category_specs, strict=True):
                    if box_item:
                        if series_lbl:
                            box_item.indiv_box_lbl = f"{series_lbl}, {category_spec.lbl}"
                        else:
                            box_item.indiv_box_lbl = category_spec.lbl
