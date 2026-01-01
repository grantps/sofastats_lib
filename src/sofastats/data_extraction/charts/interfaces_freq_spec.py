"""
These functions are not responsible for sort order of category values (by value, by label etc).
Nor are they responsible for having placeholders for empty items
e.g. one country series lacks a certain web browser value
It is the dataclasses returned by these functions that are responsible for empty values.
Empty values are handled in their methods responsible for translating into charts specs
e.g. to_indiv_chart_spec().

Sort order always includes by value and by label. Only single chart, single series charts
also sort by increasing and decreasing.

The job of these functions is to get all the details you could possibly want about the data -
including labels, amounts etc. - into a dataclass.

These dataclasses should have everything included that directly relates to the data - field labels, value labels etc.
They shouldn't contain any settings which are purely about style or display.

For example:
IN: chart_label
OUT: rotate_x_labels, show_n_records, series_legend_label (as such - might actually be one of the data labels)
"""
from collections.abc import Sequence
from dataclasses import dataclass
from textwrap import dedent
from typing import Any

import pandas as pd

from sofastats.conf.main import DbeSpec, SortOrder, SortOrderSpecs
from sofastats.data_extraction.db import ExtendedCursor
from sofastats.data_extraction.charts.interfaces import DataItem, DataSeriesSpec, IndivChartSpec
from sofastats.data_extraction.utils import to_sorted_values

## by category only (one chart, one series)

@dataclass(frozen=True)
class CategoryItemFreqSpec:
    """
    Frequency-related specification for an individual category value e.g. for Japan
    Frequency-related includes percentage. Both freq and pct are about the number of items.
    """
    category_val: float | str  ## e.g. 1, or Japan
    freq: int
    category_pct: float


@dataclass(frozen=True)
class CategoryFreqSpecs:
    """
    Store frequency and percentage for each category value e.g. Japan in a category variable e.g. country

    Category-by variable label e.g. country, and one spec related to frequency per country value
    e.g. one for Italy, one for Germany etc.
    Frequency-related includes percentage. Both freq and pct are about the number of items.
    """
    category_field_name: str  ## e.g. Country
    category_freq_specs: Sequence[CategoryItemFreqSpec]  ## e.g. one freq spec per country
    sort_orders: SortOrderSpecs
    category_sort_order: SortOrder

    def __str__(self):
        bits = [f"Category field value: {self.category_field_name}", ]
        for freq_spec in self.category_freq_specs:
            bits.append(f"    {freq_spec}")
        return dedent('\n'.join(bits))

    @property
    def sorted_categories(self):
        return to_sorted_categories(category_freq_specs=self.category_freq_specs,
            category_field_name=self.category_field_name,
            sort_orders=self.sort_orders, category_sort_order=self.category_sort_order, can_sort_by_freq=True)

    def to_indiv_chart_spec(self) -> IndivChartSpec:
        n_records = sum(category_freq_spec.freq for category_freq_spec in self.category_freq_specs)
        ## collect data items according to correctly sorted x-axis category items
        ## a) make dict so we can get from val to data item
        vals2data_items = {}
        for category_freq_spec in self.category_freq_specs:
            val = category_freq_spec.category_val
            data_item = DataItem(
                amount=category_freq_spec.freq,
                label=str(category_freq_spec.freq),
                tooltip=f"{category_freq_spec.freq}<br>({round(category_freq_spec.category_pct, 2)}%)")
            vals2data_items[val] = data_item
        ## b) create sorted collection of data items according to x-axis sorting.
        ## Note - never gaps for by-category only charts
        series_data_items = []
        for category in self.sorted_categories:
            data_item = vals2data_items.get(category)
            series_data_items.append(data_item)
        ## assemble
        data_series_spec = DataSeriesSpec(
            label=None,
            data_items=series_data_items,
        )
        indiv_chart_spec = IndivChartSpec(
            label=None,
            data_series_specs=[data_series_spec, ],
            n_records=n_records,
        )
        return indiv_chart_spec

def to_sorted_categories(*, category_freq_specs: Sequence[CategoryItemFreqSpec],
        category_field_name: str, sort_orders: SortOrderSpecs, category_sort_order: SortOrder,
        can_sort_by_freq=True) -> Sequence[Any]:
    """
    Get category specs in correct order ready for use.
    The category specs are constant across all charts and series (if multi-chart and / or multi-series)

    Only makes sense to order by INCREASING or DECREASING if single series and single chart.
    """
    if category_sort_order == SortOrder.VALUE:
        def sort_me(freq_spec):
            return freq_spec.category_val
        reverse = False
    elif category_sort_order == SortOrder.CUSTOM:
        ## use supplied sort order
        try:
            values_in_order = sort_orders[category_field_name]
        except KeyError:
            raise Exception(
                f"You wanted the values in variable '{category_field_name}' to have a custom sort order "
                "but I couldn't find a sort order from what you supplied. "
                "Please fix the sort order details or use another approach to sorting.")
        value2order = {val: order for order, val in enumerate(values_in_order)}
        def sort_me(freq_spec):
            try:
                idx_for_ordered_position = value2order[freq_spec.category_val]
            except KeyError:
                raise Exception(
                    f"The custom sort order you supplied for values in variable '{category_field_name}' "
                    f"didn't include value '{freq_spec.category_val}' so please fix that and try again.")
            return idx_for_ordered_position
        reverse = False
    elif category_sort_order == SortOrder.INCREASING:
        if can_sort_by_freq:
            def sort_me(freq_spec):
                return freq_spec.freq
            reverse = False
        else:
            raise Exception(
                f"Unexpected category_sort_order ({category_sort_order})"
                "\nINCREASING is for ordering by frequency which makes no sense when multi-series charts."
            )
    elif category_sort_order == SortOrder.DECREASING:
        if can_sort_by_freq:
            def sort_me(freq_spec):
                return freq_spec.freq
            reverse = True
        else:
            raise Exception(
                f"Unexpected category_sort_order ({category_sort_order})"
                "\nDECREASING is for ordering by frequency which makes no sense when multi-series charts."
            )
    else:
        raise Exception(f"Unexpected category_sort_order ({category_sort_order})")
    categories = [freq_spec.category_val for freq_spec in sorted(category_freq_specs, key=sort_me, reverse=reverse)]
    return categories


## by category and by series

@dataclass(frozen=True)
class SeriesCategoryFreqSpec:
    """
    Frequency-related specifications for each category value within this particular value of the series-by variable.
    Frequency-related includes percentage. Both freq and pct are about the number of items.
    """
    series_val: float | str  ## e.g. 1, or Male
    category_freq_specs: Sequence[CategoryItemFreqSpec]  ## one frequency-related spec per country

    def __str__(self):
        bits = [f"Series value: {self.series_val}", ]
        for freq_spec in self.category_freq_specs:
            bits.append(f"        {freq_spec}")
        return dedent('\n'.join(bits))


@dataclass(frozen=True)
class SeriesCategoryFreqSpecs:
    """
    Against each series store frequency and percentage for each category value
    e.g. Japan in a category variable e.g. country

    Series-by variable name e.g. Gender, and category-by variable name e.g. country,
    and one spec related to frequency per country value
    e.g. one for Italy, one for Germany etc.
    Frequency-related includes percentage. Both freq and pct are about the number of items.
    """
    series_field_name: str  ## e.g. Gender
    category_field_name: str  ## e.g. Country
    series_category_freq_specs: Sequence[SeriesCategoryFreqSpec]
    sort_orders: SortOrderSpecs
    category_sort_order: SortOrder

    def __str__(self):
        bits = [
            f"Series field name: {self.series_field_name}",
            f"Category field name: {self.category_field_name}",
        ]
        for series_category_freq_spec in self.series_category_freq_specs:
            bits.append(f"    {series_category_freq_spec}")
        return dedent('\n'.join(bits))

    @property
    def category_freq_specs(self) -> Sequence[CategoryItemFreqSpec]:
        """
        Relied upon by to_sorted_category_specs()
        """
        all_category_freq_specs = []
        vals = set()
        for series_category_freq_spec in self.series_category_freq_specs:
            for freq_spec in series_category_freq_spec.category_freq_specs:
                if freq_spec.category_val not in vals:
                    all_category_freq_specs.append(freq_spec)
                    vals.add(freq_spec.category_val)
        return list(all_category_freq_specs)

    @property
    def sorted_categories(self):
        return to_sorted_categories(category_freq_specs=self.category_freq_specs,
            category_field_name=self.category_field_name,
            sort_orders=self.sort_orders, category_sort_order=self.category_sort_order,
            can_sort_by_freq=False)

    def to_indiv_chart_spec(self) -> IndivChartSpec:
        n_records = 0
        data_series_specs = []
        for series_category_freq_spec in self.series_category_freq_specs:
            ## prepare for sorting category items within this series (may even have missing items)
            vals2data_items = {}
            for freq_spec in series_category_freq_spec.category_freq_specs:
                ## count up n_records while we're here in loop
                n_records += freq_spec.freq
                ## collect data items according to correctly sorted x-axis category items
                ## a) make dict so we can get from val to data item
                val = freq_spec.category_val
                tooltip = (f"{freq_spec.category_val}, {series_category_freq_spec.series_val}"
                   f"<br>{freq_spec.freq}"
                   f"<br>({round(freq_spec.category_pct, 2)}%)")
                data_item = DataItem(
                    amount=freq_spec.freq,
                    label=str(freq_spec.freq),
                    tooltip=tooltip)
                vals2data_items[val] = data_item
            ## b) create sorted collection of data items according to x-axis sorting.
            ## Note - gaps should become None (which .get() automatically handles for us :-))
            series_data_items = []
            for category in self.sorted_categories:
                data_item = vals2data_items.get(category)
                series_data_items.append(data_item)
            data_series_spec = DataSeriesSpec(
                label=series_category_freq_spec.series_val,
                data_items=series_data_items,
            )
            data_series_specs.append(data_series_spec)
        indiv_chart_spec = IndivChartSpec(
            label=None,
            data_series_specs=data_series_specs,
            n_records=n_records,
        )
        return indiv_chart_spec


## multi-chart, one series each chart by category

@dataclass(frozen=True)
class ChartCategoryFreqSpec:
    """
    Frequency-related specifications for each category value within this particular value of the chart-by variable.
    Frequency-related includes percentage. Both freq and pct are about the number of items.
    """
    chart_val: float | str
    category_freq_specs: Sequence[CategoryItemFreqSpec]

    def __str__(self):
        bits = [f"Chart value (label): {self.chart_val}", ]
        for freq_spec in self.category_freq_specs:
            bits.append(f"        {freq_spec}")
        return dedent('\n'.join(bits))

@dataclass(frozen=True)
class ChartCategoryFreqSpecs:
    """
    Against each chart store frequency and percentage for each category value
    e.g. Japan in a category variable e.g. country
    Also store labels for chart and category as a convenience so all the building blocks are in one place.
    """
    chart_field_name: str  ## e.g. Web Browser
    category_field_name: str  ## e.g. Country
    chart_category_freq_specs: Sequence[ChartCategoryFreqSpec]
    sort_orders: SortOrderSpecs
    category_sort_order: SortOrder

    def __str__(self):
        bits = [
            f"Chart field label: {self.chart_field_name}",
            f"Category field label: {self.category_field_name}",
        ]
        for chart_category_freq_spec in self.chart_category_freq_specs:
            bits.append(f"    {chart_category_freq_spec}")
        return dedent('\n'.join(bits))

    @property
    def category_freq_specs(self) -> Sequence[CategoryItemFreqSpec]:
        all_category_freq_specs = []
        vals = set()
        for chart_category_freq_spec in self.chart_category_freq_specs:
            for freq_spec in chart_category_freq_spec.category_freq_specs:
                if freq_spec.category_val not in vals:
                    all_category_freq_specs.append(freq_spec)
                    vals.add(freq_spec.category_val)
        return list(all_category_freq_specs)

    @property
    def sorted_categories(self):
        return to_sorted_categories(category_freq_specs=self.category_freq_specs,
            category_field_name=self.category_field_name,
            sort_orders=self.sort_orders, category_sort_order=self.category_sort_order,
            can_sort_by_freq=False)

    def to_indiv_chart_specs(self) -> Sequence[IndivChartSpec]:
        indiv_chart_specs = []
        for chart_category_freq_spec in self.chart_category_freq_specs:
            n_records = 0
            ## prepare for sorting category items within this chart (may even have missing items)
            vals2data_items = {}
            for freq_spec in chart_category_freq_spec.category_freq_specs:
                ## count up n_records while we're here in loop
                n_records += freq_spec.freq
                ## collect data items according to correctly sorted x-axis category items
                ## a) make dict so we can get from val to data item
                val = freq_spec.category_val
                tooltip = f"{freq_spec.freq}<br>({round(freq_spec.category_pct, 2)}%)"
                data_item = DataItem(
                    amount=freq_spec.freq,
                    label=str(freq_spec.freq),
                    tooltip=tooltip)
                vals2data_items[val] = data_item
            ## b) create sorted collection of data items according to x-axis sorting.
            ## Note - gaps should become None (which .get() automatically handles for us :-))
            chart_data_items = []
            for category in self.sorted_categories:
                data_item = vals2data_items.get(category)
                chart_data_items.append(data_item)
            data_series_spec = DataSeriesSpec(
                label=None,
                data_items=chart_data_items,
            )
            indiv_chart_spec = IndivChartSpec(
                label=f"{self.chart_field_name}: {chart_category_freq_spec.chart_val}",
                data_series_specs=[data_series_spec, ],
                n_records=n_records,
            )
            indiv_chart_specs.append(indiv_chart_spec)
        return indiv_chart_specs

## Chart, series, category

@dataclass(frozen=True)
class ChartSeriesCategoryFreqSpec:
    """
    Nested within each value of the chart-by variable, within each value of the series-by variable,
    collect frequency-related specifications for each category value.
    Frequency-related includes percentage. Both freq and pct are about the number of items.
    """
    chart_val: float | str
    series_category_freq_specs: Sequence[SeriesCategoryFreqSpec]

    def __str__(self):
        bits = [f"Chart value: {self.chart_val}", ]
        for series_category_freq_spec in self.series_category_freq_specs:
            bits.append(f"    {series_category_freq_spec}")
        return dedent('\n'.join(bits))

@dataclass(frozen=True)
class ChartSeriesCategoryFreqSpecs:
    """
    Against each chart and series store frequency and percentage for each category value
    e.g. Japan in a category variable e.g. country
    Also store labels for chart, series, and category as a convenience so all the building blocks are in one place.
    """
    category_field_name: str  ## e.g. Country
    series_field_name: str  ## e.g. Gender
    chart_field_name: str  ## e.g. Web Browser
    chart_series_category_freq_specs: Sequence[ChartSeriesCategoryFreqSpec]
    sort_orders: SortOrderSpecs
    category_sort_order: SortOrder

    def __str__(self):
        bits = [
            f"Chart field name: {self.chart_field_name}",
            f"Series field name: {self.series_field_name}",
            f"Category field name: {self.category_field_name}",
        ]
        for chart_series_category_freq_spec in self.chart_series_category_freq_specs:
            bits.append(f"{chart_series_category_freq_spec}")
        return dedent('\n'.join(bits))

    @property
    def category_freq_specs(self) -> Sequence[CategoryItemFreqSpec]:
        all_category_freq_specs = []
        vals = set()
        for chart_series_category_freq_spec in self.chart_series_category_freq_specs:
            for series_category_freq_specs in chart_series_category_freq_spec.series_category_freq_specs:
                for freq_spec in series_category_freq_specs.category_freq_specs:
                    if freq_spec.category_val not in vals:
                        all_category_freq_specs.append(freq_spec)
                        vals.add(freq_spec.category_val)
        return list(all_category_freq_specs)

    @property
    def sorted_categories(self):
        return to_sorted_categories(category_freq_specs=self.category_freq_specs,
            category_field_name=self.category_field_name,
            sort_orders=self.sort_orders, category_sort_order=self.category_sort_order,
            can_sort_by_freq=False)

    def to_indiv_chart_specs(self) -> Sequence[IndivChartSpec]:
        indiv_chart_specs = []
        for chart_series_category_freq_spec in self.chart_series_category_freq_specs:
            n_records = 0
            data_series_specs = []
            for series_category_freq_spec in chart_series_category_freq_spec.series_category_freq_specs:
                ## prepare for sorting category items within this chart (may even have missing items)
                vals2data_items = {}
                for freq_spec in series_category_freq_spec.category_freq_specs:
                    ## count up n_records while we're here in loop
                    n_records += freq_spec.freq
                    ## collect data items according to correctly sorted x-axis category items
                    ## a) make dict so we can get from val to data item
                    val = freq_spec.category_val
                    tooltip = (
                        f"{freq_spec.category_val}, {series_category_freq_spec.series_val}"
                        f"<br>{freq_spec.freq}"
                        f"<br>({round(freq_spec.category_pct, 2)}%)")
                    data_item = DataItem(
                        amount=freq_spec.freq,
                        label=str(freq_spec.freq),
                        tooltip=tooltip)
                    vals2data_items[val] = data_item
                ## b) create sorted collection of data items according to x-axis sorting.
                ## Note - gaps should become None (which .get() automatically handles for us :-))
                chart_series_data_items = []
                for category in self.sorted_categories:
                    data_item = vals2data_items.get(category)
                    chart_series_data_items.append(data_item)
                data_series_spec = DataSeriesSpec(
                    label=series_category_freq_spec.series_val,
                    data_items=chart_series_data_items,
                )
                data_series_specs.append(data_series_spec)
            indiv_chart_spec = IndivChartSpec(
                label=f"{self.chart_field_name}: {chart_series_category_freq_spec.chart_val}",
                data_series_specs=data_series_specs,
                n_records=n_records,
            )
            indiv_chart_specs.append(indiv_chart_spec)
        return indiv_chart_specs

def get_by_category_charting_spec(*, cur: ExtendedCursor, dbe_spec: DbeSpec, src_tbl_name: str,
        category_field_name: str, sort_orders: SortOrderSpecs, category_sort_order: SortOrder = SortOrder.VALUE,
        tbl_filt_clause: str | None = None) -> CategoryFreqSpecs:
    """
    Intermediate charting spec - close to the data
    """
    ## prepare items
    and_tbl_filt_clause = f"AND ({tbl_filt_clause})" if tbl_filt_clause else ''
    category_field_name_quoted = dbe_spec.entity_quoter(category_field_name)
    src_tbl_name_quoted = dbe_spec.entity_quoter(src_tbl_name)
    ## assemble SQL
    sql = f"""\
    SELECT
        {category_field_name_quoted} AS
      category_val,
        COUNT(*) AS
      freq,
        (100.0 * COUNT(*)) / (SELECT COUNT(*) FROM {src_tbl_name_quoted}) AS
      raw_category_pct
    FROM {src_tbl_name_quoted}
    WHERE {category_field_name_quoted} IS NOT NULL
    {and_tbl_filt_clause}
    GROUP BY {category_field_name_quoted}
    ORDER BY {category_field_name_quoted}
    """
    ## get data
    cur.exe(sql)
    data = cur.fetchall()
    ## build result
    category_freq_specs = []
    for category_val, freq, category_pct in data:
        freq_spec = CategoryItemFreqSpec(
            category_val=category_val,
            freq=int(freq), category_pct=category_pct)
        category_freq_specs.append(freq_spec)
    data_spec = CategoryFreqSpecs(
        category_field_name=category_field_name,
        category_freq_specs=category_freq_specs,
        sort_orders=sort_orders,
        category_sort_order=category_sort_order,
    )
    return data_spec

def get_by_series_category_charting_spec(cur: ExtendedCursor, src_tbl_name: str, dbe_spec: DbeSpec,
        category_field_name: str, series_field_name: str,
        sort_orders: SortOrderSpecs,
        series_sort_order: SortOrder = SortOrder.VALUE, category_sort_order: SortOrder = SortOrder.VALUE,
        tbl_filt_clause: str | None = None) -> SeriesCategoryFreqSpecs:
    """
    Intermediate charting spec - close to the data

    For clustered bar charts and multi-line line charts
    """
    ## prepare items
    and_tbl_filt_clause = f"AND ({tbl_filt_clause})" if tbl_filt_clause else ''
    series_field_name_quoted = dbe_spec.entity_quoter(series_field_name)
    category_field_name_quoted = dbe_spec.entity_quoter(category_field_name)
    src_tbl_name_quoted = dbe_spec.entity_quoter(src_tbl_name)
    ## assemble SQL
    sql = f"""\
    SELECT
        {series_field_name_quoted} AS
      series_val,
        {category_field_name_quoted} AS
      category_val,
        COUNT(*) AS
      freq,
        ((100.0 * COUNT(*))
        / (
          SELECT COUNT(*)
          FROM {src_tbl_name_quoted}
          WHERE {series_field_name_quoted} = src.{series_field_name_quoted}
        )) AS
      raw_category_pct
    FROM {src_tbl_name} AS src
    WHERE {series_field_name_quoted} IS NOT NULL
    AND {category_field_name_quoted} IS NOT NULL
    {and_tbl_filt_clause}
    GROUP BY {series_field_name_quoted}, {category_field_name_quoted}
    ORDER BY {series_field_name_quoted}, {category_field_name_quoted}
    """
    ## get data
    cur.exe(sql)
    data = cur.fetchall()
    cols = ['series_val', 'category_val', 'freq', 'raw_category_pct']
    df = pd.DataFrame(data, columns=cols)
    series_category_freq_specs = []
    orig_series_vals = df['series_val'].unique()
    sorted_series_vals = to_sorted_values(orig_vals=orig_series_vals,
        field_name=series_field_name, sort_orders=sort_orders, sort_order=series_sort_order)
    for series_val in sorted_series_vals:
        category_item_freq_specs = []
        for _i, (category_val, freq, raw_category_pct) in df.loc[
            df['series_val'] == series_val,
            ['category_val', 'freq', 'raw_category_pct']
        ].iterrows():
            freq_spec = CategoryItemFreqSpec(
                category_val=category_val,
                freq=int(freq),
                category_pct=raw_category_pct,
            )
            category_item_freq_specs.append(freq_spec)
        series_category_freq_spec = SeriesCategoryFreqSpec(
            series_val=series_val,
            category_freq_specs=category_item_freq_specs,
        )
        series_category_freq_specs.append(series_category_freq_spec)
    data_spec = SeriesCategoryFreqSpecs(
        series_field_name=series_field_name,
        category_field_name=category_field_name,
        series_category_freq_specs=series_category_freq_specs,
        sort_orders=sort_orders,
        category_sort_order=category_sort_order,
    )
    return data_spec

def get_by_chart_category_charting_spec(*, cur: ExtendedCursor, dbe_spec: DbeSpec, src_tbl_name: str,
        category_field_name: str, chart_field_name: str,
        sort_orders: SortOrderSpecs,
        category_sort_order: SortOrder = SortOrder.VALUE, chart_sort_order: SortOrder = SortOrder.VALUE,
        tbl_filt_clause: str | None = None) -> ChartCategoryFreqSpecs:
    """
    Intermediate charting spec - close to the data
    """
    ## prepare items
    and_tbl_filt_clause = f"AND ({tbl_filt_clause})" if tbl_filt_clause else ''
    chart_field_name_quoted = dbe_spec.entity_quoter(chart_field_name)
    category_field_name_quoted = dbe_spec.entity_quoter(category_field_name)
    src_tbl_name_quoted = dbe_spec.entity_quoter(src_tbl_name)
    ## assemble SQL
    sql = f"""\
    SELECT
        {chart_field_name_quoted} AS
      chart_val,
        {category_field_name_quoted} AS
      category_val,
        COUNT(*) AS
      freq,
        ((100.0 * COUNT(*))
        / (
          SELECT COUNT(*)
          FROM {src_tbl_name_quoted}
          WHERE {chart_field_name_quoted} = src.{chart_field_name_quoted}
        )) AS
      raw_category_pct
    FROM {src_tbl_name_quoted} AS src
    WHERE {chart_field_name_quoted} IS NOT NULL
    AND {category_field_name_quoted} IS NOT NULL
    {and_tbl_filt_clause}
    GROUP BY {chart_field_name_quoted}, {category_field_name_quoted}
    ORDER BY {chart_field_name_quoted}, {category_field_name_quoted}
    """
    ## get data
    cur.exe(sql)
    data = cur.fetchall()
    cols = ['chart_val', 'category_val', 'freq', 'raw_category_pct']
    df = pd.DataFrame(data, columns=cols)
    chart_category_freq_specs = []
    orig_chart_vals = df['chart_val'].unique()
    sorted_chart_vals = to_sorted_values(orig_vals=orig_chart_vals,
        field_name=chart_field_name, sort_orders=sort_orders, sort_order=chart_sort_order)
    for chart_val in sorted_chart_vals:
        freq_specs = []
        for _i, (category_val, freq, raw_category_pct) in df.loc[
                    df['chart_val'] == chart_val,
                    ['category_val', 'freq', 'raw_category_pct']
                ].iterrows():
            freq_spec = CategoryItemFreqSpec(
                category_val=category_val,
                freq=int(freq),
                category_pct=raw_category_pct,
            )
            freq_specs.append(freq_spec)
        chart_category_freq_spec = ChartCategoryFreqSpec(
            chart_val=chart_val,
            category_freq_specs=freq_specs,
        )
        chart_category_freq_specs.append(chart_category_freq_spec)
    charting_spec = ChartCategoryFreqSpecs(
        chart_field_name=chart_field_name,
        category_field_name=category_field_name,
        chart_category_freq_specs=chart_category_freq_specs,
        sort_orders=sort_orders,
        category_sort_order=category_sort_order,
    )
    return charting_spec

def get_by_chart_series_category_charting_spec(*, cur: ExtendedCursor, dbe_spec: DbeSpec, src_tbl_name: str,
        category_field_name: str, series_field_name: str, chart_field_name: str,
        sort_orders: SortOrderSpecs,
        category_sort_order: SortOrder = SortOrder.VALUE,
        series_sort_order: SortOrder = SortOrder.VALUE,
        chart_sort_order: SortOrder = SortOrder.VALUE,
        tbl_filt_clause: str | None = None) -> ChartSeriesCategoryFreqSpecs:
    """
    Intermediate charting spec - close to the data
    """
    ## prepare items
    category_field_name_quoted = dbe_spec.entity_quoter(category_field_name)
    series_field_name_quoted = dbe_spec.entity_quoter(series_field_name)
    chart_field_name_quoted = dbe_spec.entity_quoter(chart_field_name)
    src_tbl_name_quoted = dbe_spec.entity_quoter(src_tbl_name)
    and_tbl_filt_clause = f"AND ({tbl_filt_clause})" if tbl_filt_clause else ''
    ## assemble SQL
    sql = f"""\
    SELECT
        {chart_field_name_quoted} AS
      chart_val,
        {series_field_name_quoted} AS
      series_val,
        {category_field_name_quoted} AS
      category_val,
        COUNT(*) AS
      freq,
        ((100.0 * COUNT(*))
        / (
          SELECT COUNT(*)
          FROM {src_tbl_name_quoted}
          WHERE {chart_field_name_quoted} = src.{chart_field_name_quoted}
          AND {series_field_name_quoted} = src.{series_field_name_quoted}
        )) AS
      raw_category_pct
    FROM {src_tbl_name_quoted} AS src
    WHERE {chart_field_name_quoted} IS NOT NULL
    AND {series_field_name_quoted} IS NOT NULL
    AND {category_field_name_quoted} IS NOT NULL
    {and_tbl_filt_clause}
    GROUP BY {chart_field_name_quoted}, {series_field_name_quoted}, {category_field_name_quoted}
    ORDER BY {chart_field_name_quoted}, {series_field_name_quoted}, {category_field_name_quoted}
    """
    ## get data
    cur.exe(sql)
    data = cur.fetchall()
    cols = ['chart_val', 'series_val', 'category_val', 'freq', 'raw_category_pct']
    df = pd.DataFrame(data, columns=cols)
    chart_series_category_freq_specs = []
    orig_chart_vals = df['chart_val'].unique()
    sorted_chart_vals = to_sorted_values(orig_vals=orig_chart_vals,
        field_name=chart_field_name, sort_orders=sort_orders, sort_order=chart_sort_order)
    for chart_val in sorted_chart_vals:
        series_category_freq_specs = []
        orig_series_vals = df.loc[df['chart_val'] == chart_val, 'series_val'].unique()
        sorted_series_vals = to_sorted_values(orig_vals=orig_series_vals,
            field_name=series_field_name, sort_orders=sort_orders, sort_order=series_sort_order)
        for series_val in sorted_series_vals:
            freq_specs = []
            for _i, (category_val, freq, raw_category_pct) in df.loc[
                (df['chart_val'] == chart_val) & (df['series_val'] == series_val),
                ['category_val', 'freq', 'raw_category_pct']
            ].iterrows():
                freq_spec = CategoryItemFreqSpec(
                    category_val=category_val,
                    freq=int(freq),
                    category_pct=raw_category_pct,
                )
                freq_specs.append(freq_spec)
            series_category_freq_spec = SeriesCategoryFreqSpec(
                series_val=series_val,
                category_freq_specs=freq_specs,
            )
            series_category_freq_specs.append(series_category_freq_spec)
        chart_series_category_freq_spec = ChartSeriesCategoryFreqSpec(
            chart_val=chart_val,
            series_category_freq_specs=series_category_freq_specs,
        )
        chart_series_category_freq_specs.append(chart_series_category_freq_spec)
    data_spec = ChartSeriesCategoryFreqSpecs(
        chart_field_name=chart_field_name,
        series_field_name=series_field_name,
        category_field_name=category_field_name,
        chart_series_category_freq_specs=chart_series_category_freq_specs,
        sort_orders=sort_orders,
        category_sort_order=category_sort_order,
    )
    return data_spec
