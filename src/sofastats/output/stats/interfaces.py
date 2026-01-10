from abc import abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Type

from sofastats.output.interfaces import CommonDesign
from sofastats.stats_calc.interfaces import CorrelationCalcResult, RegressionResult, SpearmansResult, StatsResult

class Sausage:
    """
    Sausage!!!
    """
    pass

class CommonStatsDesign(CommonDesign):
    """
    Output dataclasses for statistical tests (e.g. MannWhitneyUDesign) inherit from CommonStatsDesign.
    """

    @abstractmethod
    def to_result(self) -> Type[StatsResult]:
        """
        Return a dataclass with results as attributes
        """
        pass

@dataclass(frozen=True)
class Coord:
    x: float
    y: float

@dataclass(frozen=True, kw_only=True)
class CorrelationResult:
    variable_a_name: str
    variable_b_name: str
    coords: Sequence[Coord]
    stats_result: CorrelationCalcResult
    regression_result: RegressionResult
    worked_result: SpearmansResult | None = None
    decimal_points: int = 3

    @property
    def xs(self):
        return [coord.x for coord in self.coords]

    @property
    def ys(self):
        return [coord.y for coord in self.coords]
