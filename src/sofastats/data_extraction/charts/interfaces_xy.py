from collections.abc import Sequence
from dataclasses import dataclass

import pandas as pd

from sofastats.conf.main import DbeSpec
from sofastats.data_extraction.charts.scatterplot import ScatterDataSeriesSpec, ScatterIndivChartSpec
from sofastats.data_extraction.db import ExtendedCursor

@dataclass(frozen=True)
class XYSpecs:
    x_fld_lbl: str
    y_fld_lbl: str
    xys: Sequence[tuple[float, float]]

    def to_indiv_chart_specs(self) -> Sequence[ScatterIndivChartSpec]:
        data_series_spec = ScatterDataSeriesSpec(
            lbl=None,
            xy_pairs=self.xys,
        )
        indiv_chart_spec = ScatterIndivChartSpec(
            data_series_specs=[data_series_spec],
            lbl=None,
        )
        indiv_chart_specs = [indiv_chart_spec, ]
        return indiv_chart_specs

@dataclass(frozen=True)
class SeriesXYSpec:
    lbl: str
    xys: Sequence[tuple[float, float]]

@dataclass(frozen=True)
class SeriesXYSpecs:
    series_fld_lbl: str
    x_fld_lbl: str
    y_fld_lbl: str
    series_xy_specs: Sequence[SeriesXYSpec]

    def to_indiv_chart_specs(self) -> Sequence[ScatterIndivChartSpec]:
        data_series_specs = []
        for series_xy_spec in self.series_xy_specs:
            data_series_spec = ScatterDataSeriesSpec(
                lbl=series_xy_spec.lbl,
                xy_pairs=series_xy_spec.xys,
            )
            data_series_specs.append(data_series_spec)
        indiv_chart_spec = ScatterIndivChartSpec(
            data_series_specs=data_series_specs,
            lbl=None,
        )
        indiv_chart_specs = [indiv_chart_spec, ]
        return indiv_chart_specs\

@dataclass(frozen=True)
class ChartXYSpec:
    lbl: str
    xys: Sequence[tuple[float, float]]

@dataclass(frozen=True)
class ChartXYSpecs:
    x_fld_lbl: str
    y_fld_lbl: str
    charts_xy_specs: Sequence[ChartXYSpec]

    def to_indiv_chart_specs(self) -> Sequence[ScatterIndivChartSpec]:
        indiv_chart_specs = []
        for charts_xy_spec in self.charts_xy_specs:
            data_series_spec = ScatterDataSeriesSpec(
                lbl=None,
                xy_pairs=charts_xy_spec.xys,
            )
            indiv_chart_spec = ScatterIndivChartSpec(
                data_series_specs=[data_series_spec, ],
                lbl=charts_xy_spec.lbl,
            )
            indiv_chart_specs.append(indiv_chart_spec)
        return indiv_chart_specs

@dataclass(frozen=True)
class ChartSeriesXYSpec:
    lbl: str
    series_xy_specs: Sequence[SeriesXYSpec]

@dataclass(frozen=True)
class ChartSeriesXYSpecs:
    series_fld_lbl: str
    x_fld_lbl: str
    y_fld_lbl: str
    chart_series_xy_specs: Sequence[ChartSeriesXYSpec]

    def to_indiv_chart_specs(self) -> Sequence[ScatterIndivChartSpec]:
        indiv_chart_specs = []
        for chart_series_xy_spec in self.chart_series_xy_specs:
            data_series_specs = []
            for series_xy_spec in chart_series_xy_spec.series_xy_specs:
                data_series_spec = ScatterDataSeriesSpec(
                    lbl=series_xy_spec.lbl,
                    xy_pairs=series_xy_spec.xys,
                )
                data_series_specs.append(data_series_spec)
            indiv_chart_spec = ScatterIndivChartSpec(
                data_series_specs=data_series_specs,
                lbl=chart_series_xy_spec.lbl,
            )
            indiv_chart_specs.append(indiv_chart_spec)
        return indiv_chart_specs

def get_by_xy_charting_spec(*, cur: ExtendedCursor, dbe_spec: DbeSpec, src_tbl_name: str,
        x_fld_name: str, x_fld_lbl: str,
        y_fld_name: str, y_fld_lbl: str,
        tbl_filt_clause: str | None = None) -> XYSpecs:
    ## prepare items
    and_tbl_filt_clause = f"AND ({tbl_filt_clause})" if tbl_filt_clause else ''
    x_fld_name_quoted = dbe_spec.entity_quoter(x_fld_name)
    y_fld_name_quoted = dbe_spec.entity_quoter(y_fld_name)
    src_tbl_name_quoted = dbe_spec.entity_quoter(src_tbl_name)
    ## assemble SQL
    sql = f"""\
    SELECT
        {x_fld_name_quoted} AS x,
        {y_fld_name_quoted} AS y
    FROM {src_tbl_name_quoted}
    WHERE {x_fld_name_quoted} IS NOT NULL
    AND {y_fld_name_quoted} IS NOT NULL
    {and_tbl_filt_clause}
    """
    ## get data
    cur.exe(sql)
    data = cur.fetchall()
    ## build result
    data_spec = XYSpecs(
        x_fld_lbl=x_fld_lbl,
        y_fld_lbl=y_fld_lbl,
        xys=data,
    )
    return data_spec

def get_by_series_xy_charting_spec(*, cur: ExtendedCursor, dbe_spec: DbeSpec, src_tbl_name: str,
        series_fld_name: str, series_fld_lbl: str,
        x_fld_name: str, x_fld_lbl: str,
        y_fld_name: str, y_fld_lbl: str,
        series_vals2lbls: dict | None,
        tbl_filt_clause: str | None = None) -> SeriesXYSpecs:
    x_fld_name_quoted = dbe_spec.entity_quoter(x_fld_name)
    y_fld_name_quoted = dbe_spec.entity_quoter(y_fld_name)
    series_fld_name_quoted = dbe_spec.entity_quoter(series_fld_name)
    src_tbl_name_quoted = dbe_spec.entity_quoter(src_tbl_name)
    ## prepare items
    series_vals2lbls = {} if series_vals2lbls is None else series_vals2lbls
    and_tbl_filt_clause = f"AND ({tbl_filt_clause})" if tbl_filt_clause else ''
    ## assemble SQL
    sql = f"""\
    SELECT
        {series_fld_name_quoted} AS series_val,
        {x_fld_name_quoted} AS x,
        {y_fld_name_quoted} AS y
    FROM {src_tbl_name_quoted}
    WHERE {x_fld_name_quoted} IS NOT NULL
    AND {y_fld_name_quoted} IS NOT NULL
    {and_tbl_filt_clause}
    """
    ## get data
    cur.exe(sql)
    data = cur.fetchall()
    cols = ['series_val', 'x', 'y']
    df = pd.DataFrame(data, columns=cols)
    ## build result
    series_xy_specs = []
    for series_val in df['series_val'].unique():
        xys = df.loc[df['series_val'] == series_val, ['x', 'y']].to_records(index=False).tolist()
        series_xy_spec = SeriesXYSpec(
            lbl=series_vals2lbls.get(series_val, series_val),
            xys=xys,
        )
        series_xy_specs.append(series_xy_spec)
    data_spec = SeriesXYSpecs(
        series_fld_lbl=series_fld_lbl,
        x_fld_lbl=x_fld_lbl,
        y_fld_lbl=y_fld_lbl,
        series_xy_specs=series_xy_specs,
    )
    return data_spec

def get_by_chart_xy_charting_spec(*, cur: ExtendedCursor, dbe_spec: DbeSpec, src_tbl_name: str,
        chart_fld_name: str, chart_fld_lbl: str,
        x_fld_name: str, x_fld_lbl: str,
        y_fld_name: str, y_fld_lbl: str,
        chart_vals2lbls: dict | None,
        tbl_filt_clause: str | None = None) -> ChartXYSpecs:
    ## prepare items
    chart_vals2lbls = {} if chart_vals2lbls is None else chart_vals2lbls
    and_tbl_filt_clause = f"AND ({tbl_filt_clause})" if tbl_filt_clause else ''
    chart_fld_name_quoted = dbe_spec.entity_quoter(chart_fld_name)
    x_fld_name_quoted = dbe_spec.entity_quoter(x_fld_name)
    y_fld_name_quoted = dbe_spec.entity_quoter(y_fld_name)
    src_tbl_name_quoted = dbe_spec.entity_quoter(src_tbl_name)
    ## assemble SQL
    sql = f"""\
    SELECT
        {chart_fld_name_quoted} AS charts_val,
        {x_fld_name_quoted} AS x,
        {y_fld_name_quoted} AS y
    FROM {src_tbl_name_quoted}
    WHERE {x_fld_name_quoted} IS NOT NULL
    AND {y_fld_name_quoted} IS NOT NULL
    {and_tbl_filt_clause}
    """
    ## get data
    cur.exe(sql)
    data = cur.fetchall()
    cols = ['charts_val', 'x', 'y']
    df = pd.DataFrame(data, columns=cols)
    ## build result
    charts_xy_specs = []
    for chart_val in df['charts_val'].unique():
        xys = df.loc[df['charts_val'] == chart_val, ['x', 'y']].to_records(index=False).tolist()
        chart_xy_spec = ChartXYSpec(
            lbl=f"{chart_fld_lbl}: {chart_vals2lbls.get(chart_val, chart_val)}",
            xys=xys,
        )
        charts_xy_specs.append(chart_xy_spec)
    data_spec = ChartXYSpecs(
        x_fld_lbl=x_fld_lbl,
        y_fld_lbl=y_fld_lbl,
        charts_xy_specs=charts_xy_specs,
    )
    return data_spec

def get_by_chart_series_xy_charting_spec(*, cur: ExtendedCursor, dbe_spec: DbeSpec, src_tbl_name: str,
        chart_fld_name: str, chart_fld_lbl: str,
        series_fld_name: str, series_fld_lbl: str,
        x_fld_name: str, x_fld_lbl: str,
        y_fld_name: str, y_fld_lbl: str,
        chart_vals2lbls: dict | None,
        series_vals2lbls: dict | None,
        tbl_filt_clause: str | None = None) -> ChartSeriesXYSpecs:
    ## prepare items
    chart_vals2lbls = {} if chart_vals2lbls is None else chart_vals2lbls
    series_vals2lbls = {} if series_vals2lbls is None else series_vals2lbls
    and_tbl_filt_clause = f"AND ({tbl_filt_clause})" if tbl_filt_clause else ''
    chart_fld_name_quoted = dbe_spec.entity_quoter(chart_fld_name)
    series_fld_name_quoted = dbe_spec.entity_quoter(series_fld_name)
    x_fld_name_quoted = dbe_spec.entity_quoter(x_fld_name)
    y_fld_name_quoted = dbe_spec.entity_quoter(y_fld_name)
    src_tbl_name_quoted = dbe_spec.entity_quoter(src_tbl_name)
    ## assemble SQL
    sql = f"""\
    SELECT
        {chart_fld_name_quoted} AS chart_val,
        {series_fld_name_quoted} AS series_val,
        {x_fld_name_quoted} AS x,
        {y_fld_name_quoted} AS y
    FROM {src_tbl_name_quoted}
    WHERE {x_fld_name_quoted} IS NOT NULL
    AND {y_fld_name_quoted} IS NOT NULL
    {and_tbl_filt_clause}
    """
    ## get data
    cur.exe(sql)
    data = cur.fetchall()
    cols = ['chart_val', 'series_val', 'x', 'y']
    df = pd.DataFrame(data, columns=cols)
    ## build result
    chart_series_xy_specs = []
    for chart_val in df['chart_val'].unique():
        series_xy_specs = []
        for series_val in df.loc[df['chart_val'] == chart_val, 'series_val'].unique():
            xys = df.loc[
                (df['chart_val'] == chart_val) & (df['series_val'] == series_val),
                ['x', 'y']
            ].to_records(index=False).tolist()
            series_xy_spec = SeriesXYSpec(
                lbl=series_vals2lbls.get(series_val, series_val),
                xys=xys,
            )
            series_xy_specs.append(series_xy_spec)
        chart_series_xy_spec = ChartSeriesXYSpec(
            lbl=f"{chart_fld_lbl}: {chart_vals2lbls.get(chart_val, chart_val)}",
            series_xy_specs=series_xy_specs,
        )
        chart_series_xy_specs.append(chart_series_xy_spec)
    data_spec = ChartSeriesXYSpecs(
        series_fld_lbl=series_fld_lbl,
        x_fld_lbl=x_fld_lbl,
        y_fld_lbl=y_fld_lbl,
        chart_series_xy_specs=chart_series_xy_specs,
    )
    return data_spec
