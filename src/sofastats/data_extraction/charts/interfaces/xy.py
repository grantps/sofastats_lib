from collections.abc import Sequence
from dataclasses import dataclass

import pandas as pd

from sofastats.conf.main import DbeSpec, SortOrder, SortOrderSpecs
from sofastats.data_extraction.charts.scatter_plot import ScatterDataSeriesSpec, ScatterIndivChartSpec
from sofastats.data_extraction.db import ExtendedCursor

@dataclass(frozen=True)
class SeriesXYSpec:
    label: str
    xys: Sequence[tuple[float, float]]

@dataclass(frozen=True)
class ChartXYSpec:
    chart_value: str
    label: str
    xys: Sequence[tuple[float, float]]

@dataclass(frozen=True)
class ChartSeriesXYSpec:
    chart_value: str
    label: str
    series_xy_specs: Sequence[SeriesXYSpec]

## Sorting functions ***************************************************************************************************

def _to_sorted_xy_specs(*, xy_specs: Sequence[SeriesXYSpec | ChartXYSpec | ChartSeriesXYSpec],
        val_attribute_name: str, field_name: str, sort_orders: SortOrderSpecs, field_sort_order: SortOrder) -> list:
    if field_sort_order == SortOrder.VALUE:
        def sort_me(xy_spec):
            return getattr(xy_spec, val_attribute_name)

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

        def sort_me(xy_spec):
            field_value = getattr(xy_spec, val_attribute_name)
            try:
                idx_for_ordered_position = value2order[field_value]
            except KeyError:
                raise Exception(
                    f"The custom sort order you supplied for values in variable '{field_name}' "
                    f"didn't include value '{field_value}' so please fix that and try again.")
            return idx_for_ordered_position

        reverse = False
    else:
        raise Exception(
            f"Unexpected chart_sort_order ({field_sort_order})"
            f"\nINCREASING and DECREASING is for ordering by frequency which makes no sense for {field_name}."
        )
    sorted_xy_specs = sorted(xy_specs, key=sort_me, reverse=reverse)
    return sorted_xy_specs

def to_sorted_charts_xy_specs(*, charts_xy_specs: Sequence[ChartXYSpec], chart_field_name: str,
        sort_orders: SortOrderSpecs, chart_sort_order: SortOrder) -> list[ChartXYSpec]:
    return _to_sorted_xy_specs(xy_specs=charts_xy_specs, val_attribute_name='chart_value', field_name=chart_field_name,
        sort_orders=sort_orders, field_sort_order=chart_sort_order)

def to_sorted_series_xy_specs(series_xy_specs: Sequence[SeriesXYSpec], series_field_name: str,
        sort_orders: SortOrderSpecs, series_sort_order: SortOrder) -> list[SeriesXYSpec]:
    return _to_sorted_xy_specs(xy_specs=series_xy_specs, val_attribute_name='label', field_name=series_field_name,
        sort_orders=sort_orders, field_sort_order=series_sort_order)

def to_sorted_chart_series_xy_specs(chart_series_xy_specs: Sequence[ChartSeriesXYSpec], chart_field_name: str,
        sort_orders: SortOrderSpecs, chart_sort_order: SortOrder) -> list[ChartSeriesXYSpec]:
    return _to_sorted_xy_specs(xy_specs=chart_series_xy_specs, val_attribute_name='chart_value', field_name=chart_field_name,
        sort_orders=sort_orders, field_sort_order=chart_sort_order)


## Main Specs **********************************************************************************************************

@dataclass(frozen=True)
class XYSpecs:
    x_field_name: str
    y_field_name: str
    xys: Sequence[tuple[float, float]]

    def to_indiv_chart_specs(self) -> Sequence[ScatterIndivChartSpec]:
        data_series_spec = ScatterDataSeriesSpec(
            label=None,
            xy_pairs=self.xys,
        )
        indiv_chart_spec = ScatterIndivChartSpec(
            series_field_name=None,
            sort_orders=None,
            series_sort_order=None,
            data_series_specs=[data_series_spec],
            label=None,
        )
        indiv_chart_specs = [indiv_chart_spec, ]
        return indiv_chart_specs

@dataclass(frozen=True)
class SeriesXYSpecs:
    x_field_name: str
    y_field_name: str
    series_field_name: str
    sort_orders: SortOrderSpecs
    series_sort_order: SortOrder
    series_xy_specs: Sequence[SeriesXYSpec]

    def to_indiv_chart_specs(self) -> Sequence[ScatterIndivChartSpec]:
        data_series_specs = []
        for series_xy_spec in self.series_xy_specs:
            data_series_spec = ScatterDataSeriesSpec(
                label=series_xy_spec.label,
                xy_pairs=series_xy_spec.xys,
            )
            data_series_specs.append(data_series_spec)
        indiv_chart_spec = ScatterIndivChartSpec(
            series_field_name=self.series_field_name,
            sort_orders=self.sort_orders,
            series_sort_order=self.series_sort_order,
            data_series_specs=data_series_specs,
            label=None,
        )
        indiv_chart_specs = [indiv_chart_spec, ]
        return indiv_chart_specs

@dataclass(frozen=True)
class ChartXYSpecs:
    x_field_name: str
    y_field_name: str
    chart_field_name: str
    sort_orders: SortOrderSpecs
    chart_sort_order: SortOrder
    charts_xy_specs: Sequence[ChartXYSpec]

    def to_indiv_chart_specs(self) -> Sequence[ScatterIndivChartSpec]:
        indiv_chart_specs = []
        sorted_charts_xy_specs = to_sorted_charts_xy_specs(
            charts_xy_specs=self.charts_xy_specs, chart_field_name=self.chart_field_name,
            sort_orders=self.sort_orders, chart_sort_order=self.chart_sort_order)
        for charts_xy_spec in sorted_charts_xy_specs:
            data_series_spec = ScatterDataSeriesSpec(
                label=None,
                xy_pairs=charts_xy_spec.xys,
            )
            indiv_chart_spec = ScatterIndivChartSpec(
                series_field_name=None,
                sort_orders=None,
                series_sort_order=None,
                data_series_specs=[data_series_spec, ],
                label=charts_xy_spec.label,
            )
            indiv_chart_specs.append(indiv_chart_spec)
        return indiv_chart_specs

@dataclass(frozen=True)
class ChartSeriesXYSpecs:
    x_field_name: str
    y_field_name: str
    series_field_name: str
    chart_field_name: str
    sort_orders: SortOrderSpecs
    series_sort_order: SortOrder
    chart_sort_order: SortOrder
    chart_series_xy_specs: Sequence[ChartSeriesXYSpec]

    def to_indiv_chart_specs(self) -> Sequence[ScatterIndivChartSpec]:
        indiv_chart_specs = []
        sorted_series_charts_xy_specs =to_sorted_chart_series_xy_specs(
            chart_series_xy_specs=self.chart_series_xy_specs, chart_field_name=self.chart_field_name,
            sort_orders=self.sort_orders, chart_sort_order=self.chart_sort_order)
        for chart_series_xy_spec in sorted_series_charts_xy_specs:
            data_series_specs = []
            sorted_series_xy_specs = to_sorted_series_xy_specs(
                series_xy_specs=chart_series_xy_spec.series_xy_specs, series_field_name=self.series_field_name,
                sort_orders=self.sort_orders, series_sort_order=self.series_sort_order)
            for series_xy_spec in sorted_series_xy_specs:
                data_series_spec = ScatterDataSeriesSpec(
                    label=series_xy_spec.label,
                    xy_pairs=series_xy_spec.xys,
                )
                data_series_specs.append(data_series_spec)
            indiv_chart_spec = ScatterIndivChartSpec(
                series_field_name=self.series_field_name,
                sort_orders=self.sort_orders,
                series_sort_order=self.series_sort_order,
                data_series_specs=data_series_specs,
                label=chart_series_xy_spec.label,
            )
            indiv_chart_specs.append(indiv_chart_spec)
        return indiv_chart_specs


## *********************************************************************************************************************

def get_by_xy_charting_spec(*, cur: ExtendedCursor, dbe_spec: DbeSpec, source_table_name: str,
        x_field_name: str, y_field_name: str,
        table_filter_sql: str | None = None) -> XYSpecs:
    ## prepare items
    x_field_name_quoted = dbe_spec.entity_quoter(x_field_name)
    y_field_name_quoted = dbe_spec.entity_quoter(y_field_name)
    source_table_name_quoted = dbe_spec.entity_quoter(source_table_name)
    AND_table_filter_sql = f"AND ({table_filter_sql})" if table_filter_sql else ''
    ## assemble SQL
    sql = f"""\
    SELECT
        {x_field_name_quoted} AS x,
        {y_field_name_quoted} AS y
    FROM {source_table_name_quoted}
    WHERE {x_field_name_quoted} IS NOT NULL
    AND {y_field_name_quoted} IS NOT NULL
    {AND_table_filter_sql}
    """
    ## get data
    cur.exe(sql)
    data = cur.fetchall()
    ## build result
    data_spec = XYSpecs(
        x_field_name=x_field_name,
        y_field_name=y_field_name,
        xys=data,
    )
    return data_spec

def get_by_series_xy_charting_spec(*, cur: ExtendedCursor, dbe_spec: DbeSpec, source_table_name: str,
        x_field_name: str, y_field_name: str,
        series_field_name: str,
        sort_orders: SortOrderSpecs,
        series_sort_order: SortOrder,
        table_filter_sql: str | None = None) -> SeriesXYSpecs:
    ## prepare items
    x_fld_name_quoted = dbe_spec.entity_quoter(x_field_name)
    y_fld_name_quoted = dbe_spec.entity_quoter(y_field_name)
    series_fld_name_quoted = dbe_spec.entity_quoter(series_field_name)
    source_table_name_quoted = dbe_spec.entity_quoter(source_table_name)
    AND_table_filter_sql = f"AND ({table_filter_sql})" if table_filter_sql else ''
    ## assemble SQL
    sql = f"""\
    SELECT
        {series_fld_name_quoted} AS series_val,
        {x_fld_name_quoted} AS x,
        {y_fld_name_quoted} AS y
    FROM {source_table_name_quoted}
    WHERE {x_fld_name_quoted} IS NOT NULL
    AND {y_fld_name_quoted} IS NOT NULL
    {AND_table_filter_sql}
    """
    ## get data
    cur.exe(sql)
    data = cur.fetchall()
    cols = ['series_val', 'x', 'y']
    df = pd.DataFrame(data, columns=cols)
    ## build result
    series_xy_specs = []
    series_vals = df['series_val'].unique()
    for series_val in series_vals:
        xys = df.loc[df['series_val'] == series_val, ['x', 'y']].to_records(index=False).tolist()
        series_xy_spec = SeriesXYSpec(
            label=series_val,
            xys=xys,
        )
        series_xy_specs.append(series_xy_spec)
    data_spec = SeriesXYSpecs(
        x_field_name=x_field_name,
        y_field_name=y_field_name,
        series_field_name=series_field_name,
        sort_orders=sort_orders,
        series_sort_order=series_sort_order,
        series_xy_specs=series_xy_specs,
    )
    return data_spec

def get_by_chart_xy_charting_spec(*, cur: ExtendedCursor, dbe_spec: DbeSpec, source_table_name: str,
        x_field_name: str,
        y_field_name: str,
        chart_field_name: str,
        sort_orders: SortOrderSpecs,
        chart_sort_order: SortOrder,
        table_filter_sql: str | None = None) -> ChartXYSpecs:
    ## prepare items
    x_field_name_quoted = dbe_spec.entity_quoter(x_field_name)
    y_field_name_quoted = dbe_spec.entity_quoter(y_field_name)
    chart_field_name_quoted = dbe_spec.entity_quoter(chart_field_name)
    source_table_name_quoted = dbe_spec.entity_quoter(source_table_name)
    AND_table_filter_sql = f"AND ({table_filter_sql})" if table_filter_sql else ''
    ## assemble SQL
    sql = f"""\
    SELECT
        {chart_field_name_quoted} AS charts_val,
        {x_field_name_quoted} AS x,
        {y_field_name_quoted} AS y
    FROM {source_table_name_quoted}
    WHERE {x_field_name_quoted} IS NOT NULL
    AND {y_field_name_quoted} IS NOT NULL
    {AND_table_filter_sql}
    """
    ## get data
    cur.exe(sql)
    data = cur.fetchall()
    cols = ['chart_val', 'x', 'y']
    df = pd.DataFrame(data, columns=cols)
    ## build result
    charts_xy_specs = []
    chart_vals = df['chart_val'].unique()
    for chart_val in chart_vals:
        xys = df.loc[df['chart_val'] == chart_val, ['x', 'y']].to_records(index=False).tolist()
        chart_xy_spec = ChartXYSpec(
            chart_value=chart_val,
            label=f"{chart_field_name}: {chart_val}",
            xys=xys,
        )
        charts_xy_specs.append(chart_xy_spec)
    data_spec = ChartXYSpecs(
        x_field_name=x_field_name,
        y_field_name=y_field_name,
        chart_field_name=chart_field_name,
        sort_orders=sort_orders,
        chart_sort_order=chart_sort_order,
        charts_xy_specs=charts_xy_specs,
    )
    return data_spec

def get_by_chart_series_xy_charting_spec(*, cur: ExtendedCursor, dbe_spec: DbeSpec, source_table_name: str,
        x_field_name: str, y_field_name: str,
        series_field_name: str, chart_field_name: str,
        sort_orders: SortOrderSpecs,
        series_sort_order: SortOrder, chart_sort_order: SortOrder,
        table_filter_sql: str | None = None) -> ChartSeriesXYSpecs:
    ## prepare items
    x_field_name_quoted = dbe_spec.entity_quoter(x_field_name)
    y_field_name_quoted = dbe_spec.entity_quoter(y_field_name)
    series_field_name_quoted = dbe_spec.entity_quoter(series_field_name)
    chart_field_name_quoted = dbe_spec.entity_quoter(chart_field_name)
    source_table_name_quoted = dbe_spec.entity_quoter(source_table_name)
    AND_table_filter_sql = f"AND ({table_filter_sql})" if table_filter_sql else ''
    ## assemble SQL
    sql = f"""\
    SELECT
        {chart_field_name_quoted} AS chart_val,
        {series_field_name_quoted} AS series_val,
        {x_field_name_quoted} AS x,
        {y_field_name_quoted} AS y
    FROM {source_table_name_quoted}
    WHERE {x_field_name_quoted} IS NOT NULL
    AND {y_field_name_quoted} IS NOT NULL
    {AND_table_filter_sql}
    """
    ## get data
    cur.exe(sql)
    data = cur.fetchall()
    cols = ['chart_val', 'series_val', 'x', 'y']
    df = pd.DataFrame(data, columns=cols)
    ## build result
    chart_series_xy_specs = []
    chart_vals = df['chart_val'].unique()
    for chart_val in chart_vals:
        series_xy_specs = []
        series_vals = df.loc[df['chart_val'] == chart_val, 'series_val'].unique()
        for series_val in series_vals:
            xys = df.loc[
                (df['chart_val'] == chart_val) & (df['series_val'] == series_val),
                ['x', 'y']
            ].to_records(index=False).tolist()
            series_xy_spec = SeriesXYSpec(
                label=series_val,
                xys=xys,
            )
            series_xy_specs.append(series_xy_spec)
        chart_series_xy_spec = ChartSeriesXYSpec(
            chart_value=chart_val,
            label=f"{chart_field_name}: {chart_val}",
            series_xy_specs=series_xy_specs,
        )
        chart_series_xy_specs.append(chart_series_xy_spec)
    data_spec = ChartSeriesXYSpecs(
        x_field_name=x_field_name,
        y_field_name=y_field_name,
        series_field_name=series_field_name,
        chart_field_name=chart_field_name,
        sort_orders=sort_orders,
        series_sort_order=series_sort_order,
        chart_sort_order=chart_sort_order,
        chart_series_xy_specs=chart_series_xy_specs,
    )
    return data_spec
