"""
Usage needs:

Start with raw data and decide on nice number of bins given range.
Then change number of bins if saw-toothing detected.
Once final number of bins decided, get bin details and bin freqs.

May need to get bin details using values from all charts combined if multi-chart histograms.

Once bin details determined, get bin freqs based on values passed in (if multi-chart, values per chart).
"""
from collections.abc import Sequence
from dataclasses import dataclass
import math

@dataclass(frozen=False)
class BinSpec:
    lower_limit: float
    upper_limit: float
    n_bins: int
    bin_width: float

    def validate(self):
        expected_n_bins = round(self.range / self.bin_width)
        if self.n_bins != expected_n_bins:
            raise ValueError(f"{self.n_bins} not expected value {expected_n_bins} "
                f"as calculated from {self.lower_limit=}, {self.upper_limit=}, and {self.bin_width=}")

    def __post_init__(self):
        self.range = self.upper_limit - self.lower_limit
        self.validate()
        bin_start = self.lower_limit
        self.bin_ranges = []
        for bin_n in range(1, self.n_bins + 1):
            bin_end = bin_start + self.bin_width
            self.bin_ranges.append((bin_start, bin_end))
            bin_start = bin_end

    def to_bin_labels(self, *, decimal_points: int = 3):
        rounded_bin_ranges = []
        for raw_bin_start, raw_bin_end in self.bin_ranges:
            ## if ints
            rounded_start = round(raw_bin_start, decimal_points)
            if rounded_start == int(rounded_start):
                bin_start = int(rounded_start)
            else:
                bin_start = rounded_start
            rounded_end = round(raw_bin_end, decimal_points)
            if rounded_end == int(rounded_end):
                bin_end = int(rounded_end)
            else:
                bin_end = rounded_end
            rounded_bin_ranges.append((bin_start, bin_end))
        bin_labels = [f"{lower} to < {upper}" for lower, upper in rounded_bin_ranges]
        bin_labels[-1] = bin_labels[-1].replace('<', '<=')
        return bin_labels

def get_nice_initial_bin_details(vals: Sequence[float], *, debug=False) -> tuple[float, float, int]:
    """
    Goal - set nice bin widths so 'nice' value e.g. 0.2, 0.5, 1
    (or 200, 500, 1000 or 0.002, 0.005, 0.01) and not too many or too few bins.

    Start with a bin width which splits the data into the optimal number of bins.
    Normalise it, adjust upwards to nice size, and denormalise. Check number of bins resulting.

    OK? If room to double number of bins, halve size of normalised bin width,
    and try to adjust upwards to a nice size.
    This time, however, there is the option of 2 as an interval size (so we have 2, 5, or 10).
    Denormalise and recalculate the number of bins.

    Now reset lower and upper limits if appropriate.
    Make lower limit a multiple of the bin_width and make upper limit n_bins*bin_width higher.

    Add another bin if not covering max value.

    :return: lower_limit, upper_limit, n_bins
    """
    ## init
    n_distinct = len(set(vals))
    min_val = min(vals)
    max_val = max(vals)
    data_range = max_val - min_val
    if data_range == 0:
        data_range = 1
    target_n_bins = 20
    """
    If lots of values then 10, otherwise n_distinct unless too low in which case
    4 at lowest.
    """
    if n_distinct >= 10:
        min_n_bins = 10
    elif n_distinct <= 4:
        min_n_bins = 4
    else:
        min_n_bins = n_distinct
    init_bin_width = data_range / (target_n_bins * 1.0)
    ## normalise init_bin_width to val between 1 and 10
    norm_bin_width = init_bin_width
    while norm_bin_width <= 1:
        norm_bin_width *= 10
    while norm_bin_width > 10:
        norm_bin_width /= 10.0
    if debug: print(f'init_bin_width={init_bin_width}, norm_bin_width={norm_bin_width}')
    ## get denorm ratio so can convert norm_bin widths back to data bin widths
    denorm_ratio = init_bin_width/norm_bin_width
    ## adjust upwards to either 5 or 10
    better_norm_bin_width = 5 if norm_bin_width <= 5 else 10
    ## denormalise
    better_bin_width = better_norm_bin_width*denorm_ratio
    n_bins = int(math.ceil(data_range / better_bin_width))
    ## possible to increase granularity?
    if n_bins < min_n_bins:
        ## halve normalised bin width and try again but with an extra option of 2
        norm_bin_width /= 2.0
        if norm_bin_width <= 2:
            better_norm_bin_width = 2
        elif norm_bin_width <= 5:
            better_norm_bin_width = 5
        else:
            better_norm_bin_width = 10
        ## denormalise
        better_bin_width = better_norm_bin_width*denorm_ratio
        n_bins = int(math.ceil(data_range / (better_bin_width * 1.0)))
    lower_limit = min_val
    upper_limit = max_val
    ## Adjust lower and upper limits if bin_width doesn't exactly fit.
    ## If an exact fit, leave alone on assumption the limits are meaningful
    ## e.g. if 9.69 - 19.69 and 20 bins then leave limits alone.
    if better_bin_width * n_bins != data_range:
        if debug:
            print(f"data_range={data_range}, better_bin_width*n_bins={better_bin_width * n_bins}")
        ## Set lower limit to a clean multiple of the bin_width
        ## e.g. 3*bin_width or -6*bin_width.
        ## Identify existing multiple and set to integer below (floor).
        ## Lower limit is now that lower integer times the bin_width.
        ## NB the multiple is an integer but the lower limit might not be
        ## e.g. if the bin_size is a fraction e.g. 0.002
        existing_multiple = lower_limit / better_bin_width
        lower_limit = math.floor(existing_multiple) * better_bin_width
        upper_limit = lower_limit + (n_bins * better_bin_width)
    if max_val > upper_limit:
        upper_limit += better_bin_width
        n_bins += 1
    if debug:
        print(f'For {min_val} to {max_val} use an interval size of {better_bin_width} for a data range of '
            f'{lower_limit} to {upper_limit} giving you {n_bins} bins')
    return lower_limit, upper_limit, n_bins

def get_bin_spec_from_vals(vals: Sequence[float], *, n_bins=10) -> BinSpec:
    """
    Default is N bins but width is larger than the range divided evenly.
    It is enlarged enough, so it has the lowest and uppermost values appearing in the middle of their bins.
    Half a bin before and half a bin after = add one more bin evenly amongst all bins.
    """
    tot_width = max(vals) - min(vals)
    initial_bin_width = (tot_width / n_bins) + 1e-6  ## slightly larger
    bin_width = (tot_width + initial_bin_width) / n_bins
    lower_limit = min(vals) - bin_width / 2  ## lower limit, 1st bin
    upper_limit = lower_limit + (n_bins * bin_width)
    return BinSpec(lower_limit, upper_limit, n_bins, bin_width)

def get_bin_spec_from_limits(limits: tuple[float, float], *, n_bins=10) -> BinSpec:
    lower_limit, upper_limit = limits
    bin_width = (upper_limit - lower_limit) / n_bins
    return BinSpec(lower_limit, upper_limit, n_bins, bin_width)

def get_bin_freqs(vals: Sequence[float], bin_spec: BinSpec) -> list[int]:
    bin_freqs = [0, ] * bin_spec.n_bins
    for val in vals:
        if not bin_spec.lower_limit <= val <= bin_spec.upper_limit:
            raise ValueError(f"Value {val} is not between lower limit {bin_spec.lower_limit} "
                f"and upper limit {bin_spec.upper_limit}")
        if val == bin_spec.upper_limit:  ## includes uppermost value in top bin rather than saving for start of next bin (there isn't one when you're top value ;-))
            top_bin_n = bin_spec.n_bins - 1
            bin2increment = top_bin_n
        else:
            bin2increment = int((val - bin_spec.lower_limit) / bin_spec.bin_width)
        bin_freqs[bin2increment] += 1
    return bin_freqs

def has_saw_toothing(bin_freqs: Sequence[float], *, period: int, start_idx: int = 0) -> bool:
    """
    Saw-toothing is where every nth bin has values, but the others have none.
    """
    period_vals = bin_freqs[start_idx::period]
    sum_period = sum(period_vals)
    sum_all = sum(bin_freqs)
    sum_non_period = sum_all - sum_period
    return sum_non_period == 0

def get_best_bin_details_given_freqs(vals: Sequence[float],
        initial_bin_spec: BinSpec, initial_bin_freqs: Sequence[int]) -> tuple[BinSpec, list[int]]:
    limits = (initial_bin_spec.lower_limit, initial_bin_spec.upper_limit)  ## stable
    ## changing the following as we loop (if we choose fewer bins, we'll have greater frequencies per bin)
    bin_spec = initial_bin_spec
    bin_freqs = initial_bin_freqs
    n_bins = initial_bin_spec.n_bins
    while n_bins > 5:
        if has_saw_toothing(bin_freqs, period=5):
            shrink_factor = 5
        elif has_saw_toothing(bin_freqs, period=2):
            shrink_factor = 2
        elif has_saw_toothing(bin_freqs, period=2, start_idx=1):
            shrink_factor = 2
        else:
            break
        n_bins = int(math.ceil(n_bins / shrink_factor))
        ## update variables as we possibly loop back for fresh attempt to get better results
        bin_spec = get_bin_spec_from_limits(limits, n_bins=n_bins)
        bin_freqs = get_bin_freqs(vals, bin_spec)
    return bin_spec, bin_freqs

def get_bin_details_from_vals(vals: Sequence[float]) -> tuple[BinSpec, list[int]]:
    """
    Includes the uppermost value in top bin.
    This is essential if wanting to have "nice", human-readable bins e.g. 10 to < 20, ... 90 to 100
    because the only alternatives are worse.
    NB label of top bin must be explicit about including upper values. Known problem with continuous distributions.

    There are two functions doing the heavy lifting.
    1) get_bin_spec_from_limits() (vs ... from_vals) which turns limits and n_bins into bin details
    2) get_bin_freqs() which turns values and bin details into bin freqs. Returns a simple list of ints in bin order.

    We try to get nice bins from the values only.
    No assumption about the number of bins we want.
    Not looking at the frequencies per bin yet - just the pleasantness of the bins
    e.g. 4.546 - 7.232 is not as nice as 4-7

    We then get the freqs per bin and see if it worked i.e. have we managed to avoid saw-toothing?
    If not, we try to get better bins (fewer but hopefully all filled in - i.e. minimised number of empty bins).
    We take the best bin_spec, and bin_freqs we can,
    and bundle our final results into a HistogramDetails dataclass for use elsewhere.
    """
    initial_lower_limit, initial_upper_limit, initial_n_bins = get_nice_initial_bin_details(vals)
    limits = (initial_lower_limit, initial_upper_limit)
    initial_bin_spec = get_bin_spec_from_limits(limits, n_bins=initial_n_bins)
    initial_bin_freqs = get_bin_freqs(vals, initial_bin_spec)
    final_bin_spec, final_bin_freqs = get_best_bin_details_given_freqs(vals, initial_bin_spec, initial_bin_freqs)
    return final_bin_spec, final_bin_freqs
