"""
Get all vals by group, combine, and get overall bin_spec (discard overall bin_freqs).
Then, using get_bin_freqs(vals, bin_spec), and the common bin_spec, get bin_freqs for each chart.
"""
from collections.abc import Sequence
from dataclasses import dataclass

import pandas as pd

from sofastats.conf.main import DbeSpec, SortOrder, SortOrderSpecs
from sofastats.data_extraction.db import ExtendedCursor
from sofastats.stats_calc.engine import get_normal_ys
from sofastats.stats_calc.histogram import get_bin_details_from_vals

@dataclass
class HistoIndivChartSpec:
    label: str | None
    n_records: int
    norm_y_vals: Sequence[float]
    y_vals: Sequence[int]

@dataclass(frozen=False)
class HistoValsSpec:
    field_name: str
    chart_field_name: str | None
    chart_name: str | None
    vals: Sequence[float]
    decimal_points: int = 3

    def __post_init__(self):
        bin_spec, bin_freqs = get_bin_details_from_vals(self.vals)
        self.bin_spec = bin_spec
        self.bin_freqs = bin_freqs

    def to_indiv_chart_specs(self) -> Sequence[HistoIndivChartSpec]:
        """
        Translate vals into all the bits and pieces required by each HistoIndivChartSpec
        using stats_calc.histogram
        """
        import numpy as np
        bin_starts = [start for start, end in self.bin_spec.bin_ranges]
        norm_y_vals = get_normal_ys(self.vals, np.array(bin_starts))
        sum_y_vals = sum(self.bin_freqs)
        sum_norm_y_vals = sum(norm_y_vals)
        norm_multiplier = float(sum_y_vals / sum_norm_y_vals)
        adjusted_norm_y_vals = [float(val) * norm_multiplier for val in norm_y_vals]
        label = f"{self.chart_field_name}: {self.chart_name}" if self.chart_field_name else ''
        indiv_chart_spec = HistoIndivChartSpec(
            label=label,
            n_records=len(self.vals),
            norm_y_vals=adjusted_norm_y_vals,
            y_vals=self.bin_freqs,
        )
        return [indiv_chart_spec, ]

    def to_bin_labels(self) -> list[str]:
        bin_labels = self.bin_spec.to_bin_labels(decimal_points=self.decimal_points)
        return bin_labels

    def to_x_axis_range(self) -> tuple[float, float]:
        bin_spec, _bin_freqs = get_bin_details_from_vals(self.vals)
        x_axis_min_val = bin_spec.lower_limit
        x_axis_max_val = bin_spec.upper_limit
        return x_axis_min_val, x_axis_max_val



def to_sorted_histo_chart_vals_specs(
        histo_chart_vals_specs: Sequence[HistoValsSpec],
        chart_field_name: str, sort_orders: SortOrderSpecs, chart_sort_order: SortOrder) -> list:
    if chart_sort_order == SortOrder.VALUE:
        def sort_me(histo_vals_spec):
            return histo_vals_spec.chart_name
        reverse = False
    elif chart_sort_order == SortOrder.CUSTOM:
        ## use supplied sort order
        try:
            values_in_order = sort_orders[chart_field_name]
        except KeyError:
            raise Exception(
                f"You wanted the values in variable '{chart_field_name}' to have a custom sort order "
                "but I couldn't find a sort order from what you supplied. "
                "Please fix the sort order details or use another approach to sorting.")
        value2order = {val: order for order, val in enumerate(values_in_order)}
        def sort_me(histo_vals_spec):
            histo_chart_val = histo_vals_spec.chart_name
            try:
                idx_for_ordered_position = value2order[histo_chart_val]
            except KeyError:
                raise Exception(
                    f"The custom sort order you supplied for values in variable '{chart_field_name}' "
                    f"didn't include value '{histo_chart_val}' so please fix that and try again.")
            return idx_for_ordered_position
    else:
        raise Exception(
            f"Unexpected chart_sort_order ({chart_sort_order})"
            "\nDECREASING is for ordering by frequency which makes no sense when multi-series charts."
        )
    sorted_histo_chart_vals_specs = sorted(histo_chart_vals_specs, key=sort_me)
    return sorted_histo_chart_vals_specs


@dataclass(frozen=False)
class HistoValsSpecs:
    field_name: str
    chart_field_name: str
    sort_orders: SortOrderSpecs
    chart_sort_order: SortOrder
    chart_vals_specs: Sequence[HistoValsSpec]
    decimal_points: int = 3

    def __post_init__(self):
        vals = []
        for chart_vals_spec in self.chart_vals_specs:
            vals.extend(chart_vals_spec.vals)
        self.vals = vals
        bin_spec, bin_freqs = get_bin_details_from_vals(vals)
        self.bin_spec = bin_spec

    def to_indiv_chart_specs(self) -> Sequence[HistoIndivChartSpec]:
        indiv_chart_specs = []
        sorted_histo_chart_vals_specs = to_sorted_histo_chart_vals_specs(
            histo_chart_vals_specs=self.chart_vals_specs, chart_field_name=self.chart_field_name,
            sort_orders=self.sort_orders, chart_sort_order=self.chart_sort_order,
        )
        for chart_vals_spec in sorted_histo_chart_vals_specs:
            indiv_chart_specs.extend(chart_vals_spec.to_indiv_chart_specs())
        return indiv_chart_specs

    def to_bin_labels(self) -> list[str]:
        bin_labels = self.bin_spec.to_bin_labels(decimal_points=self.decimal_points)
        return bin_labels

    def to_x_axis_range(self) -> tuple[float, float]:
        bin_spec, _bin_freqs = get_bin_details_from_vals(self.vals)
        x_axis_min_val = bin_spec.lower_limit
        x_axis_max_val = bin_spec.upper_limit
        return x_axis_min_val, x_axis_max_val

def get_by_vals_charting_spec(*, cur: ExtendedCursor, dbe_spec: DbeSpec, source_table_name: str,
        field_name: str, table_filter_sql: str | None = None, decimal_points: int = 3) -> HistoValsSpec:
    ## prepare items
    field_name_quoted = dbe_spec.entity_quoter(field_name)
    source_table_name_quoted = dbe_spec.entity_quoter(source_table_name)
    AND_table_filter_sql = f"AND ({table_filter_sql})" if table_filter_sql else ''
    ## assemble SQL
    sql = f"""\
    SELECT
        {field_name_quoted} AS y
    FROM {source_table_name_quoted}
    WHERE {field_name_quoted} IS NOT NULL
    {AND_table_filter_sql}
    """
    ## get data
    cur.exe(sql)
    data = cur.fetchall()
    vals = [row[0] for row in data]
    ## build result
    data_spec = HistoValsSpec(
        field_name=field_name,
        chart_field_name=None,
        chart_name=None,
        vals=vals,
        decimal_points=decimal_points,
    )
    return data_spec

def get_by_chart_charting_spec(*, cur: ExtendedCursor, dbe_spec: DbeSpec, source_table_name: str,
        field_name: str,
        chart_field_name: str,
        sort_orders: SortOrderSpecs,
        chart_sort_order: SortOrder,
        table_filter_sql: str | None = None, decimal_points: int = 3) -> HistoValsSpecs:
    ## prepare items
    field_name_quoted = dbe_spec.entity_quoter(field_name)
    chart_field_name_quoted = dbe_spec.entity_quoter(chart_field_name)
    source_table_name_quoted = dbe_spec.entity_quoter(source_table_name)
    AND_table_filter_sql = f"AND ({table_filter_sql})" if table_filter_sql else ''
    ## assemble SQL
    sql = f"""\
    SELECT
      {chart_field_name_quoted},
        {field_name_quoted} AS
      y
    FROM {source_table_name_quoted}
    WHERE {chart_field_name_quoted} IS NOT NULL
    AND {field_name_quoted} IS NOT NULL
    {AND_table_filter_sql}
    """
    ## get data
    cur.exe(sql)
    data = cur.fetchall()
    cols = ['chart_val', 'val']
    df = pd.DataFrame(data, columns=cols)
    chart_vals_specs = []
    chart_vals = df['chart_val'].unique()
    for chart_val in chart_vals:
        df_vals = df.loc[df['chart_val'] == chart_val, ['val']]
        vals = list(df_vals['val'])
        vals_spec = HistoValsSpec(
            field_name=field_name,  ## needed when single chart but redundant / repeated here in multi-chart context
            chart_field_name=chart_field_name,
            chart_name=chart_val,
            vals=vals,
        )
        chart_vals_specs.append(vals_spec)
    data_spec = HistoValsSpecs(
        field_name=field_name,
        chart_field_name=chart_field_name,
        sort_orders=sort_orders,
        chart_sort_order=chart_sort_order,
        chart_vals_specs=chart_vals_specs,
        decimal_points=decimal_points,
    )
    return data_spec
