from collections.abc import Sequence
from dataclasses import dataclass

from sofastats_lib.stats_calc.interfaces import CorrelationCalcResult, RegressionResult, SpearmansResult

@dataclass(frozen=True)
class Coord:
    x: float
    y: float

@dataclass(frozen=True, kw_only=True)
class CorrelationResult:
    variable_a_label: str
    variable_b_label: str
    coords: Sequence[Coord]
    stats_result: CorrelationCalcResult
    regression_result: RegressionResult
    worked_result: SpearmansResult | None = None

    @property
    def xs(self):
        return [coord.x for coord in self.coords]

    @property
    def ys(self):
        return [coord.y for coord in self.coords]
