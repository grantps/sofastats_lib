"""
Amounts - frequencies, percentages, averages, and sums.
Common code used by Area, Bar, and Line charts
"""

import pandas as pd

from sofastats.conf.main import ChartMetric, DbeSpec, SortOrder, SortOrderSpecs
from sofastats.data_extraction.charts.interfaces.amounts import (
    CategoryAmountSpecs, CategoryItemAmountSpec,
    ChartCategoryAmountSpec, ChartCategoryAmountSpecs,
    ChartSeriesCategoryAmountSpec, ChartSeriesCategoryAmountSpecs,
    SeriesCategoryAmountSpec, SeriesCategoryAmountSpecs)
from sofastats.data_extraction.db import ExtendedCursor
from sofastats.data_extraction.utils import to_sorted_values

def validate_metric_and_field_name(metric: ChartMetric, field_name: str):
    if metric in (ChartMetric.AVG, ChartMetric.SUM):
        if not field_name:
            raise ValueError("field_name must be set if calculating Average or Sum")
    elif metric in (ChartMetric.FREQ, ChartMetric.PCT):
        if field_name:
            raise ValueError("field_name should only be set if calculating Average or Sum")

def get_by_category_charting_spec(*, cur: ExtendedCursor, dbe_spec: DbeSpec, source_table_name: str,
        category_field_name: str, sort_orders: SortOrderSpecs, category_sort_order: SortOrder = SortOrder.VALUE,
        metric: ChartMetric = ChartMetric.FREQ, field_name: str | None = None,
        table_filter_sql: str | None = None, decimal_points: int = 3) -> CategoryAmountSpecs:
    """
    Intermediate charting spec - close to the data
    """
    validate_metric_and_field_name(metric, field_name)
    ## prepare items
    field_name_quoted = dbe_spec.entity_quoter(field_name) if field_name else None
    category_field_name_quoted = dbe_spec.entity_quoter(category_field_name)
    source_table_name_quoted = dbe_spec.entity_quoter(source_table_name)
    AND_table_filter_sql = f"AND ({table_filter_sql})" if table_filter_sql else ''
    ## handle metric requirements
    if metric in (ChartMetric.FREQ, ChartMetric.PCT):
        agg_fields_clause = f"""\
        COUNT(*) AS
          freq,
            (100.0 * COUNT(*)) / (SELECT COUNT(*) FROM {source_table_name_quoted}) AS
          raw_category_pct
        """
        if metric == ChartMetric.FREQ:
            def get_amount_and_tool_tip(freq: int, category_pct: float) -> tuple[int, str]:
                return int(freq), f"{freq}<br>({round(category_pct, decimal_points)}%)"
        elif metric == ChartMetric.PCT:
            def get_amount_and_tool_tip(freq: int, category_pct: float) -> tuple[int, str]:
                return int(category_pct), f"{freq}<br>({round(category_pct, decimal_points)}%)"
        else:
            raise ValueError(f"Metric {metric} is not supported")
    elif metric == ChartMetric.AVG:
        agg_fields_clause = f"""\
        AVG({field_name_quoted}) AS
          average_value
        """
        def get_amount_and_tool_tip(avg: float) -> tuple[float, str]:
            return float(avg), str(round(avg, 2))
    elif metric == ChartMetric.SUM:
        agg_fields_clause = f"""\
        SUM({field_name_quoted}) AS
          summed_value
        """
        def get_amount_and_tool_tip(summed_value: float) -> tuple[int, str]:
            return int(summed_value), str(round(summed_value, 2))
    else:
        raise ValueError(f"Metric {metric} is not supported")
    ## assemble SQL
    sql = f"""\
    SELECT
        {category_field_name_quoted} AS
      category_val,
        COUNT(*) AS
      sub_total,  -- needed for n_records even if not ChartMetric.FREQ
        {agg_fields_clause}
    FROM {source_table_name_quoted}
    WHERE {category_field_name_quoted} IS NOT NULL
    {AND_table_filter_sql}
    GROUP BY {category_field_name_quoted}
    ORDER BY {category_field_name_quoted}
    """
    ## get data
    cur.exe(sql)
    data = cur.fetchall()
    ## build result
    category_amount_specs = []
    for category_val, sub_total, *agg_fields in data:
        amount, tool_tip = get_amount_and_tool_tip(*agg_fields)
        amount_spec = CategoryItemAmountSpec(category_val=category_val,
            amount=amount, tool_tip=tool_tip, sub_total=sub_total)
        category_amount_specs.append(amount_spec)
    data_spec = CategoryAmountSpecs(
        category_field_name=category_field_name,
        category_amount_specs=category_amount_specs,
        sort_orders=sort_orders,
        category_sort_order=category_sort_order,
        metric=metric,
        decimal_points=decimal_points,
    )
    return data_spec

def get_by_series_category_charting_spec(cur: ExtendedCursor, source_table_name: str, dbe_spec: DbeSpec,
        category_field_name: str, series_field_name: str,
        sort_orders: SortOrderSpecs,
        series_sort_order: SortOrder = SortOrder.VALUE, category_sort_order: SortOrder = SortOrder.VALUE,
        metric: ChartMetric = ChartMetric.FREQ, field_name: str | None = None,
        table_filter_sql: str | None = None, decimal_points: int = 3) -> SeriesCategoryAmountSpecs:
    """
    Intermediate charting spec - close to the data

    For clustered bar charts and multi-line line charts
    """
    validate_metric_and_field_name(metric, field_name)
    ## prepare items
    field_name_quoted = dbe_spec.entity_quoter(field_name) if field_name else None
    category_field_name_quoted = dbe_spec.entity_quoter(category_field_name)
    series_field_name_quoted = dbe_spec.entity_quoter(series_field_name)
    source_table_name_quoted = dbe_spec.entity_quoter(source_table_name)
    AND_table_filter_sql = f"AND ({table_filter_sql})" if table_filter_sql else ''
    ## handle metric requirements
    if metric in (ChartMetric.FREQ, ChartMetric.PCT):
        agg_fields_clause = f"""\
        COUNT(*) AS
          freq,
            ((100.0 * COUNT(*))
            / (
              SELECT COUNT(*)
              FROM {source_table_name_quoted}
              WHERE {series_field_name_quoted} = src.{series_field_name_quoted}
            )) AS
          category_pct
        """
        if metric == ChartMetric.FREQ:
            def get_amount_and_tool_tip(args_dict: dict) -> tuple[int, str]:
                returned_tool_tip = (f"{args_dict['category_val']}, {args_dict['series_val']}"
                    f"<br>{args_dict['freq']}"
                    f"<br>({round(args_dict['category_pct'], decimal_points)}%)")
                return int(args_dict['freq']), returned_tool_tip
        elif metric == ChartMetric.PCT:
            def get_amount_and_tool_tip(args_dict: dict) -> tuple[int, str]:
                returned_tool_tip = (f"{args_dict['category_val']}, {args_dict['series_val']}"
                    f"<br>{args_dict['freq']}"
                    f"<br>({round(args_dict['category_pct'], decimal_points)}%)")
                return int(args_dict['category_pct']), returned_tool_tip
        else:
            raise ValueError(f"Metric {metric} is not supported")
    elif metric == ChartMetric.AVG:
        agg_fields_clause = f"""\
        AVG({field_name_quoted}) AS
          average_value
        """
        def get_amount_and_tool_tip(args_dict: dict) -> tuple[float, str]:
            returned_tool_tip = (f"{args_dict['category_val']}, {args_dict['series_val']}"
                f"<br>{round(args_dict['avg'], decimal_points)}")
            return float(args_dict['avg']), returned_tool_tip
    elif metric == ChartMetric.SUM:
        agg_fields_clause = f"""\
        SUM({field_name_quoted}) AS
          summed_value
        """
        def get_amount_and_tool_tip(args_dict: dict) -> tuple[int, str]:
            returned_tool_tip = (
                f"{args_dict['category_val']}, {args_dict['series_val']}"
                f"<br>{round(args_dict['summed_value'], decimal_points)}")
            return int(args_dict['summed_value']), returned_tool_tip
    else:
        raise ValueError(f"Metric {metric} is not supported")
    ## assemble SQL
    sql = f"""\
    SELECT
        {series_field_name_quoted} AS
      series_val,
        {category_field_name_quoted} AS
      category_val,
        COUNT(*) AS
      sub_total,  -- needed for n_records even if not ChartMetric.FREQ
        {agg_fields_clause}
    FROM {source_table_name_quoted} AS src
    WHERE {series_field_name_quoted} IS NOT NULL
    AND {category_field_name_quoted} IS NOT NULL
    {AND_table_filter_sql}
    GROUP BY {series_field_name_quoted}, {category_field_name_quoted}
    ORDER BY {series_field_name_quoted}, {category_field_name_quoted}
    """
    ## get data
    cur.exe(sql)
    data = cur.fetchall()
    cols = [desc[0] for desc in cur.description]
    df = pd.DataFrame(data, columns=cols)
    series_category_amount_specs = []
    orig_series_vals = df['series_val'].unique()
    sorted_series_vals = to_sorted_values(orig_vals=orig_series_vals,
        field_name=series_field_name, sort_orders=sort_orders, sort_order=series_sort_order)
    for series_val in sorted_series_vals:
        category_item_amount_specs = []
        for _i, row in df.loc[df['series_val'] == series_val].iterrows():
            amount, tool_tip = get_amount_and_tool_tip(row.to_dict())
            amount_spec = CategoryItemAmountSpec(
                category_val=row['category_val'],
                amount=amount,
                tool_tip=tool_tip,
                sub_total=row['sub_total'],
            )
            category_item_amount_specs.append(amount_spec)
        series_category_amount_spec = SeriesCategoryAmountSpec(
            series_val=series_val,
            category_amount_specs=category_item_amount_specs,
        )
        series_category_amount_specs.append(series_category_amount_spec)
    data_spec = SeriesCategoryAmountSpecs(
        series_field_name=series_field_name,
        category_field_name=category_field_name,
        series_category_amount_specs=series_category_amount_specs,
        sort_orders=sort_orders,
        category_sort_order=category_sort_order,
        decimal_points=decimal_points,
    )
    return data_spec

def get_by_chart_category_charting_spec(*, cur: ExtendedCursor, dbe_spec: DbeSpec, source_table_name: str,
        category_field_name: str, chart_field_name: str,
        sort_orders: SortOrderSpecs,
        category_sort_order: SortOrder = SortOrder.VALUE, chart_sort_order: SortOrder = SortOrder.VALUE,
        metric: ChartMetric = ChartMetric.FREQ, field_name: str | None = None,
        table_filter_sql: str | None = None, decimal_points: int = 3) -> ChartCategoryAmountSpecs:
    """
    Intermediate charting spec - close to the data
    """
    validate_metric_and_field_name(metric, field_name)
    ## prepare items
    field_name_quoted = dbe_spec.entity_quoter(field_name) if field_name else None
    category_field_name_quoted = dbe_spec.entity_quoter(category_field_name)
    chart_field_name_quoted = dbe_spec.entity_quoter(chart_field_name)
    source_table_name_quoted = dbe_spec.entity_quoter(source_table_name)
    AND_table_filter_sql = f"AND ({table_filter_sql})" if table_filter_sql else ''
    ## handle metric requirements
    if metric in (ChartMetric.FREQ, ChartMetric.PCT):
        agg_fields_clause = f"""\
        COUNT(*) AS
          freq,
            ((100.0 * COUNT(*))
            / (
              SELECT COUNT(*)
              FROM {source_table_name_quoted}
              WHERE {chart_field_name_quoted} = src.{chart_field_name_quoted}
            )) AS
          category_pct
        """
        if metric == ChartMetric.FREQ:
            def get_amount_and_tool_tip(args_dict: dict) -> tuple[int, str]:
                returned_tool_tip = (f"{args_dict['category_val']}, {args_dict['chart_val']}"
                    f"<br>{args_dict['freq']}"
                    f"<br>({round(args_dict['category_pct'], decimal_points)}%)")
                return int(args_dict['freq']), returned_tool_tip
        elif metric == ChartMetric.PCT:
            def get_amount_and_tool_tip(args_dict: dict) -> tuple[int, str]:
                returned_tool_tip = (f"{args_dict['category_val']}, {args_dict['chart_val']}"
                    f"<br>{args_dict['freq']}"
                    f"<br>({round(args_dict['category_pct'], decimal_points)}%)")
                return int(args_dict['category_pct']), returned_tool_tip
        else:
            raise ValueError(f"Metric {metric} is not supported")
    elif metric == ChartMetric.AVG:
        agg_fields_clause = f"""\
        AVG({field_name_quoted}) AS
          average_value
        """
        def get_amount_and_tool_tip(args_dict: dict) -> tuple[float, str]:
            returned_tool_tip = (f"{args_dict['category_val']}, {args_dict['chart_val']}"
                f"<br>{round(args_dict['avg'], decimal_points)}")
            return float(args_dict['avg']), returned_tool_tip
    elif metric == ChartMetric.SUM:
        agg_fields_clause = f"""\
        SUM({field_name_quoted}) AS
          summed_value
        """
        def get_amount_and_tool_tip(args_dict: dict) -> tuple[int, str]:
            returned_tool_tip = (
                f"{args_dict['category_val']}, {args_dict['chart_val']}"
                f"<br>{round(args_dict['summed_value'], decimal_points)}")
            return int(args_dict['summed_value']), returned_tool_tip
    else:
        raise ValueError(f"Metric {metric} is not supported")
    ## assemble SQL
    sql = f"""\
    SELECT
        {chart_field_name_quoted} AS
      chart_val,
        {category_field_name_quoted} AS
      category_val,
        COUNT(*) AS
      sub_total,  -- needed for n_records even if not ChartMetric.FREQ
        {agg_fields_clause}
    FROM {source_table_name_quoted} AS src
    WHERE {chart_field_name_quoted} IS NOT NULL
    AND {category_field_name_quoted} IS NOT NULL
    {AND_table_filter_sql}
    GROUP BY {chart_field_name_quoted}, {category_field_name_quoted}
    ORDER BY {chart_field_name_quoted}, {category_field_name_quoted}
    """
    ## get data
    cur.exe(sql)
    data = cur.fetchall()
    cols = [desc[0] for desc in cur.description]
    df = pd.DataFrame(data, columns=cols)
    chart_category_amount_specs = []
    orig_chart_vals = df['chart_val'].unique()
    sorted_chart_vals = to_sorted_values(orig_vals=orig_chart_vals,
        field_name=chart_field_name, sort_orders=sort_orders, sort_order=chart_sort_order)
    for chart_val in sorted_chart_vals:
        amount_specs = []
        for _i, row in df.loc[df['chart_val'] == chart_val].iterrows():
            amount, tool_tip = get_amount_and_tool_tip(row.to_dict())
            amount_spec = CategoryItemAmountSpec(
                category_val=row['category_val'],
                amount=amount,
                tool_tip=tool_tip,
                sub_total=row['sub_total'],
            )
            amount_specs.append(amount_spec)
        chart_category_amount_spec = ChartCategoryAmountSpec(
            chart_val=chart_val,
            category_amount_specs=amount_specs,
        )
        chart_category_amount_specs.append(chart_category_amount_spec)
    charting_spec = ChartCategoryAmountSpecs(
        chart_field_name=chart_field_name,
        category_field_name=category_field_name,
        chart_category_amount_specs=chart_category_amount_specs,
        sort_orders=sort_orders,
        category_sort_order=category_sort_order,
        decimal_points=decimal_points,
    )
    return charting_spec

def get_by_chart_series_category_charting_spec(*, cur: ExtendedCursor, dbe_spec: DbeSpec, source_table_name: str,
        category_field_name: str, series_field_name: str, chart_field_name: str,
        sort_orders: SortOrderSpecs,
        category_sort_order: SortOrder = SortOrder.VALUE,
        series_sort_order: SortOrder = SortOrder.VALUE,
        chart_sort_order: SortOrder = SortOrder.VALUE,
        metric: ChartMetric = ChartMetric.FREQ, field_name: str | None = None,
        table_filter_sql: str | None = None, decimal_points: int = 3) -> ChartSeriesCategoryAmountSpecs:
    """
    Intermediate charting spec - close to the data
    """
    validate_metric_and_field_name(metric, field_name)
    ## prepare items
    field_name_quoted = dbe_spec.entity_quoter(field_name) if field_name else None
    category_field_name_quoted = dbe_spec.entity_quoter(category_field_name)
    series_field_name_quoted = dbe_spec.entity_quoter(series_field_name)
    chart_field_name_quoted = dbe_spec.entity_quoter(chart_field_name)
    source_table_name_quoted = dbe_spec.entity_quoter(source_table_name)
    AND_table_filter_sql = f"AND ({table_filter_sql})" if table_filter_sql else ''
    ## handle metric requirements
    if metric in (ChartMetric.FREQ, ChartMetric.PCT):
        agg_fields_clause = f"""\
        COUNT(*) AS
          freq,
            ((100.0 * COUNT(*))
            / (
              SELECT COUNT(*)
              FROM {source_table_name_quoted}
              WHERE {chart_field_name_quoted} = src.{chart_field_name_quoted}
              AND {series_field_name_quoted} = src.{series_field_name_quoted}
            )) AS
          category_pct
        """
        if metric == ChartMetric.FREQ:
            def get_amount_and_tool_tip(args_dict: dict) -> tuple[int, str]:
                returned_tool_tip = (f"{args_dict['category_val']}, {args_dict['series_val']}"
                    f"<br>{args_dict['freq']}"
                    f"<br>({round(args_dict['category_pct'], decimal_points)}%)")
                return int(args_dict['freq']), returned_tool_tip
        elif metric == ChartMetric.PCT:
            def get_amount_and_tool_tip(args_dict: dict) -> tuple[int, str]:
                returned_tool_tip = (f"{args_dict['category_val']}, {args_dict['series_val']}"
                    f"<br>{args_dict['freq']}"
                    f"<br>({round(args_dict['category_pct'], decimal_points)}%)")
                return int(args_dict['category_pct']), returned_tool_tip
        else:
            raise ValueError(f"Metric {metric} is not supported")
    elif metric == ChartMetric.AVG:
        agg_fields_clause = f"""\
        AVG({field_name_quoted}) AS
          average_value
        """
        def get_amount_and_tool_tip(args_dict: dict) -> tuple[float, str]:
            returned_tool_tip = (f"{args_dict['category_val']}, {args_dict['series_val']}"
                f"<br>{round(args_dict['avg'], decimal_points)}")
            return float(args_dict['avg']), returned_tool_tip
    elif metric == ChartMetric.SUM:
        agg_fields_clause = f"""\
        SUM({field_name_quoted}) AS
          summed_value
        """
        def get_amount_and_tool_tip(args_dict: dict) -> tuple[int, str]:
            returned_tool_tip = (
                f"{args_dict['category_val']}, {args_dict['series_val']}"
                f"<br>{round(args_dict['summed_value'], decimal_points)}")
            return int(args_dict['summed_value']), returned_tool_tip
    else:
        raise ValueError(f"Metric {metric} is not supported")
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
      sub_total,  -- needed for n_records even if not ChartMetric.FREQ
        {agg_fields_clause}
    FROM {source_table_name_quoted} AS src
    WHERE {chart_field_name_quoted} IS NOT NULL
    AND {series_field_name_quoted} IS NOT NULL
    AND {category_field_name_quoted} IS NOT NULL
    {AND_table_filter_sql}
    GROUP BY {chart_field_name_quoted}, {series_field_name_quoted}, {category_field_name_quoted}
    ORDER BY {chart_field_name_quoted}, {series_field_name_quoted}, {category_field_name_quoted}
    """
    ## get data
    cur.exe(sql)
    data = cur.fetchall()
    cols = [desc[0] for desc in cur.description]
    df = pd.DataFrame(data, columns=cols)
    chart_series_category_amount_specs = []
    orig_chart_vals = df['chart_val'].unique()
    sorted_chart_vals = to_sorted_values(orig_vals=orig_chart_vals,
        field_name=chart_field_name, sort_orders=sort_orders, sort_order=chart_sort_order)
    for chart_val in sorted_chart_vals:
        series_category_amount_specs = []
        orig_series_vals = df.loc[df['chart_val'] == chart_val, 'series_val'].unique()
        sorted_series_vals = to_sorted_values(orig_vals=orig_series_vals,
            field_name=series_field_name, sort_orders=sort_orders, sort_order=series_sort_order)
        for series_val in sorted_series_vals:
            amount_specs = []
            for _i, row in df.loc[(df['chart_val'] == chart_val) & (df['series_val'] == series_val)].iterrows():
                amount, tool_tip = get_amount_and_tool_tip(row.to_dict())
                amount_spec = CategoryItemAmountSpec(
                    category_val=row['category_val'],
                    amount=amount,
                    tool_tip=tool_tip,
                    sub_total=row['sub_total'],
                )
                amount_specs.append(amount_spec)
            series_category_amount_spec = SeriesCategoryAmountSpec(
                series_val=series_val,
                category_amount_specs=amount_specs,
            )
            series_category_amount_specs.append(series_category_amount_spec)
        chart_series_category_amount_spec = ChartSeriesCategoryAmountSpec(
            chart_val=chart_val,
            series_category_amount_specs=series_category_amount_specs,
        )
        chart_series_category_amount_specs.append(chart_series_category_amount_spec)
    data_spec = ChartSeriesCategoryAmountSpecs(
        chart_field_name=chart_field_name,
        series_field_name=series_field_name,
        category_field_name=category_field_name,
        chart_series_category_amount_specs=chart_series_category_amount_specs,
        sort_orders=sort_orders,
        category_sort_order=category_sort_order,
        decimal_points=decimal_points,
    )
    return data_spec
