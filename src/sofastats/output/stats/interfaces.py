from abc import abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Type

from sofastats.output.interfaces import CommonDesign
from sofastats.stats_calc.interfaces import CorrelationCalcResult, RegressionResult, SpearmansResult, StatsResult


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


class CommonStatsDesignWithoutSortAttributes(CommonStatsDesign):
    """
    Output dataclasses for statistical tests (e.g. MannWhitneyUDesign) inherit from CommonStatsDesign.
    """

    def __post_init__(self):
        """
        There is no sorting for stats output other than Chi Square Observed vs Expected Tables.
        We should prevent the user from setting these attributes to stop them making the false assumption that these
        sort settings will alter anything when they won't. Affected attributes: sort_orders, sort_orders_yaml_file_path
        """
        super().__post_init__()
        if self.sort_orders:
            raise AttributeError("sort_orders should not be set for Statistical Tests")
        if self.sort_orders_yaml_file_path:
            raise AttributeError("sort_orders_yaml_file_path should not be set for Statistical Tests")

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
