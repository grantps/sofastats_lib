from collections.abc import Sequence
from dataclasses import dataclass

import pandas as pd

from sofastats.conf.main import DbeSpec, SortOrder, SortOrderSpecs
from sofastats.data_extraction.charts.scatter_plot import ScatterDataSeriesSpec, ScatterIndivChartSpec
from sofastats.data_extraction.db import ExtendedCursor
from sofastats.utils.item_sorting import sort_by_text

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
    sorted_series_xy_specs: Sequence[SeriesXYSpec]


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
            sorted_data_series_specs=[data_series_spec],
            label=None,
        )
        indiv_chart_specs = [indiv_chart_spec, ]
        return indiv_chart_specs

@dataclass(frozen=True)
class SeriesXYSpecs:
    x_field_name: str
    y_field_name: str
    series_field_name: str
    sorted_series_xy_specs: Sequence[SeriesXYSpec]

    def to_indiv_chart_specs(self) -> Sequence[ScatterIndivChartSpec]:
        sorted_data_series_specs = []
        for series_xy_spec in self.sorted_series_xy_specs:
            data_series_spec = ScatterDataSeriesSpec(
                label=series_xy_spec.label,
                xy_pairs=series_xy_spec.xys,
            )
            sorted_data_series_specs.append(data_series_spec)
        indiv_chart_spec = ScatterIndivChartSpec(
            sorted_data_series_specs=sorted_data_series_specs,
            label=None,
        )
        indiv_chart_specs = [indiv_chart_spec, ]
        return indiv_chart_specs

@dataclass(frozen=True)
class ChartXYSpecs:
    x_field_name: str
    y_field_name: str
    sorted_charts_xy_specs: Sequence[ChartXYSpec]

    def to_indiv_chart_specs(self) -> Sequence[ScatterIndivChartSpec]:
        indiv_chart_specs = []
        for charts_xy_spec in self.sorted_charts_xy_specs:
            data_series_spec = ScatterDataSeriesSpec(
                label=None,
                xy_pairs=charts_xy_spec.xys,
            )
            indiv_chart_spec = ScatterIndivChartSpec(
                sorted_data_series_specs=[data_series_spec, ],
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
    sorted_chart_series_xy_specs: Sequence[ChartSeriesXYSpec]

    def to_indiv_chart_specs(self) -> Sequence[ScatterIndivChartSpec]:
        indiv_chart_specs = []
        for chart_series_xy_spec in self.sorted_chart_series_xy_specs:
            sorted_data_series_specs = []
            for series_xy_spec in chart_series_xy_spec.sorted_series_xy_specs:
                data_series_spec = ScatterDataSeriesSpec(
                    label=series_xy_spec.label,
                    xy_pairs=series_xy_spec.xys,
                )
                sorted_data_series_specs.append(data_series_spec)
            indiv_chart_spec = ScatterIndivChartSpec(
                sorted_data_series_specs=sorted_data_series_specs,
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
    sorted_series_xy_specs = []
    series_vals = df['series_val'].unique()
    sorted_series_vals = sort_by_text(
        variable_name=series_field_name, values=series_vals, sort_orders=sort_orders, sort_order=series_sort_order)
    for series_val in sorted_series_vals:
        xys = df.loc[df['series_val'] == series_val, ['x', 'y']].to_records(index=False).tolist()
        series_xy_spec = SeriesXYSpec(
            label=series_val,
            xys=xys,
        )
        sorted_series_xy_specs.append(series_xy_spec)
    data_spec = SeriesXYSpecs(
        x_field_name=x_field_name,
        y_field_name=y_field_name,
        series_field_name=series_field_name,
        sorted_series_xy_specs=sorted_series_xy_specs,
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
    sorted_charts_xy_specs = []
    chart_vals = df['chart_val'].unique()
    sorted_chart_vals = sort_by_text(
        variable_name=chart_field_name, values=chart_vals, sort_orders=sort_orders, sort_order=chart_sort_order)
    for chart_val in sorted_chart_vals:
        xys = df.loc[df['chart_val'] == chart_val, ['x', 'y']].to_records(index=False).tolist()
        chart_xy_spec = ChartXYSpec(
            chart_value=chart_val,
            label=f"{chart_field_name}: {chart_val}",
            xys=xys,
        )
        sorted_charts_xy_specs.append(chart_xy_spec)
    data_spec = ChartXYSpecs(
        x_field_name=x_field_name,
        y_field_name=y_field_name,
        sorted_charts_xy_specs=sorted_charts_xy_specs,
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
    sorted_chart_series_xy_specs = []
    chart_vals = df['chart_val'].unique()
    sorted_chart_vals = sort_by_text(
        variable_name=chart_field_name, values=chart_vals, sort_orders=sort_orders, sort_order=chart_sort_order)
    for chart_val in sorted_chart_vals:
        sorted_series_xy_specs = []
        series_vals = df.loc[df['chart_val'] == chart_val, 'series_val'].unique()
        sorted_series_vals = sort_by_text(
            variable_name=series_field_name, values=series_vals, sort_orders=sort_orders, sort_order=series_sort_order)
        for series_val in sorted_series_vals:
            xys = df.loc[
                (df['chart_val'] == chart_val) & (df['series_val'] == series_val),
                ['x', 'y']
            ].to_records(index=False).tolist()
            series_xy_spec = SeriesXYSpec(
                label=series_val,
                xys=xys,
            )
            sorted_series_xy_specs.append(series_xy_spec)
        chart_series_xy_spec = ChartSeriesXYSpec(
            chart_value=chart_val,
            label=f"{chart_field_name}: {chart_val}",
            sorted_series_xy_specs=sorted_series_xy_specs,
        )
        sorted_chart_series_xy_specs.append(chart_series_xy_spec)
    data_spec = ChartSeriesXYSpecs(
        x_field_name=x_field_name,
        y_field_name=y_field_name,
        series_field_name=series_field_name,
        chart_field_name=chart_field_name,
        sorted_chart_series_xy_specs=sorted_chart_series_xy_specs,
    )
    return data_spec
