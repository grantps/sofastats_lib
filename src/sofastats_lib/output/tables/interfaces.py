## No project dependencies except conf.main :-)
from collections.abc import Collection
from dataclasses import dataclass
from enum import StrEnum
from typing import Self

from sofastats_lib.conf.main import SortOrder

BLANK = '__blank__'
TOTAL = 'TOTAL'

class Metric(StrEnum):
    FREQ = 'Freq'
    ROW_PCT = 'Row %'
    COL_PCT = 'Col %'

PCT_METRICS = [Metric.ROW_PCT, Metric.COL_PCT]

class PctType(StrEnum):
    ROW_PCT = 'Row %'
    COL_PCT = 'Col %'

@dataclass(frozen=False)
class DimSpec:
    variable: str
    has_total: bool = False
    is_col: bool = False
    pct_metrics: Collection[Metric] | None = None
    sort_order: SortOrder | str = SortOrder.VALUE
    child: Self | None = None

    @property
    def descendant_vars(self) -> list[str]:
        """
        All variables under, but not including, this Dim.
        Note - only includes chains, not trees, as a deliberate design choice to avoid excessively complicated tables.
        Tables are for computers to make, but for humans to read and understand :-).
        """
        dim_vars = []
        if self.child:
            dim_vars.append(self.child.variable)
            dim_vars.extend(self.child.descendant_vars)
        return dim_vars

    @property
    def self_and_descendants(self) -> list[Self]:
        """
        All Dims under, and including, this Dim.
        """
        dims = [self, ]
        if self.child:
            dims.extend(self.child.self_and_descendants)
        return dims

    @property
    def self_and_descendant_vars(self) -> list[str]:
        return [dim.variable for dim in self.self_and_descendants]

    @property
    def self_and_descendant_totalled_vars(self) -> list[str]:
        """
        All variables under, and including, this Dim that are totalled (if any).
        """
        return [dim.variable for dim in self.self_and_descendants if dim.has_total]

    @property
    def self_or_descendant_pct_metrics(self) -> Collection[Metric] | None:
        if self.pct_metrics:
            return self.pct_metrics
        elif self.child:
            return self.child.self_or_descendant_pct_metrics
        else:
            return None

    def __post_init__(self):
        if self.pct_metrics:
            if self.child:
                raise ValueError(f"Metrics are only for terminal dimension specs e.g. a > b > c (can have metrics)")
            if not self.is_col:
                raise ValueError(f"Metrics are only for terminal column specs, yet this is a row spec")
        if self.child:
            if not self.is_col == self.child.is_col:
                raise ValueError(f"This dim has a child that is inconsistent e.g. a col parent having a row child")
        if self.variable in self.descendant_vars:
            raise ValueError("Variables can't be repeated in the same dimension spec "
                f"e.g. Car > Country > Car. Variable {self.variable}")


@dataclass(frozen=False)
class Row(DimSpec):
    is_col = False


@dataclass(frozen=False)
class Column(DimSpec):
    is_col = True
