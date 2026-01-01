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
    label: HTML label e.g. "Ubuntu<br>Linux" - ready for display in chart
    """
    amount: float
    label: str
    tooltip: str

@dataclass
class DataSeriesSpec:
    label: str | None
    data_items: Sequence[DataItem]

    def __post_init__(self):
        """
        Used in JS which often grabs bits separately.
        """
        self.amounts = []
        self.labels = []
        self.tooltips = []
        for data_item in self.data_items:
            if data_item is not None:
                self.amounts.append(data_item.amount)
                self.labels.append(data_item.label)
                self.tooltips.append(data_item.tooltip)
            else:
                self.amounts.append(0)
                self.labels.append('')
                self.tooltips.append('')

## everything with categories i.e. all charts with frequencies + box plots
## The categories e.g. NZ (common across all individual charts and series within any charts)
@dataclass(frozen=True)
class CategorySpec:
    """
    label: HTML label e.g. "Ubuntu<br>Linux" - ready for display in chart
    """
    val: Any
    label: str

@dataclass
class IndivChartSpec:
    label: str | None
    data_series_specs: Sequence[DataSeriesSpec]
    n_records: int
