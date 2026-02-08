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

from sofastats.conf.main import ChartMetric, SortOrder, SortOrderSpecs
from sofastats.data_extraction.charts.interfaces.common import DataItem, DataSeriesSpec, IndivChartSpec
from sofastats.utils.item_sorting import sort_values_by_value_or_custom_if_possible

## Amount Specs ********************************************************************************************************

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
class SeriesCategoryAmountSpec:
    """
    Frequency-related specifications for each category value within this particular value of the series-by variable.
    Frequency-related includes percentage. Both freq and pct are about the number of items.
    """
    series_val: float | str  ## e.g. 1, or Male
    category_amount_specs: Sequence[CategoryItemAmountSpec]  ## one frequency-related spec per country

    def __str__(self):
        bits = [f"Series value: {self.series_val}", ]
        for amount_spec in self.category_amount_specs:
            bits.append(f"        {amount_spec}")
        return dedent('\n'.join(bits))

@dataclass(frozen=True)
class ChartCategoryAmountSpec:
    """
    Frequency-related specifications for each category value within this particular value of the chart-by variable.
    Frequency-related includes percentage. Both freq and pct are about the number of items.
    """
    chart_val: float | str
    category_amount_specs: Sequence[CategoryItemAmountSpec]

    def __str__(self):
        bits = [f"Chart value (label): {self.chart_val}", ]
        for amount_spec in self.category_amount_specs:
            bits.append(f"        {amount_spec}")
        return dedent('\n'.join(bits))

@dataclass(frozen=True)
class ChartSeriesCategoryAmountSpec:
    """
    Nested within each value of the chart-by variable, within each value of the series-by variable,
    collect frequency-related specifications for each category value.
    Frequency-related includes percentage. Both freq and pct are about the number of items.
    """
    chart_val: float | str
    series_category_amount_specs: Sequence[SeriesCategoryAmountSpec]

    def __str__(self):
        bits = [f"Chart value: {self.chart_val}", ]
        for series_category_amount_spec in self.series_category_amount_specs:
            bits.append(f"    {series_category_amount_spec}")
        return dedent('\n'.join(bits))

## Sorting functions ***************************************************************************************************

def _to_sorted_amount_specs(
        amount_specs: Sequence[CategoryItemAmountSpec | ChartCategoryAmountSpec | SeriesCategoryAmountSpec | ChartSeriesCategoryAmountSpec],
        amount_spec_val_attribute_name: str, field_name: str, sort_orders: SortOrderSpecs, field_sort_order: SortOrder,
        can_sort_by_freq=True) -> list:
    """
    Args:
        amount_specs: the amount spec needing to be sorted
        amount_spec_val_attribute_name: e.g. category_val, chart_val etc.
        field_name: e.g. category_field_name, series_field_name etc.
        sort_orders: if supplied, a dictionary that provides the sort orders for any variables given a custom sort order
        field_sort_order: e.g. SortOrder.CUSTOM
        can_sort_by_freq: whether INCREASING or DECREASING are valid options for sorting
    Returns:
        Same amount specs as were given to it, but sorted
    """
    if field_sort_order == SortOrder.VALUE:
        def sort_me(amount_spec):
            return getattr(amount_spec, amount_spec_val_attribute_name)
        reverse = False
    elif field_sort_order == SortOrder.CUSTOM:
        ## use supplied sort order
        try:
            values_in_order = sort_orders[field_name]
        except KeyError:
            raise Exception(
                f"You wanted the values in variable '{field_name}' to have a custom sort order "
                "but I couldn't find a sort order from what you supplied. "
                "Please fix the sort order details or use another approach to sorting.")
        value2order = {val: order for order, val in enumerate(values_in_order)}
        def sort_me(amount_spec):
            amount_spec_val = getattr(amount_spec, amount_spec_val_attribute_name)
            try:
                idx_for_ordered_position = value2order[amount_spec_val]
            except KeyError:
                raise Exception(
                    f"The custom sort order you supplied for values in variable '{field_name}' "
                    f"didn't include value '{amount_spec_val}' so please fix that and try again.")
            return idx_for_ordered_position
        reverse = False
    elif field_sort_order == SortOrder.INCREASING:
        if can_sort_by_freq:
            def sort_me(amount_spec):
                return amount_spec.freq
            reverse = False
        else:
            raise Exception(
                f"Unexpected field_sort_order ({field_sort_order})"
                "\nINCREASING is for ordering by frequency which makes no sense when multi-series charts."
            )
    elif field_sort_order == SortOrder.DECREASING:
        if can_sort_by_freq:
            def sort_me(amount_spec):
                return amount_spec.freq
            reverse = True
        else:
            raise Exception(
                f"Unexpected field_sort_order ({field_sort_order})"
                "\nDECREASING is for ordering by frequency which makes no sense when multi-series charts."
            )
    else:
        raise Exception(f"Unexpected field_sort_order ({field_sort_order})")
    sorted_amount_specs = sorted(amount_specs, key=sort_me, reverse=reverse)
    return sorted_amount_specs

def to_sorted_category_amount_specs(*, category_amount_specs: Sequence[CategoryItemAmountSpec],
        category_field_name: str, sort_orders: SortOrderSpecs, category_sort_order: SortOrder,
        can_sort_by_freq=True) -> list[CategoryItemAmountSpec]:
    """
    Get category amount specs in correct order ready for use.
    The category amount specs are constant across all charts and series (if multi-chart and / or multi-series)

    Only makes sense to order by INCREASING or DECREASING if single series and single chart.

    Args:
        can_sort_by_freq: do not sort categories by frequency when inside a series or chart (or both)
          because this can lead to different sort orders per series or chart.
          So it should only be True for charts by category alone.
    """
    return _to_sorted_amount_specs(amount_specs=category_amount_specs, amount_spec_val_attribute_name='category_val',
        field_name=category_field_name, sort_orders=sort_orders, field_sort_order=category_sort_order,
        can_sort_by_freq=can_sort_by_freq)

def to_sorted_category_vals(**kwargs) -> list[str]:
    return [category_amount_spec.category_val for category_amount_spec in to_sorted_category_amount_specs(**kwargs)]

def to_sorted_chart_amount_specs(*, chart_amount_specs: Sequence[ChartCategoryAmountSpec],
        chart_field_name: str, sort_orders: SortOrderSpecs, chart_sort_order: SortOrder) -> Sequence[ChartCategoryAmountSpec]:
    return _to_sorted_amount_specs(amount_specs=chart_amount_specs, amount_spec_val_attribute_name='chart_val',
        field_name=chart_field_name, sort_orders=sort_orders, field_sort_order=chart_sort_order, can_sort_by_freq=False)

def to_sorted_series_category_amount_specs(
        series_category_amount_specs: Sequence[SeriesCategoryAmountSpec], series_field_name: str,
        sort_orders: SortOrderSpecs, series_sort_order: SortOrder) -> list[SeriesCategoryAmountSpec]:
    return _to_sorted_amount_specs(
        amount_specs=series_category_amount_specs, amount_spec_val_attribute_name='series_val',
        field_name=series_field_name, sort_orders=sort_orders, field_sort_order=series_sort_order,
        can_sort_by_freq=False)

def to_sorted_chart_series_category_amount_specs(
        chart_series_category_amount_specs: Sequence[ChartSeriesCategoryAmountSpec], chart_field_name: str,
        sort_orders: SortOrderSpecs, chart_sort_order: SortOrder) -> list[ChartSeriesCategoryAmountSpec]:
    return _to_sorted_amount_specs(
        amount_specs=chart_series_category_amount_specs, amount_spec_val_attribute_name='chart_val',
        field_name=chart_field_name, sort_orders=sort_orders, field_sort_order=chart_sort_order,
        can_sort_by_freq=False)


## Amount Specs specific to particular charting types ******************************************************************

## by category only (one chart, one series)

@dataclass(frozen=True)
class CategoryAmountSpecs:
    """
    Store frequency and percentage for each category value e.g. Japan in a category variable e.g. country

    Category-by variable label e.g. country, and one spec related to frequency per country value
    e.g. one for Italy, one for Germany etc.
    Frequency-related includes percentage. Both freq and pct are about the number of items.
    """
    category_field_name: str  ## e.g. Country
    category_amount_specs: Sequence[CategoryItemAmountSpec]  ## e.g. one amount spec per country
    sort_orders: SortOrderSpecs
    category_sort_order: SortOrder
    metric: ChartMetric = ChartMetric.FREQ
    decimal_points: int = 3

    def __str__(self):
        bits = [f"Category field value: {self.category_field_name}", ]
        for amount_spec in self.category_amount_specs:
            bits.append(f"    {amount_spec}")
        return dedent('\n'.join(bits))

    @property
    def sorted_category_vals(self):
        """
        Needed outside of this class.
        """
        return to_sorted_category_vals(category_amount_specs=self.category_amount_specs,
            category_field_name=self.category_field_name,
            sort_orders=self.sort_orders, category_sort_order=self.category_sort_order, can_sort_by_freq=True)

    def to_indiv_chart_spec(self) -> IndivChartSpec:
        n_records = sum(category_amount_spec.sub_total for category_amount_spec in self.category_amount_specs)
        ## collect data items according to correctly sorted x-axis category items
        ## Note - never gaps for by-category only charts
        series_data_items = []
        sorted_category_amount_specs = to_sorted_category_amount_specs(
            category_amount_specs=self.category_amount_specs, category_field_name=self.category_field_name,
            sort_orders=self.sort_orders, category_sort_order=self.category_sort_order, can_sort_by_freq=True)
        for category_amount_spec in sorted_category_amount_specs:
            data_item = DataItem(
                amount=category_amount_spec.amount,
                tool_tip=category_amount_spec.tool_tip,
                sub_total=category_amount_spec.sub_total)
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

## Sequences of Amount Specs *******************************************************************************************

## by category and by series

@dataclass(frozen=True)
class SeriesCategoryAmountSpecs:
    """
    Against each series store frequency and percentage for each category value
    e.g. Japan in a category variable e.g. country

    Series-by variable name e.g. Gender, and category-by variable name e.g. country,
    and one spec related to frequency per country value
    e.g. one for Italy, one for Germany etc.
    Frequency-related includes percentage. Both freq and pct are about the number of items.
    """
    category_field_name: str  ## e.g. Country
    series_field_name: str  ## e.g. Gender
    series_category_amount_specs: Sequence[SeriesCategoryAmountSpec]
    sort_orders: SortOrderSpecs
    category_sort_order: SortOrder
    series_sort_order: SortOrder
    decimal_points: int = 3

    def __str__(self):
        bits = [
            f"Series field name: {self.series_field_name}",
            f"Category field name: {self.category_field_name}",
        ]
        for series_category_amount_spec in self.series_category_amount_specs:
            bits.append(f"    {series_category_amount_spec}")
        return dedent('\n'.join(bits))

    @property
    def _all_category_vals(self) -> list[str]:
        """
        Relied upon by sorted_category_vals()
        """
        all_category_vals = set()
        for series_category_amount_spec in self.series_category_amount_specs:
            for amount_spec in series_category_amount_spec.category_amount_specs:
                all_category_vals.add(amount_spec.category_val)
        return sorted(all_category_vals)

    @property
    def sorted_category_vals(self):
        return sort_values_by_value_or_custom_if_possible(variable_name=self.category_field_name, values=self._all_category_vals,
            sort_orders=self.sort_orders, sort_order=self.category_sort_order)

    def to_indiv_chart_spec(self) -> IndivChartSpec:
        n_records = 0
        data_series_specs = []
        sorted_series_category_amount_specs = to_sorted_series_category_amount_specs(
            series_category_amount_specs=self.series_category_amount_specs, series_field_name=self.series_field_name,
            sort_orders=self.sort_orders, series_sort_order=self.series_sort_order)
        for series_category_amount_spec in sorted_series_category_amount_specs:
            category_val2spec = {}  ## so we can check expected category vals in order to see if category val in this actual series or not
            for amount_spec in series_category_amount_spec.category_amount_specs:
                n_records += amount_spec.sub_total  ## count up n_records while we're here in loop
                category_val2spec[amount_spec.category_val] = amount_spec
            series_data_items = []
            ## run through in sort order recognising that some items might not be present for a particular chart
            for category_val in self.sorted_category_vals:
                category_amount_spec = category_val2spec.get(category_val)
                if category_amount_spec:
                    data_item = DataItem(
                        amount=category_amount_spec.amount,
                        tool_tip=category_amount_spec.tool_tip,
                        sub_total=category_amount_spec.sub_total)
                else:
                    data_item = None
                series_data_items.append(data_item)
            data_series_spec = DataSeriesSpec(
                label=series_category_amount_spec.series_val,
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
class ChartCategoryAmountSpecs:
    """
    Against each chart store frequency and percentage for each category value
    e.g. Japan in a category variable e.g. country
    Also store labels for chart and category as a convenience so all the building blocks are in one place.
    """
    category_field_name: str  ## e.g. Country
    chart_field_name: str  ## e.g. Web Browser
    chart_category_amount_specs: Sequence[ChartCategoryAmountSpec]
    sort_orders: SortOrderSpecs
    category_sort_order: SortOrder
    chart_sort_order: SortOrder
    decimal_points: int = 3

    def __str__(self):
        bits = [
            f"Chart field label: {self.chart_field_name}",
            f"Category field label: {self.category_field_name}",
        ]
        for chart_category_amount_spec in self.chart_category_amount_specs:
            bits.append(f"    {chart_category_amount_spec}")
        return dedent('\n'.join(bits))

    @property
    def _all_category_vals(self) -> list[str]:
        all_category_vals = set()
        for chart_category_amount_spec in self.chart_category_amount_specs:
            for amount_spec in chart_category_amount_spec.category_amount_specs:
                all_category_vals.add(amount_spec.category_val)
        return sorted(all_category_vals)

    @property
    def sorted_category_vals(self):
        return sort_values_by_value_or_custom_if_possible(variable_name=self.category_field_name, values=self._all_category_vals,
            sort_orders=self.sort_orders, sort_order=self.category_sort_order)

    def to_indiv_chart_specs(self) -> Sequence[IndivChartSpec]:
        indiv_chart_specs = []
        sorted_chart_category_amount_specs = to_sorted_chart_amount_specs(
            chart_amount_specs=self.chart_category_amount_specs, chart_field_name=self.chart_field_name,
            sort_orders=self.sort_orders, chart_sort_order=self.chart_sort_order)
        for chart_category_amount_spec in sorted_chart_category_amount_specs:
            n_records = 0
            category_val2spec = {}  ## so we can check expected category vals in order to see if category val in this actual series or not
            for category_amount_spec in chart_category_amount_spec.category_amount_specs:
                n_records += category_amount_spec.sub_total
                category_val2spec[category_amount_spec.category_val] = category_amount_spec
            chart_data_items = []
            ## run through in sort order recognising that some items might not be present for a particular chart
            for category_val in self.sorted_category_vals:
                category_amount_spec = category_val2spec.get(category_val)
                if category_amount_spec:
                    data_item = category_amount_spec
                else:
                    data_item = None
                chart_data_items.append(data_item)
            data_series_spec = DataSeriesSpec(
                label=None,
                data_items=chart_data_items,
            )
            indiv_chart_spec = IndivChartSpec(
                label=f"{self.chart_field_name}: {chart_category_amount_spec.chart_val}",
                data_series_specs=[data_series_spec, ],
                n_records=n_records,
            )
            indiv_chart_specs.append(indiv_chart_spec)
        return indiv_chart_specs


## Chart, series, category

@dataclass(frozen=True)
class ChartSeriesCategoryAmountSpecs:
    """
    Against each chart and series store frequency and percentage for each category value
    e.g. Japan in a category variable e.g. country
    Also store labels for chart, series, and category as a convenience so all the building blocks are in one place.
    """
    category_field_name: str  ## e.g. Country
    series_field_name: str  ## e.g. Gender
    chart_field_name: str  ## e.g. Web Browser
    chart_series_category_amount_specs: Sequence[ChartSeriesCategoryAmountSpec]
    sort_orders: SortOrderSpecs
    category_sort_order: SortOrder
    series_sort_order: SortOrder
    chart_sort_order: SortOrder
    decimal_points: int = 3

    def __str__(self):
        bits = [
            f"Chart field name: {self.chart_field_name}",
            f"Series field name: {self.series_field_name}",
            f"Category field name: {self.category_field_name}",
        ]
        for chart_series_category_amount_spec in self.chart_series_category_amount_specs:
            bits.append(f"{chart_series_category_amount_spec}")
        return dedent('\n'.join(bits))

    @property
    def _all_category_vals(self) -> list[str]:
        all_category_vals = set()
        for chart_series_category_amount_spec in self.chart_series_category_amount_specs:
            for series_category_amount_specs in chart_series_category_amount_spec.series_category_amount_specs:
                for amount_spec in series_category_amount_specs.category_amount_specs:
                    all_category_vals.add(amount_spec.category_val)
        return sorted(all_category_vals)

    @property
    def sorted_category_vals(self):
        return sort_values_by_value_or_custom_if_possible(variable_name=self.category_field_name, values=self._all_category_vals,
            sort_orders=self.sort_orders, sort_order=self.category_sort_order)

    def to_indiv_chart_specs(self) -> Sequence[IndivChartSpec]:
        indiv_chart_specs = []
        sorted_chart_series_category_amount_specs = to_sorted_chart_series_category_amount_specs(
            chart_series_category_amount_specs=self.chart_series_category_amount_specs,
            chart_field_name=self.chart_field_name,
            sort_orders=self.sort_orders, chart_sort_order=self.chart_sort_order)
        for chart_series_category_amount_spec in sorted_chart_series_category_amount_specs:
            n_records = 0
            data_series_specs = []
            sorted_series_category_amount_specs = to_sorted_series_category_amount_specs(
                series_category_amount_specs=chart_series_category_amount_spec.series_category_amount_specs,
                series_field_name=self.series_field_name,
                sort_orders=self.sort_orders, series_sort_order=self.series_sort_order)
            for series_category_amount_spec in sorted_series_category_amount_specs:
                category_val2spec = {}  ## so we can check expected category vals in order to see if category val in this actual series or not
                for amount_spec in series_category_amount_spec.category_amount_specs:
                    n_records += amount_spec.sub_total  ## count up n_records while we're here in loop
                    category_val2spec[amount_spec.category_val] = amount_spec
                chart_series_data_items = []
                ## run through in sort order recognising that some items might not be present for a particular chart
                for category_val in self.sorted_category_vals:
                    category_amount_spec = category_val2spec.get(category_val)
                    if category_amount_spec:
                        data_item = category_amount_spec
                    else:
                        data_item = None
                    chart_series_data_items.append(data_item)
                data_series_spec = DataSeriesSpec(
                    label=series_category_amount_spec.series_val,
                    data_items=chart_series_data_items,
                )
                data_series_specs.append(data_series_spec)
            indiv_chart_spec = IndivChartSpec(
                label=f"{self.chart_field_name}: {chart_series_category_amount_spec.chart_val}",
                data_series_specs=data_series_specs,
                n_records=n_records,
            )
            indiv_chart_specs.append(indiv_chart_spec)
        return indiv_chart_specs
