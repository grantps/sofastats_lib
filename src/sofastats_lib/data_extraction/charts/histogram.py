"""
Get all vals by group, combine, and get overall bin_spec (discard overall bin_freqs).
Then, using get_bin_freqs(vals, bin_spec), and the common bin_spec, get bin_freqs for each chart.
"""
from collections.abc import Sequence
from dataclasses import dataclass

import pandas as pd

from sofastats_lib.conf.main import DbeSpec
from sofastats_lib.data_extraction.db import ExtendedCursor, get_dbe_spec
from sofastats_lib.stats_calc.engine import get_normal_ys
from sofastats_lib.stats_calc.histogram import get_bin_details_from_vals

@dataclass
class HistoIndivChartSpec:
    lbl: str | None
    n_records: int
    norm_y_vals: Sequence[float]
    y_vals: Sequence[int]

@dataclass(frozen=False)
class HistoValsSpec:
    chart_lbl: str | None
    fld_lbl: str
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
            lbl=self.chart_lbl,
            n_records=len(self.vals),
            norm_y_vals=adjusted_norm_y_vals,
            y_vals=self.bin_freqs,
        )
        return [indiv_chart_spec, ]

    def to_bin_lbls(self, *, dp: int = 3) -> list[str]:
        bin_lbls = self.bin_spec.to_bin_lbls(dp=dp)
        return bin_lbls

    def to_x_axis_range(self) -> tuple[float, float]:
        bin_spec, _bin_freqs = get_bin_details_from_vals(self.vals)
        x_axis_min_val = bin_spec.lower_limit
        x_axis_max_val = bin_spec.upper_limit
        return x_axis_min_val, x_axis_max_val

@dataclass(frozen=False)
class HistoValsSpecs:
    chart_fld_lbl: str
    fld_lbl: str
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

    def to_bin_lbls(self, *, dp: int = 3) -> list[str]:
        bin_lbls = self.bin_spec.to_bin_lbls(dp=dp)
        return bin_lbls

    def to_x_axis_range(self) -> tuple[float, float]:
        bin_spec, _bin_freqs = get_bin_details_from_vals(self.vals)
        x_axis_min_val = bin_spec.lower_limit
        x_axis_max_val = bin_spec.upper_limit
        return x_axis_min_val, x_axis_max_val

def get_by_vals_charting_spec(*, cur: ExtendedCursor, dbe_spec: DbeSpec, src_tbl_name: str,
        fld_name: str, fld_lbl: str,
        tbl_filt_clause: str | None = None) -> HistoValsSpec:
    ## prepare items
    and_tbl_filt_clause = f"AND ({tbl_filt_clause})" if tbl_filt_clause else ''
    fld_name_quoted = dbe_spec.entity_quoter(fld_name)
    src_tbl_name_quoted = dbe_spec.entity_quoter(src_tbl_name)
    ## assemble SQL
    sql = f"""\
    SELECT
        {fld_name_quoted} AS y
    FROM {src_tbl_name_quoted}
    WHERE {fld_name_quoted} IS NOT NULL
    {and_tbl_filt_clause}
    """
    ## get data
    cur.exe(sql)
    data = cur.fetchall()
    vals = [row[0] for row in data]
    ## build result
    data_spec = HistoValsSpec(
        chart_lbl=None,
        fld_lbl=fld_lbl,
        vals=vals,
    )
    return data_spec

def get_by_chart_charting_spec(*, cur: ExtendedCursor, dbe_spec: DbeSpec, src_tbl_name: str,
        chart_fld_name: str, chart_fld_lbl: str,
        fld_name: str, fld_lbl: str,
        chart_vals2lbls: dict | None,
        tbl_filt_clause: str | None = None) -> HistoValsSpecs:
    ## prepare items
    and_tbl_filt_clause = f"AND ({tbl_filt_clause})" if tbl_filt_clause else ''
    chart_fld_name_quoted = dbe_spec.entity_quoter(chart_fld_name)
    fld_name_quoted = dbe_spec.entity_quoter(fld_name)
    src_tbl_name_quoted = dbe_spec.entity_quoter(src_tbl_name)
    ## assemble SQL
    sql = f"""\
    SELECT
      {chart_fld_name_quoted},
        {fld_name_quoted} AS
      y
    FROM {src_tbl_name_quoted}
    WHERE {chart_fld_name_quoted} IS NOT NULL
    AND {fld_name_quoted} IS NOT NULL
    {and_tbl_filt_clause}
    """
    ## get data
    cur.exe(sql)
    data = cur.fetchall()
    cols = ['chart_val', 'val']
    df = pd.DataFrame(data, columns=cols)
    chart_vals_specs = []
    for chart_val in df['chart_val'].unique():
        chart_lbl = chart_vals2lbls.get(chart_val, chart_val)
        df_vals = df.loc[df['chart_val'] == chart_val, ['val']]
        vals = list(df_vals['val'])
        vals_spec = HistoValsSpec(
            chart_lbl=chart_lbl,
            fld_lbl=fld_lbl,  ## needed when single chart but redundant / repeated here in multi-chart context
            vals=vals,
        )
        chart_vals_specs.append(vals_spec)
    data_spec = HistoValsSpecs(
        chart_fld_lbl=chart_fld_lbl,
        fld_lbl=fld_lbl,
        chart_vals_specs=chart_vals_specs,
    )
    return data_spec
