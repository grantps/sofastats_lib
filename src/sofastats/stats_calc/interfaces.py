"""
Depends on stats_calc and utils which are lower level - so no problematic project dependencies :-)

Some interfaces are extended beyond those required for the original stats.py function results.
"""
from collections.abc import Sequence
from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum
from statistics import median
from textwrap import dedent
from typing import Literal

from sofastats.stats_calc.box_plot import get_bottom_whisker, get_top_whisker
from sofastats.stats_calc.histogram import BinSpec  ## noqa - so available for import from here as the one-stop shop for stats interfaces
from sofastats.utils.maths import nice_number_if_possible
from sofastats.utils.stats import get_quartiles

## samples

@dataclass(frozen=True, kw_only=True)
class NumericSampleSpec:
    label: str
    n: int
    mean: float
    median: float
    std_dev: float
    sample_min: float
    sample_max: float
    ci95: tuple[float, float] | None = None

    def __str__(self):
        return dedent(f"""\
        Group Label: {self.label}
        N Values: {self.n:,}
        Mean Value: {self.mean:,}
        Standard Deviation: {self.std_dev:,}
        Minimum Value: {self.sample_min:,}
        Maximum Value: {self.sample_max:,}
        95% Confidence Interval: {self.ci95}
        """)

@dataclass(frozen=True, kw_only=True)
class NumericSampleSpecExt(NumericSampleSpec):
    kurtosis: float | str
    skew: float | str
    normality_test_p: float | str
    vals: Sequence[float]

    def __str__(self):
        return str(super().__str__()) + dedent(f"""\
        Kurtosis: {self.kurtosis:,}
        Skew: {self.skew:,}
        Normality Test p: {self.normality_test_p}
        """)

@dataclass(frozen=True)
class NumericParametricSampleSpecFormatted:
    """
    Just the fields needed for tabular display as output.
    Usually formatted with decimal places and p in a helpful string already.
    Maybe could be generated from a dataclass with the raw values including numbers before converted into strings
    """
    label: str
    n: str
    mean: str
    ci95: str
    std_dev: str
    sample_min: str
    sample_max: str
    kurtosis: str | None = None
    skew: str | None = None
    p: str | None = None

@dataclass(frozen=True)
class NumericNonParametricSampleSpecFormatted:
    """
    Just the fields needed for tabular display as output.
    Usually formatted with decimal places.
    """
    label: str
    n: str
    median: str
    sample_min: str
    sample_max: str
    avg_rank: str | None = None  ## needed by Mann-Whitney U

@dataclass(frozen=True)
class Sample:
    """
    Sample including label.
    To refer to the vals of a sample call them "sample_vals" not "sample" to prevent confusion.
    "sample" must always mean an object with both label and vals.
    If there are multiple sample_vals call it "samples_vals" not "samples".
    "samples" should only ever refer to a sequence of Sample objects.
    Sample spec refers primarily to metadata about sample values e.g. min, max, mean.
    A "vals" attribute is included.
    """
    label: str
    vals: list[float]  ## np.ravel, shape etc. work on lists but not just Sequence

@dataclass(frozen=True)
class PairedSamples:
    sample_a: Sample
    sample_b: Sample

    def __post_init__(self):
        len_a = len(self.sample_a.vals)
        len_b = len(self.sample_b.vals)
        if len_a != len_b:
            raise Exception(f"The length of sample A ({len_a:,}) didn't equal the length of sample B ({len_b:,})")

class StatsResult:  ## not a dataclass because must be either frozen or unfrozen and descendants can be either
    pass

## other
## https://medium.com/@aniscampos/python-dataclass-inheritance-finally-686eaf60fbb5

@dataclass(frozen=True)
class AnovaResult(StatsResult):
    p: float | Decimal
    F: float | Decimal
    group_specs: Sequence[NumericSampleSpecExt]
    sum_squares_within_groups: float | Decimal
    degrees_freedom_within_groups: float
    mean_squares_within_groups: float | Decimal
    sum_squares_between_groups: float | Decimal
    degrees_freedom_between_groups: int
    mean_squares_between_groups: float | Decimal
    obriens_msg: str

    def __str__(self):
        return dedent(f"""\
        ANOVA Result
        ============
        p-value: {self.p}
        F: {self.F}
        Sum of squares within groups: {self.sum_squares_within_groups:,}
        Degrees of freedom within groups: {self.degrees_freedom_within_groups:,}
        Mean squares within groups: {self.mean_squares_within_groups:,}
        Sum of squares between groups: {self.sum_squares_between_groups:,}
        Degrees of freedom between groups: {self.degrees_freedom_between_groups:,}
        Mean of squares between groups: {self.mean_squares_between_groups:,}
        """)

@dataclass(frozen=True)
class ChiSquareResult(StatsResult):
    chi_square: float
    p: float

    def __str__(self):
        return dedent(f"""\
        Chi Square Result
        =================
        p-value: {self.p:,}
        Chi Square: {self.chi_square:,}
        """)

@dataclass(frozen=True)
class KruskalWallisHResult(StatsResult):
    h: float
    p: float
    group_specs: Sequence[NumericSampleSpecExt]
    degrees_of_freedom: int

    def __str__(self):
        bits = []
        bits.append(dedent(f"""\
        Kruskal-Wallis H Result
        =======================
        p-value: {self.p:,}
        Kruskal-Wallis H: {self.h:,}
        Degrees of Freedom: {self.degrees_of_freedom:,}
        """))
        for group_spec in self.group_specs:
            bits.append(str(group_spec))
        return '\n'.join(bits)

@dataclass(frozen=True)
class MannWhitneyUGroupSpec:
    label: str
    n: int
    avg_rank: float
    median: float
    sample_min: float
    sample_max: float

    def __str__(self):
        return dedent(f"""\
        Group Label: {self.label}
        N Values: {self.n:,}
        Average Rank: {self.avg_rank:,}
        Median Value: {self.median:,}
        Minimum Value: {self.sample_min:,}
        Maximum Value: {self.sample_max:,}
        """)

@dataclass(frozen=True)
class MannWhitneyUResult(StatsResult):
    """
    From the fast all at once ranks approach
    """
    small_u: float
    p: float
    group_a_spec: MannWhitneyUGroupSpec
    group_b_spec: MannWhitneyUGroupSpec
    z: float

    def __str__(self):
        bits = []
        bits.append(dedent(f"""\
        Mann Whitney U Result
        =====================
        Small u: {self.small_u:,}
        p-value: {self.p:,}
        """))
        for group_spec in (self.group_a_spec, self.group_b_spec):
            bits.append(str(group_spec))
        return '\n'.join(bits)

@dataclass(frozen=False)
class MannWhitneyUVal(StatsResult):
    """
    rank and counter get populated after creation as part of Mann Whitney processing
    """
    val: float
    sample: Literal[1, 2]
    rank: int | None = None
    counter: int | None = None

@dataclass(frozen=True)
class MannWhitneyUIndivComparisonsResult(StatsResult):
    """
    From the individual comparisons approach.
    Slower but has more obvious workings.
    """
    label_1: str
    label_2: str
    n_1: int
    n_2: int
    u_1: float
    u_2: float
    u: float
    mw_vals: list[MannWhitneyUVal]
    ranks_1: list[int]
    sum_rank_1: int

@dataclass(frozen=True)
class NormalTestResult(StatsResult):
    k2: float | None
    p: float | None
    c_skew: float | None
    z_skew: float | None
    c_kurtosis: float | None
    z_kurtosis: float | None

    def __str__(self):
        k2 = nice_number_if_possible(self.k2)
        p = nice_number_if_possible(self.p)
        c_skew = nice_number_if_possible(self.c_skew)
        z_skew = nice_number_if_possible(self.z_skew)
        c_kurtosis = nice_number_if_possible(self.c_kurtosis)
        z_kurtosis = nice_number_if_possible(self.z_kurtosis)
        str_representation = dedent(f"""\
        Normality Test Result
        =====================
        k2: {k2}
        p-value: {p}
        c Skew: {c_skew}
        z Skew: {z_skew}
        c Kurtosis: {c_kurtosis}
        z Kurtosis: {z_kurtosis}
        """)
        return str_representation

@dataclass(frozen=True)
class CorrelationCalcResult(StatsResult):
    r: float
    p: float
    degrees_of_freedom: int

    def __str__(self):
        return dedent(f"""\
        Correlation Result
        ==================
        r-value: {self.r:,}
        p-value: {self.p:,}
        Degrees of Freedom: {self.degrees_of_freedom:,}
        """)

@dataclass(frozen=True)
class RegressionResult(StatsResult):
    slope: float
    intercept: float
    r: float
    x0: float
    y0: float
    x1: float
    y1: float

@dataclass(frozen=True)
class SpearmansInitTbl:
    x: float
    y: float
    rank_x: int
    rank_y: int
    diff: int
    diff_squared: int

@dataclass(frozen=True)
class SpearmansResult(StatsResult):
    initial_tbl: list
    x_and_rank: list[tuple]
    y_and_rank: list[tuple]
    n_x: int
    n_cubed_minus_n: int
    tot_d_squared: float
    tot_d_squared_x_6: float
    pre_rho: float
    rho: float

@dataclass(frozen=True)
class TTestIndepResult(StatsResult):
    """
    p is the two-tailed probability
    """
    t: float | Decimal
    p: float | Decimal
    group_a_spec: NumericSampleSpecExt
    group_b_spec: NumericSampleSpecExt
    degrees_of_freedom: float
    obriens_msg: str

    def __str__(self):
        bits = []
        bits.append(dedent(f"""\
        Independent T-Test Result
        =========================
        t-value: {self.t:,}
        p-value: {self.p:,}
        Degrees of Freedom: {self.degrees_of_freedom:,}
        O'Brien's Result: {self.obriens_msg}
        """))
        for group_spec in (self.group_a_spec, self.group_b_spec):
            bits.append(str(group_spec))
        return '\n'.join(bits)

@dataclass(frozen=True)
class TTestPairedResult(StatsResult):
    """
    p is the two-tailed probability
    """
    t: float | Decimal
    p: float | Decimal
    group_a_spec: NumericSampleSpec
    group_b_spec: NumericSampleSpec
    degrees_of_freedom: float
    diffs: Sequence[float]

    def __str__(self):
        bits = []
        bits.append(dedent(f"""\
        Paired T-Test Result
        ====================
        t-value: {self.t:,}
        p-value: {self.p:,}
        Degrees of Freedom: {self.degrees_of_freedom:,}
        Diffs: {self.diffs[0]:,} ... {self.diffs[-1]:,} (N diffs: {len(self.diffs):,})
        """))
        for group_spec in (self.group_a_spec, self.group_b_spec):
            bits.append(str(group_spec))
        return '\n'.join(bits)

@dataclass(frozen=True)
class WilcoxonSignedRanksDiffSpec:
    a: float
    b: float
    diff: float

@dataclass(frozen=False)
class WilcoxonSignedRanksRankSpec:
    diff: float
    abs_diff: float
    rank: float
    counter: int | None = None

@dataclass(frozen=True)
class WilcoxonIndivComparisonResult(StatsResult):
    label_a: str
    label_b: str
    diff_specs: list[WilcoxonSignedRanksDiffSpec]
    ranking_specs: list[WilcoxonSignedRanksRankSpec]
    plus_ranks: list[int]
    minus_ranks: list[int]
    sum_plus_ranks: float
    sum_minus_ranks: float
    t: float
    n: int

@dataclass(frozen=True)
class WilcoxonSignedRanksGroupSpec:
    label: str
    n: int
    median: float
    sample_min: float
    sample_max: float

    def __str__(self):
        return dedent(f"""\
        Group Label: {self.label}
        N Values: {self.n:,}
        Median Value: {self.median:,}
        Minimum Value: {self.sample_min:,}
        Maximum Value: {self.sample_max:,}
        """)

@dataclass(frozen=True)
class WilcoxonSignedRanksResult(StatsResult):
    t: int  ## based on ranks and addition and subtraction only
    p: float
    group_a_spec: WilcoxonSignedRanksGroupSpec
    group_b_spec: WilcoxonSignedRanksGroupSpec

    def __str__(self):
        bits = []
        bits.append(dedent(f"""\
        Wilcoxon Signed Ranks Test Result
        =================================
        t-value: {self.t:,}
        p-value: {self.p:,}
        """))
        for group_spec in (self.group_a_spec, self.group_b_spec):
            bits.append(str(group_spec))
        return '\n'.join(bits)

class BoxplotType(StrEnum):
    MIN_MAX_WHISKERS = 'min-max whiskers'
    HIDE_OUTLIERS = 'hide outliers'
    INSIDE_1_POINT_5_TIMES_IQR = 'IQR-based'  ## Inside 1.5 x Inter-Quartile Range


@dataclass(frozen=False)
class BoxResult(StatsResult):
    vals: Sequence[float]
    box_plot_type: BoxplotType = BoxplotType.INSIDE_1_POINT_5_TIMES_IQR

    def __post_init__(self):
        """
        lower_box_val=box_spec.lower_box_val,
        upper_box_val=box_spec.upper_box_val,
        """
        min_measure = min(self.vals)
        max_measure = max(self.vals)
        ## box
        lower_quartile, upper_quartile = get_quartiles(self.vals)
        self.box_bottom = lower_quartile
        self.box_top = upper_quartile
        ## median
        self.median = median(self.vals)
        ## whiskers
        if self.box_plot_type == BoxplotType.MIN_MAX_WHISKERS:
            self.bottom_whisker = min_measure
            self.top_whisker = max_measure
        else:
            iqr = self.box_top - self.box_bottom
            raw_bottom_whisker = self.box_bottom - (1.5 * iqr)
            raw_top_whisker = self.box_top + (1.5 * iqr)
            self.bottom_whisker = get_bottom_whisker(raw_bottom_whisker, self.box_bottom, self.vals)
            self.top_whisker = get_top_whisker(raw_top_whisker, self.box_top, self.vals)
        ## outliers
        if self.box_plot_type == BoxplotType.INSIDE_1_POINT_5_TIMES_IQR:
            self.outliers = [x for x in self.vals
                if x < self.bottom_whisker or x > self.top_whisker]
        else:
            self.outliers = []  ## hidden or inside whiskers
