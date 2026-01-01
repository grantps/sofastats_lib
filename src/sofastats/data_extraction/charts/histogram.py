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
    chart_name: str | None
    vals: Sequence[float]

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
        indiv_chart_spec = HistoIndivChartSpec(
            label=self.chart_name,
            n_records=len(self.vals),
            norm_y_vals=adjusted_norm_y_vals,
            y_vals=self.bin_freqs,
        )
        return [indiv_chart_spec, ]

    def to_bin_labels(self, *, dp: int = 3) -> list[str]:
        bin_labels = self.bin_spec.to_bin_labels(dp=dp)
        return bin_labels

    def to_x_axis_range(self) -> tuple[float, float]:
        bin_spec, _bin_freqs = get_bin_details_from_vals(self.vals)
        x_axis_min_val = bin_spec.lower_limit
        x_axis_max_val = bin_spec.upper_limit
        return x_axis_min_val, x_axis_max_val

@dataclass(frozen=False)
class HistoValsSpecs:
    field_name: str
    chart_field_name: str
    chart_vals_specs: Sequence[HistoValsSpec]

    def __post_init__(self):
        vals = []
        for chart_vals_spec in self.chart_vals_specs:
            vals.extend(chart_vals_spec.vals)
        self.vals = vals
        bin_spec, bin_freqs = get_bin_details_from_vals(vals)
        self.bin_spec = bin_spec

    def to_indiv_chart_specs(self) -> Sequence[HistoIndivChartSpec]:
        indiv_chart_specs = []
        for chart_vals_spec in self.chart_vals_specs:
            indiv_chart_specs.extend(chart_vals_spec.to_indiv_chart_specs())
        return indiv_chart_specs

    def to_bin_labels(self, *, dp: int = 3) -> list[str]:
        bin_labels = self.bin_spec.to_bin_labels(dp=dp)
        return bin_labels

    def to_x_axis_range(self) -> tuple[float, float]:
        bin_spec, _bin_freqs = get_bin_details_from_vals(self.vals)
        x_axis_min_val = bin_spec.lower_limit
        x_axis_max_val = bin_spec.upper_limit
        return x_axis_min_val, x_axis_max_val

def get_by_vals_charting_spec(*, cur: ExtendedCursor, dbe_spec: DbeSpec, src_tbl_name: str,
        field_name: str, tbl_filt_clause: str | None = None) -> HistoValsSpec:
    ## prepare items
    and_tbl_filt_clause = f"AND ({tbl_filt_clause})" if tbl_filt_clause else ''
    field_name_quoted = dbe_spec.entity_quoter(field_name)
    src_tbl_name_quoted = dbe_spec.entity_quoter(src_tbl_name)
    ## assemble SQL
    sql = f"""\
    SELECT
        {field_name_quoted} AS y
    FROM {src_tbl_name_quoted}
    WHERE {field_name_quoted} IS NOT NULL
    {and_tbl_filt_clause}
    """
    ## get data
    cur.exe(sql)
    data = cur.fetchall()
    vals = [row[0] for row in data]
    ## build result
    data_spec = HistoValsSpec(
        field_name=field_name,
        chart_name=None,
        vals=vals,
    )
    return data_spec

def get_by_chart_charting_spec(*, cur: ExtendedCursor, dbe_spec: DbeSpec, src_tbl_name: str,
        field_name: str,
        chart_field_name: str,
        sort_orders: SortOrderSpecs,
        chart_sort_order: SortOrder,
        tbl_filt_clause: str | None = None) -> HistoValsSpecs:
    ## prepare items
    and_tbl_filt_clause = f"AND ({tbl_filt_clause})" if tbl_filt_clause else ''
    field_name_quoted = dbe_spec.entity_quoter(field_name)
    chart_field_name_quoted = dbe_spec.entity_quoter(chart_field_name)
    src_tbl_name_quoted = dbe_spec.entity_quoter(src_tbl_name)
    ## assemble SQL
    sql = f"""\
    SELECT
      {chart_field_name_quoted},
        {field_name_quoted} AS
      y
    FROM {src_tbl_name_quoted}
    WHERE {chart_field_name_quoted} IS NOT NULL
    AND {field_name_quoted} IS NOT NULL
    {and_tbl_filt_clause}
    """
    ## get data
    cur.exe(sql)
    data = cur.fetchall()
    cols = ['chart_val', 'val']
    df = pd.DataFrame(data, columns=cols)
    chart_vals_specs = []
    for chart_val in df['chart_val'].unique():
        df_vals = df.loc[df['chart_val'] == chart_val, ['val']]
        vals = list(df_vals['val'])
        vals_spec = HistoValsSpec(
            field_name=field_name,  ## needed when single chart but redundant / repeated here in multi-chart context
            chart_name=chart_val,
            vals=vals,
        )
        chart_vals_specs.append(vals_spec)
    data_spec = HistoValsSpecs(
        field_name=field_name,
        chart_field_name=chart_field_name,
        chart_vals_specs=chart_vals_specs,
    )
    return data_spec
