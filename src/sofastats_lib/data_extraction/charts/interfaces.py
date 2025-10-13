## No project dependencies :-)
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

## Data Chart parts - multi-chart, chart, category, then series, containing data points
## The higher-level components are only needed by output e.g. ChartingSpec, ChartingSpecAxes, AreaChartingSpec,
## LineChartingSpec, and ChartingSpecNoAxes, so they are in output.charts.interfaces

## Not the categories now but the data per category e.g. 123
@dataclass(frozen=True)
class DataItem:
    """
    lbl: HTML label e.g. "Ubuntu<br>Linux" - ready for display in chart
    """
    amount: float
    lbl: str
    tooltip: str

@dataclass
class DataSeriesSpec:
    lbl: str | None
    data_items: Sequence[DataItem]

    def __post_init__(self):
        """
        Used in JS which often grabs bits separately.
        """
        self.amounts = []
        self.lbls = []
        self.tooltips = []
        for data_item in self.data_items:
            if data_item is not None:
                self.amounts.append(data_item.amount)
                self.lbls.append(data_item.lbl)
                self.tooltips.append(data_item.tooltip)
            else:
                self.amounts.append(0)
                self.lbls.append('')
                self.tooltips.append('')

## everything with categories i.e. all charts with frequencies + box plots
## The categories e.g. NZ (common across all individual charts and series within any charts)
@dataclass(frozen=True)
class CategorySpec:
    """
    lbl: HTML label e.g. "Ubuntu<br>Linux" - ready for display in chart
    """
    val: Any
    lbl: str

@dataclass
class IndivChartSpec:
    lbl: str | None
    data_series_specs: Sequence[DataSeriesSpec]
    n_records: int
