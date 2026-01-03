"""
These functions are not responsible for sort order of category values (by value, by label etc).
Nor are they responsible for having placeholders for empty items
e.g. one country series lacks a certain web browser value
It is the dataclasses returned by these functions that are responsible for empty values.
Empty values are handled in their methods responsible for translating into charts specs
e.g. to_indiv_chart_spec().

Sort order always includes by value and custom.
Only single chart, single series charts also sort by increasing and decreasing.

The job of these functions is to get all the details you could possibly want about the data -
including labels, amounts etc. - into a dataclass.

These dataclasses should have everything included that directly relates to the data - field labels, value labels etc.
They shouldn't contain any settings which are purely about style or display
(although it is the best place to form HTML tool_tips).

For example:
IN: chart_label
OUT: rotate_x_labels, show_n_records, series_legend_label (as such - might actually be one of the data labels)
"""
from collections.abc import Sequence
from dataclasses import dataclass
from textwrap import dedent
from typing import Any

from sofastats.conf.main import ChartMetric, SortOrder, SortOrderSpecs
from sofastats.data_extraction.charts.misc_interfaces import DataItem, DataSeriesSpec, IndivChartSpec

## by category only (one chart, one series)

@dataclass(frozen=True)
class CategoryItemAmountSpec:
    """
    Frequency-related specification for an individual category value e.g. for Japan
    Frequency-related includes percentage. Both freq and pct are about the number of items.
    """
    category_val: float | str
    amount: float  ## e.g. frequency, mean, percent, or sum amount
    tool_tip: str  ## HTML tool tip e.g. "256<br>(23.50%)"
    sub_total: int  ## used to get total number of records (without having to run a separate, un-aggregated query


@dataclass(frozen=True)
class CategoryFreqSpecs:
    """
    Store frequency and percentage for each category value e.g. Japan in a category variable e.g. country

    Category-by variable label e.g. country, and one spec related to frequency per country value
    e.g. one for Italy, one for Germany etc.
    Frequency-related includes percentage. Both freq and pct are about the number of items.
    """
    category_field_name: str  ## e.g. Country
    category_freq_specs: Sequence[CategoryItemAmountSpec]  ## e.g. one amount spec per country
    sort_orders: SortOrderSpecs
    category_sort_order: SortOrder
    metric: ChartMetric = ChartMetric.FREQ

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
        n_records = sum(category_freq_spec.sub_total for category_freq_spec in self.category_freq_specs)
        ## collect data items according to correctly sorted x-axis category items
        ## a) make dict so we can get from val to data item
        vals2category_freq_spec = {}
        for category_freq_spec in self.category_freq_specs:
            val = category_freq_spec.category_val
            vals2category_freq_spec[val] = category_freq_spec
        ## b) create sorted collection of data items according to x-axis sorting.
        ## Note - never gaps for by-category only charts
        series_data_items = []
        for category in self.sorted_categories:
            category_freq_spec = vals2category_freq_spec.get(category)
            data_item = DataItem(
                amount=category_freq_spec.amount,
                tool_tip=category_freq_spec.tool_tip,
                sub_total=category_freq_spec.sub_total)
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

def to_sorted_categories(*, category_freq_specs: Sequence[CategoryItemAmountSpec],
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
    category_freq_specs: Sequence[CategoryItemAmountSpec]  ## one frequency-related spec per country

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
    def category_freq_specs(self) -> Sequence[CategoryItemAmountSpec]:
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
            vals2freq_spec = {}
            for freq_spec in series_category_freq_spec.category_freq_specs:
                ## count up n_records while we're here in loop
                n_records += freq_spec.sub_total
                ## collect data items according to correctly sorted x-axis category items
                ## a) make dict so we can get from val to data item
                val = freq_spec.category_val
                vals2freq_spec[val] = freq_spec
            ## b) create sorted collection of data items according to x-axis sorting.
            ## Note - gaps should become None (which .get() automatically handles for us :-))
            series_data_items = []
            for category in self.sorted_categories:
                freq_spec = vals2freq_spec.get(category)
                data_item = DataItem(
                    amount=freq_spec.amount,
                    tool_tip=freq_spec.tool_tip,
                    sub_total=freq_spec.sub_total)
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
    category_freq_specs: Sequence[CategoryItemAmountSpec]

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
    def category_freq_specs(self) -> Sequence[CategoryItemAmountSpec]:
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
            vals2freq_spec = {}
            for freq_spec in chart_category_freq_spec.category_freq_specs:
                ## count up n_records while we're here in loop
                n_records += freq_spec.sub_total
                ## collect data items according to correctly sorted x-axis category items
                ## a) make dict so we can get from val to data item
                val = freq_spec.category_val
                vals2freq_spec[val] = freq_spec
            ## b) create sorted collection of data items according to x-axis sorting.
            ## Note - gaps should become None (which .get() automatically handles for us :-))
            chart_data_items = []
            for category in self.sorted_categories:
                freq_spec = vals2freq_spec.get(category)
                chart_data_items.append(freq_spec)
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
    def category_freq_specs(self) -> Sequence[CategoryItemAmountSpec]:
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
                vals2freq_spec = {}
                for freq_spec in series_category_freq_spec.category_freq_specs:
                    ## count up n_records while we're here in loop
                    n_records += freq_spec.sub_total
                    ## collect data items according to correctly sorted x-axis category items
                    ## a) make dict so we can get from val to data item
                    val = freq_spec.category_val
                    vals2freq_spec[val] = freq_spec
                ## b) create sorted collection of data items according to x-axis sorting.
                ## Note - gaps should become None (which .get() automatically handles for us :-))
                chart_series_data_items = []
                for category in self.sorted_categories:
                    data_item = vals2freq_spec.get(category)
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
