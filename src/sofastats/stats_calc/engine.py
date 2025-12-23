"""
Taken from v1.1 of statlib http://code.google.com/p/python-statlib/

NB lots of ongoing change at
http://projects.scipy.org/scipy/browser/trunk/scipy/stats/stats.py

Code below here is modified versions of code in stats.py and pstats.py
"""
from collections.abc import Sequence
import copy
import decimal
import math
from statistics import median

import numpy as np

from sofastats import logger
from sofastats.conf.main import MAX_RANK_DATA_VALS
from sofastats.stats_calc.interfaces import (
    AnovaResult, ChiSquareResult, CorrelationCalcResult, KruskalWallisHResult,
    MannWhitneyUGroupSpec, MannWhitneyUIndivComparisonsResult, MannWhitneyUResult, MannWhitneyUVal,
    NormalTestResult,
    NumericSampleSpec, NumericSampleSpecExt,
    RegressionResult,
    Sample, SpearmansResult, SpearmansInitTbl, TTestIndepResult, TTestPairedResult,
    WilcoxonSignedRanksDiffSpec, WilcoxonSignedRanksGroupSpec, WilcoxonSignedRanksRankSpec, WilcoxonSignedRanksResult,
    WilcoxonIndivComparisonResult)
from sofastats.utils.maths import n2d
from sofastats.utils.stats import get_obriens_msg

D = decimal.Decimal

# The "minus 3" at the end of this formula is often explained as a correction to
# make the kurtosis of the normal distribution equal to zero. Another reason can
# be seen by looking at the formula for the kurtosis of the sum of random
# variables. ... This formula would be much more complicated if kurtosis were
# defined just as μ4 / σ4 (without the minus 3).
# http://en.wikipedia.org/wiki/Kurtosis

FISHER_KURTOSIS_ADJUSTMENT = 3.0

# Copyright notice for scipy stats.py.

# Copyright (c) Gary Strangman.  All rights reserved
#
# Disclaimer
#
# This software is provided "as-is".  There are no expressed or implied
# warranties of any kind, including, but not limited to, the warranties
# of merchantability and fittness for a given application.  In no event
# shall Gary Strangman be liable for any direct, indirect, incidental,
# special, exemplary or consequential damages (including, but not limited
# to, loss of use, data or profits, or business interruption) however
# caused and on any theory of liability, whether in contract, strict
# liability or tort (including negligence or otherwise) arising in any way
# out of the use of this software, even if advised of the possibility of
# such damage.
#

#
# Heavily adapted for use by SciPy 2002 by Travis Oliphant

# noinspection PyBroadException
def histogram(inlist, numbins=10, defaultreallimits=None, printextras=0, *, inc_uppermost_val_in_top_bin=True):
    """
    From stats.py. Modified to include the uppermost value in top bin. This is
    essential if wanting to have "nice", human-readable bins e.g. 10 to < 20
    because the only alternatives are worse. NB label of top bin must be
    explicit about including upper values. Known problem with continuous
    distributions.
    -------------------------------------
    Returns
    (i) a list of histogram bin counts
    (ii) the smallest value of the histogram binning
    (iii) the bin width (the last 2 are not necessarily integers). Default
    number of bins is 10. If no sequence object is given for defaultreallimits,
    the routine picks (usually non-pretty) bins spanning all the numbers in the
    inlist.

    Usage:   histogram (inlist, numbins=10, defaultreallimits=None,
        suppressoutput=0)
    Returns: list of bin values, lowerreallimit, binsize, extrapoints
    """
    if numbins < 2:
        raise ValueError(f"Not enough bins selected - only {numbins}")
    if defaultreallimits is not None:
        if ((not isinstance(defaultreallimits, (list, tuple)))
                or len(defaultreallimits) == 1):  ## only one limit given, assumed to be lower one & upper is calc'd
            lowerreallimit = defaultreallimits
            upperreallimit = 1.000001 * max(inlist)
        else:  ## assume both limits given
            lowerreallimit = defaultreallimits[0]
            upperreallimit = defaultreallimits[1]
        binsize = (upperreallimit - lowerreallimit) / float(numbins)
    else:  ## no limits given for histogram, both must be calc'd
        estbinwidth = (max(inlist) - min(inlist)) / float(numbins) + 1e-6  ##1=>cover all
        binsize = (max(inlist) - min(inlist) + estbinwidth) / float(numbins)
        lowerreallimit = min(inlist) - binsize / 2  ## lower real limit,1st bin
        upperreallimit = 1.000001 * max(
            inlist)  ## added by me so can include top val in final bin. Use same code as orig to calc upp from lower
    bins = [0] * numbins
    extra_points = 0
    for num in inlist:
        try:
            if (num - lowerreallimit) < 0 and inc_uppermost_val_in_top_bin:
                extra_points = extra_points + 1
            else:
                if num == upperreallimit:  ## includes uppermost value in top bin
                    bins[numbins - 1] += 1
                else:  ## the original always did this if not (num-lowerreallimit) < 0
                    bintoincrement = int((num - lowerreallimit) / float(binsize))
                    bins[bintoincrement] = bins[bintoincrement] + 1
        except Exception:
            extra_points = extra_points + 1
    if extra_points > 0 and printextras == 1:
        logger.warning('\nPoints outside given histogram range =', extra_points)
    logger.debug(f"bins={bins}, lowerreallimit={lowerreallimit}, binsize={binsize}, extrapoints={extra_points}")
    return bins, lowerreallimit, binsize, extra_points

def chisquare(f_obs, f_exp=None, df=None) -> ChiSquareResult:
    """
    From stats.py.  Modified to receive df (degree of freedom, not dataframe)
    e.g. when in a crosstab.
    In a crosstab, df will NOT  be k-1 it will be (a-1) x (b-1)
          Male   Female
    0-19
    20-29
    30-39
    40-49
    50+
    k=(2x5) i.e. 10, k-1 = 9 but df should be (2-1) x (5-1) i.e. 4

    Also turns f_obs[i] explicitly into a float so no mismatching between floats
    and decimals.
    -------------------------------------
    Calculates a one-way chi square for list of observed frequencies and returns
    the result.  If no expected frequencies are given, the total N is assumed to
    be equally distributed across all groups.

    Usage:   chisquare(f_obs, f_exp=None)   f_obs = list of observed cell freq.
    Returns: chisquare-statistic, associated p-value
    """
    k = len(f_obs)  ## number of groups
    if f_exp is None:
        f_exp = [sum(f_obs) / float(k)] * len(f_obs)  ## create k bins with = freq.
    chi_sq = 0
    for i in range(len(f_obs)):
        chi_sq = chi_sq + (float(f_obs[i]) - float(f_exp[i])) ** 2 / float(f_exp[i])
    if not df: df = k - 1
    return ChiSquareResult(
        chi_square=chi_sq, p=chisqprob(chi_sq, df)
    )

# noinspection PyUnusedLocal
def anova_orig(lst_samples, lst_labels, *, high=False):
    """
    Included for testing only.

    From stats.py.  Changed name to anova, replaced array versions e.g. amean
    with list versions e.g. lmean, supply data as list of lists.
    -------------------------------------
    Performs a 1-way ANOVA, returning an F-value and probability given
    any number of groups.  From Heiman, pp.394-7.

    Returns: F value, one-tailed p-value
    """
    a = len(lst_samples)  # ANOVA on 'a' groups, each in its own list
    n = len(lst_samples[0])
    # ns = [0]*a
    alldata = []
    sample_specs = []
    for i in range(a):
        sample = lst_samples[i]
        label = lst_labels[i]
        sample_spec = NumericSampleSpec(lbl=label, n=n, mean=mean(sample), median=median(sample), std_dev=stdev(sample),
            sample_min=min(sample), sample_max=max(sample))
        sample_specs.append(sample_spec)
    for i in range(len(lst_samples)):
        alldata = alldata + lst_samples[i]
    bign = len(alldata)
    sstot = sum_squares(alldata) - (square_of_sums(alldata) / float(bign))
    ssbn = 0
    for sample in lst_samples:
        ssbn = ssbn + square_of_sums(sample) / float(len(sample))
    ssbn = ssbn - (square_of_sums(alldata) / float(bign))
    sswn = sstot - ssbn
    dfbn = a - 1
    dfwn = bign - a
    msb = ssbn / float(dfbn)
    msw = sswn / float(dfwn)
    F = msb / msw
    p = fprob(dfbn, dfwn, F)
    logger.info(f'Using orig with F: {F}')
    return p, F, sample_specs, sswn, dfwn, msw, ssbn, dfbn, msb

def has_decimal_type_mix(numbers) -> bool:
    """
    Some operators support mix of Decimal and other numeric types (e.g. <, >)
    but others don't e.g. /. So we sometimes need to know if there is a mix.
    """
    decimal_type_mix = [type(x) == 'decimal.Decimal' for x in numbers]
    is_mixed = len(set(decimal_type_mix)) > 1
    return is_mixed

def get_se(n, mysd, *, high=True):
    denom = math.sqrt(n)
    if high:
        denom = D(denom)
    logger.debug(f"mysd={mysd}, denom={denom}")
    if has_decimal_type_mix(numbers=(mysd, denom)):
        raise Exception("Can't mix decimals and other numbers for division when calculating SE")
    se = mysd / denom
    return se

def get_ci95(sample_vals=None, mymean=None, mysd=None, n=None, *, high=False):
    if sample_vals is None and (n is None or mymean is None or mysd is None):
        raise Exception("Unable to calculate confidence interval without either a sample or all of n, mean, and sd.")
    if n is None:
        n = len(sample_vals)
        if high:
            n = D(n)
    mymean = mymean if mymean is not None else mean(sample_vals, high=high)
    mysd = mysd if mysd is not None else stdev(sample_vals, high=high)
    if has_decimal_type_mix(numbers=(mymean, mysd, n)):
        raise Exception("Cannot mix decimals and other numbers for some calculations e.g. division")
    if n < 30:  ## ok for mix decimals and non-dec
        logger.warning("Using sample sd instead of population sd even though n < 30. May not be reliable.")
    se = get_se(n, mysd, high=high)
    sds = 1.96
    if high:
        sds = D(sds)
    diff = sds * se
    if has_decimal_type_mix(numbers=(mymean, diff)):
        raise Exception("Cannot mix decimals and other numbers for some calculations "
            "e.g. addition and subtraction when calculating CI lower and upper bounds")
    lower95 = mymean - diff
    upper95 = mymean + diff
    return lower95, upper95

def get_numeric_sample_spec_ext(sample: Sample, *, high=False) -> NumericSampleSpecExt:
    sample_vals = sample.vals
    my_mean = mean(sample_vals, high=high)
    my_median = median(sample_vals)
    std_dev = stdev(sample_vals, high=high)
    ci95 = get_ci95(sample_vals, my_mean, std_dev, n=None, high=high)
    normal_test_result = normal_test(sample_vals)
    kurtosis_val = (normal_test_result.c_kurtosis if normal_test_result.c_kurtosis is not None
        else "Unable to calculate kurtosis")
    skew_val = (normal_test_result.c_skew if normal_test_result.c_skew is not None
        else "Unable to calculate skew")
    normality_test_p = normal_test_result.p if normal_test_result.p is not None else "Unable to calculate overall p for normality test"
    numeric_sample_spec_extended = NumericSampleSpecExt(
        lbl=sample.lbl, n=len(sample_vals), mean=my_mean, median=my_median, std_dev=std_dev,
        sample_min=min(sample_vals), sample_max=max(sample_vals), ci95=ci95,
        kurtosis=kurtosis_val, skew=skew_val, normality_test_p=normality_test_p, vals=sample_vals)
    return numeric_sample_spec_extended

def anova(group_lbl: str, measure_fld_lbl: str, samples: Sequence[Sample], *, high=True) -> AnovaResult:
    """
    From NIST algorithm used for their ANOVA tests.

    Note - keep anova_lite following same logic as here but without the extras.

    Args:
        high: high precision but much, much slower. Multiplies each by 10 (and divides by 10 and 100 as appropriate)
        plus uses decimal rather than floating point.
        Needed to handle difficult datasets e.g. ANOVA test 9 from NIST site.  TODO: relate to other comment on 9
    """
    orig_samples_vals = [sample.vals for sample in samples]
    n_samples = len(orig_samples_vals)
    sample_ns = list(map(len, orig_samples_vals))
    group_specs = []
    for sample in samples:
        sample_spec_extended = get_numeric_sample_spec_ext(sample, high=high)
        group_specs.append(sample_spec_extended)
    if high:  ## inflate for ss (sum squares) calculations only
        ## if to 1 decimal point will push from float to integer (reduce errors)
        ## deflates final results appropriately in get_sswn() and get_ssbn()
        inflated_samples = []
        for sample_vals in orig_samples_vals:
            inflated_samples.append([x * 10 for x in sample_vals])  ## NB inflated
        samples4ss_calc = inflated_samples
        sample_means4ss_calc = [n2d(mean(x, high=high)) for x in samples4ss_calc]  ## NB inflated
    else:
        samples4ss_calc = orig_samples_vals
        sample_means4ss_calc = [mean(x, high=high) for x in samples4ss_calc]
    sswn = get_sswn(samples4ss_calc, sample_means4ss_calc, high=high)
    dfwn = sum(sample_ns) - n_samples
    mean_squ_wn = sswn / dfwn
    if mean_squ_wn == 0:
        raise ValueError(f"Inadequate variability in samples of {measure_fld_lbl} "
            f"for groups defined by {group_lbl} - mean_squ_wn is 0")
    ssbn = get_ssbn(samples4ss_calc, sample_means4ss_calc, n_samples, sample_ns, high=high)
    dfbn = n_samples - 1
    mean_squ_bn = ssbn / dfbn
    F = mean_squ_bn / mean_squ_wn
    p = fprob(dfbn, dfwn, F, high=high)
    obriens_msg = get_obriens_msg(orig_samples_vals, sim_variance, high=high)
    return AnovaResult(p=p, F=F, group_specs=group_specs,
        sum_squares_within_groups=sswn, degrees_freedom_within_groups=dfwn, mean_squares_within_groups=mean_squ_wn,
        sum_squares_between_groups=ssbn, degrees_freedom_between_groups=dfbn, mean_squares_between_groups=mean_squ_bn,
        obriens_msg=obriens_msg)

def anova_p_only(samples: Sequence[Sequence[float]], *, high=True) -> float:
    """
    Should be exactly the same calculation as in anova()
    but everything stripped out that isn't needed
    when you only care about producing a p value.
    Needs to stay in sync in unlikely event of any changes.
    """
    orig_samples = samples
    n_samples = len(orig_samples)
    sample_ns = list(map(len, orig_samples))
    if high:  ## inflate for ss (sum squares) calculations only
        ## if to 1 decimal point will push from float to integer (reduce errors)
        ## deflates final results appropriately in get_sswn() and get_ssbn()
        inflated_samples = []
        for sample in orig_samples:
            inflated_samples.append([x * 10 for x in sample])  ## NB inflated
        samples4ss_calc = inflated_samples
        sample_means4ss_calc = [n2d(mean(x, high=high)) for x in samples4ss_calc]  ## NB inflated
    else:
        samples4ss_calc = orig_samples
        sample_means4ss_calc = [mean(x, high=high) for x in samples4ss_calc]
    sswn = get_sswn(samples4ss_calc, sample_means4ss_calc, high=high)
    dfwn = sum(sample_ns) - n_samples
    mean_squ_wn = sswn / dfwn
    if mean_squ_wn == 0:
        raise ValueError("Inadequate variability in samples - mean_squ_wn is 0")
    ssbn = get_ssbn(samples4ss_calc, sample_means4ss_calc, n_samples, sample_ns, high=high)
    dfbn = n_samples - 1
    mean_squ_bn = ssbn / dfbn
    F = mean_squ_bn / mean_squ_wn
    p = fprob(dfbn, dfwn, F, high=high)
    return p

def get_sswn(samples, sample_means, *, high=False):
    """
    Get sum of squares within treatment.

    If high precision, the function receives uniformly inflated
    samples and sample means and produces a deflated result.
    """
    if high:
        sswn = D('0')  ## sum of squares within treatment
        for i, sample in enumerate(samples):
            diffs = []
            sample_mean = sample_means[i]
            for val in sample:
                diffs.append(n2d(val) - sample_mean)
            squ_diffs = [(x ** 2) for x in diffs]
            sum_squ_diffs = sum(squ_diffs)
            sswn += sum_squ_diffs
        sswn = sswn / 10 ** 2  ## deflated
    else:
        sswn = 0  ## sum of squares within treatment
        for i, sample in enumerate(samples):
            diffs = []
            sample_mean = sample_means[i]
            for val in sample:
                diffs.append(val - sample_mean)
            squ_diffs = [(x ** 2) for x in diffs]
            sum_squ_diffs = sum(squ_diffs)
            sswn += sum_squ_diffs
    return sswn

def get_ssbn(samples, sample_means, n_samples, sample_ns, *, high=False):
    """
    Get sum of squares between treatment.

    If high precision, the function receives uniformly inflated
    samples and sample means and produces a deflated result.
    """
    if not high:
        sum_all_vals = sum(sum(x) for x in samples)
        n_tot = sum(sample_ns)
        grand_mean = sum_all_vals / float(n_tot)  ## correction factor
        squ_diffs = []
        for i in range(n_samples):
            squ_diffs.append((sample_means[i] - grand_mean) ** 2)
        sum_n_x_squ_diffs = 0
        for i in range(n_samples):
            sum_n_x_squ_diffs += sample_ns[i] * squ_diffs[i]
        ssbn = sum_n_x_squ_diffs
    else:
        sum_all_vals = n2d(sum(n2d(sum(x)) for x in samples))
        n_tot = n2d(sum(sample_ns))
        grand_mean = sum_all_vals / n_tot  ## NB inflated
        squ_diffs = []
        for i in range(n_samples):
            squ_diffs.append((sample_means[i] - grand_mean) ** 2)
        sum_n_x_squ_diffs = D('0')
        for i in range(n_samples):
            sum_n_x_squ_diffs += sample_ns[i] * squ_diffs[i]
        ssbn = sum_n_x_squ_diffs / (10 ** 2)  ## deflated
    return ssbn

def kruskalwallish(samples: Sequence[Sample]) -> KruskalWallisHResult:
    """
    From stats.py.  No changes except also return a dic for each sample with
    median etc and args -> samples, plus df.  Also raise a different error.
    -------------------------------------
    The Kruskal-Wallis H-test is a non-parametric ANOVA for 3 or more
    groups, requiring at least 5 subjects in each group.  This function
    calculates the Kruskal-Wallis H-test for 3 or more independent samples
    and returns the result.

    Usage:   kruskalwallish(samples)
    Returns: H-statistic (corrected for ties), associated p-value
    """
    group_specs = []
    sample_vals = [sample.vals for sample in samples]
    for sample in samples:
        sample_spec_extended = get_numeric_sample_spec_ext(sample, high=False)
        group_specs.append(sample_spec_extended)
    # n = [0]*len(sample_vals)
    all_data = []
    n = list(map(len, sample_vals))
    for i in range(len(sample_vals)):
        all_data = all_data + sample_vals[i]
    ranked = rankdata(all_data)
    T = tiecorrect(ranked)
    for i in range(len(sample_vals)):
        sample_vals[i] = ranked[0:n[i]]
        del ranked[0:n[i]]
    rsums = []
    for i in range(len(sample_vals)):
        rsums.append(sum(sample_vals[i]) ** 2)
        rsums[i] = rsums[i] / float(n[i])
    ssbn = sum(rsums)
    total_n = sum(n)
    h = 12.0 / (total_n * (total_n + 1)) * ssbn - 3 * (total_n + 1)
    df = len(sample_vals) - 1
    if T == 0:
        raise ValueError("Inadequate variability - T is 0")
    h = h / float(T)
    return KruskalWallisHResult(h=h, p=chisqprob(h, df), group_specs=group_specs, degrees_of_freedom=df)

def ttest_ind(sample_a: Sample, sample_b: Sample, *, use_orig_var=False) -> TTestIndepResult:
    """
    From stats.py - there are changes to variable labels and comments; and the
    output is extracted early to give greater control over presentation. There
    are no changes to algorithms apart from calculating sds once, rather than
    squaring to get var and taking sqrt to get sd again ;-). Plus use variance
    to get var, not stdev then squared. Also put denominator separately so can
    detect 0 (inadequate variability)

    :param bool use_orig_var: if True use original (flawed) approach to sd and
     var. Needed for unit testing against stats.py. Sort of like matching bug
     for bug ;-).

    ---------------------------------------------------------------------
    Calculates the t-obtained T-test on TWO INDEPENDENT samples of
    scores a, and b. From Numerical Recipes, p.483.
    """
    mean_a = mean(sample_a.vals)
    mean_b = mean(sample_b.vals)
    if use_orig_var:
        se_a = stdev(sample_a.vals) ** 2
        se_b = stdev(sample_b.vals) ** 2
    else:
        se_a = variance(sample_a.vals)
        se_b = variance(sample_b.vals)
    n_a = len(sample_a.vals)
    n_b = len(sample_b.vals)
    df = n_a + n_b - 2
    svar = ((n_a - 1) * se_a + (n_b - 1) * se_b) / float(df)
    denom = math.sqrt(svar * (1.0 / n_a + 1.0 / n_b))
    if denom == 0:
        raise ValueError("Inadequate variability - denom is 0")
    sample_a_spec = get_numeric_sample_spec_ext(sample_a, high=False)
    sample_b_spec = get_numeric_sample_spec_ext(sample_b, high=False)
    t = (mean_a - mean_b) / denom
    p = betai(0.5 * df, 0.5, df / (df + t * t))
    obriens_msg = get_obriens_msg([sample_a.vals, sample_b.vals], sim_variance, high=False)
    return TTestIndepResult(t=t, p=p,
        group_a_spec=sample_a_spec, group_b_spec=sample_b_spec,
        degrees_of_freedom=df, obriens_msg=obriens_msg)

def ttest_rel(*, sample_a: Sample, sample_b: Sample) -> TTestPairedResult:
    """
    The samples must be paired.

    From stats.py - there are changes to variable labels and comments;
    and the output is extracted early to give greater control over presentation.
    A list of the differences is extracted along the way.
    There are no changes to algorithms. Also added trap for zero division error.

    :return: t, p, dic_a, dic_b (p is the two-tailed probability), diffs
    :rtype: tuple
    ---------------------------------------------------------------------
    Calculates the t-obtained T-test on TWO RELATED samples of scores, a and b.
    From Numerical Recipes, p.483.
    """
    if len(sample_a.vals) != len(sample_b.vals):
        raise ValueError('Unequal length lists in ttest_rel.')
    mean_a = mean(sample_a.vals)
    mean_b = mean(sample_b.vals)
    median_a = median(sample_a.vals)
    median_b = median(sample_b.vals)
    var_a = variance(sample_a.vals)
    var_b = variance(sample_b.vals)
    n = len(sample_a.vals)
    cov = 0
    diffs = []
    for i in range(n):
        item_a = sample_a.vals[i]
        item_b = sample_b.vals[i]
        diff = item_b - item_a
        diffs.append(diff)
        cov = cov + (item_a - mean_a) * (item_b - mean_b)
    df = n - 1
    cov = cov / float(df)
    sd = math.sqrt((var_a + var_b - 2.0 * cov) / float(n))
    if sd == 0:
        raise Exception('Unable to calculate t statistic - insufficient '
            'variability in at least one variable.')
    t = (mean_a - mean_b) / sd
    p = betai(0.5 * df, 0.5, df / (df + t * t))
    min_a = min(sample_a.vals)
    min_b = min(sample_b.vals)
    max_a = max(sample_a.vals)
    max_b = max(sample_b.vals)
    sd_a = math.sqrt(var_a)
    sd_b = math.sqrt(var_b)
    ci95_a = get_ci95(sample_a.vals, mean_a, sd_a)
    ci95_b = get_ci95(sample_b.vals, mean_b, sd_b)
    sample_a_spec = NumericSampleSpec(lbl=sample_a.lbl, n=n, mean=mean_a, median=median_a, std_dev=sd_a,
        sample_min=min_a, sample_max=max_a, ci95=ci95_a)
    sample_b_spec = NumericSampleSpec(lbl=sample_b.lbl, n=n, mean=mean_b, median=median_b, std_dev=sd_b,
        sample_min=min_b, sample_max=max_b, ci95=ci95_b)
    return TTestPairedResult(
        t=t, p=p, group_a_spec=sample_a_spec, group_b_spec=sample_b_spec, degrees_of_freedom=df, diffs=diffs)

def mann_whitney_u(*, sample_a: Sample, sample_b: Sample, high_volume_ok=False) -> MannWhitneyUResult:
    """
    From stats.py - there are changes to variable labels and comments; and the
    output is extracted early to give greater control over presentation. Also
    added calculation of mean ranks, plus min and max values. And changed error
    type. And added high_volume_ok option.

    Used when getting the result - the individual comparison version is _also_ run
    when getting the workings for display.
    -------------------------------------
    Calculates a Mann-Whitney U statistic on the provided scores and returns the
    result. Use only when the n in each condition is < 20 and you have
    2 independent samples of ranks. NOTE: Mann-Whitney U is significant if the
    u obtained is LESS THAN or equal to the critical value of U found in the
    tables. Equivalent to Kruskal-Wallis H with just 2 groups.

    Usage:   mannwhitneyu(data)
    :return: u-statistic, one-tailed p-value (i.e., p(z(U))), dic_a, dic_b)
    :rtype: tuple
    """
    n_a = len(sample_a.vals)
    n_b = len(sample_b.vals)
    ranked = rankdata(sample_a.vals + sample_b.vals, high_volume_ok=high_volume_ok)
    rank_a = ranked[0: n_a]  ## get the sample_a ranks
    rank_b = ranked[n_a:]  ## the rest are sample_b ranks
    avg_rank_a = mean(rank_a)
    avg_rank_b = mean(rank_b)
    u_a = n_a * n_b + (n_a * (n_a + 1)) / 2.0 - sum(rank_a)  ## calc U for sample_a
    u_b = n_a * n_b - u_a  ## remainder is U for sample_b
    big_u = max(u_a, u_b)
    small_u = min(u_a, u_b)
    T = math.sqrt(tiecorrect(ranked))  ## correction factor for tied scores
    if T == 0:
        raise ValueError("Inadequate variability - T is 0")
    sd = math.sqrt(T * n_a * n_b * (n_a + n_b + 1) / 12.0)
    z = abs((big_u - n_a * n_b / 2.0) / sd)  ## normal approximation for prob calc
    p = 1.0 - zprob(z)
    min_a = min(sample_a.vals)
    min_b = min(sample_b.vals)
    max_a = max(sample_a.vals)
    max_b = max(sample_b.vals)
    group_a_spec = MannWhitneyUGroupSpec(lbl=sample_a.lbl, n=n_a, avg_rank=avg_rank_a,
        median=median(sample_a.vals), sample_min=min_a, sample_max=max_a)
    group_b_spec = MannWhitneyUGroupSpec(lbl=sample_b.lbl, n=n_b, avg_rank=avg_rank_b,
        median=median(sample_b.vals), sample_min=min_b, sample_max=max_b)
    return MannWhitneyUResult(small_u=small_u, p=p, group_a_spec=group_a_spec, group_b_spec=group_b_spec, z=z)

def mann_whitney_u_indiv_comparisons(*,
        sample_a: Sample, sample_b: Sample,
        high_volume_ok=False) -> MannWhitneyUIndivComparisonsResult:
    """
    The example in "Simple Statistics - A course book for the social sciences" Frances Clegg pp.164-166
    refers to A as the shorted list (if uneven lengths)
    so there is some risk of confusion because A in SOFA refers to the leftmost variable.
    So using _1 and _2 for sample names.
    Doesn't alter result which is 1 or 2 - purely to reduce amount of calculation.

    Note - the rank all the data approach vs the make every individual comparison approach
    yield exactly the same results.
    The comparison approach is more intuitive in meaning - the ranked approach is much faster.

    Used when displaying the workings.
    """
    len_a = len(sample_a.vals)
    len_b = len(sample_b.vals)
    if len_b < len_a:  ## make a first unless b shorter
        sample_1 = sample_b.vals
        sample_2 = sample_a.vals
        label_1 = sample_b.lbl
        label_2 = sample_a.lbl
    else:
        sample_1 = sample_a.vals
        sample_2 = sample_b.vals
        label_1 = sample_a.lbl
        label_2 = sample_b.lbl
    len_1 = len(sample_1)
    len_2 = len(sample_2)
    ## vals, counter, ranking
    mw_vals_1 = [MannWhitneyUVal(val=val, sample=1) for val in sample_1]
    mw_vals_2 = [MannWhitneyUVal(val=val, sample=2) for val in sample_2]
    mw_vals = mw_vals_1 + mw_vals_2
    mw_vals.sort(key=lambda sv: sv.val)
    vals = sample_1 + sample_2
    vals_ranked = rankdata(vals, high_volume_ok=high_volume_ok)
    val_ranks = dict(zip(vals, vals_ranked))  ## works because all abs diffs which are the same share a single rank
    for counter, mw_val in enumerate(mw_vals, 1):
        mw_val.rank = val_ranks[mw_val.val]
        mw_val.counter = counter
    ranks_1 = [mw_val.rank for mw_val in mw_vals if mw_val.sample == 1]
    sum_rank_1 = sum(mw_val.rank for mw_val in mw_vals if mw_val.sample == 1)
    u_1 = len_1 * len_2 + (len_1 * (len_1 + 1)) / 2.0 - sum_rank_1
    u_2 = len_1 * len_2 - u_1
    u = min(u_1, u_2)
    details = MannWhitneyUIndivComparisonsResult(
        lbl_1=label_1, lbl_2=label_2,
        n_1=len_1, n_2=len_2,
        u_1=u_1, u_2=u_2, u=u,
        mw_vals=mw_vals, ranks_1=ranks_1, sum_rank_1=sum_rank_1,
    )
    return details

def wilcoxont(*, sample_a: Sample, sample_b: Sample, high_volume_ok=False) -> WilcoxonSignedRanksResult:
    """
    From stats.py.  Added error trapping. Changes to variable labels.
    Added calculation of n, medians, plus min and max values.
    And added high_volume_ok option.
    -------------------------------------
    Calculates the Wilcoxon T-test for related samples and returns the result.
    A non-parametric T-test.

    Usage:   wilcoxont(sample_a,sample_b)
    Returns: a t-statistic, two-tail probability estimate, z
    """
    if len(sample_a.vals) != len(sample_b.vals):
        raise ValueError('Unequal N in wilcoxont. Aborting.')
    n = len(sample_a.vals)
    d = []
    for i in range(len(sample_a.vals)):
        try:
            diff = sample_a.vals[i] - sample_b.vals[i]
        except TypeError:
            raise Exception(
                'Both values in pair must be numeric:'
                f' {sample_a.vals[i]} and {sample_b.vals[i]}')
        if diff != 0:
            d.append(diff)
    count = len(d)
    absd = list(map(abs, d))
    absranked = rankdata(absd, high_volume_ok=high_volume_ok)
    r_plus = 0.0
    r_minus = 0.0
    for i in range(len(list(absd))):
        if d[i] < 0:
            r_minus = r_minus + absranked[i]
        else:
            r_plus = r_plus + absranked[i]
    wt = min(r_plus, r_minus)
    mn = count * (count + 1) * 0.25
    se = math.sqrt(count * (count + 1) * (2.0 * count + 1.0) / 24.0)
    z = math.fabs(wt - mn) / se
    prob = 2 * (1.0 - zprob(abs(z)))
    min_a = min(sample_a.vals)
    min_b = min(sample_b.vals)
    max_a = max(sample_a.vals)
    max_b = max(sample_b.vals)
    group_a_spec = WilcoxonSignedRanksGroupSpec(
        lbl=sample_a.lbl, n=n, median=median(sample_a.vals), sample_min=min_a, sample_max=max_a)
    group_b_spec = WilcoxonSignedRanksGroupSpec(
        lbl=sample_b.lbl, n=n, median=median(sample_b.vals), sample_min=min_b, sample_max=max_b)
    return WilcoxonSignedRanksResult(t=wt, p=prob, group_a_spec=group_a_spec, group_b_spec=group_b_spec)

def wilcoxon_signed_ranks_indiv_comparisons(
        sample_a: Sample, sample_b: Sample,
        label_a='Sample 1', label_b='Sample 2') -> WilcoxonIndivComparisonResult:
    """
    Only return worked example if a small amount of data. Otherwise, return an empty dict.

    See "Simple Statistics - A course book for the social sciences" Frances Clegg pp.158-160

    Not focused on performance - just clarity
    """
    pairs = zip(sample_a.vals, sample_b.vals)
    ## diffs between pairs (always in same order but which order doesn't matter
    diff_specs = [WilcoxonSignedRanksDiffSpec(a=a, b=b, diff=a - b) for a, b in pairs]
    ## get ranks on absolutes and then attach back
    abs_diffs = [abs(diff_spec.diff) for diff_spec in diff_specs]
    abs_diffs.sort()
    ranks = rankdata(abs_diffs)
    ## link ranks to diffs and abs diffs
    abs_diff_ranks = dict(zip(abs_diffs, ranks))  ## works because all abs diffs which are the same share a single rank
    ranking_specs = []
    for diff_spec in diff_specs:
        if diff_spec.diff != 0:
            ranking_specs.append(
                WilcoxonSignedRanksRankSpec(
                    diff=diff_spec.diff,
                    abs_diff=abs(diff_spec.diff),
                    rank=abs_diff_ranks[abs(diff_spec.diff)],
                )
            )  ## remember - the ranks relates to the absolute value not the original value
    ranking_specs.sort(key=lambda rs: (abs(rs.diff), rs.diff))
    ## add counter
    for counter, ranking_spec in enumerate(ranking_specs, 1):
        ranking_spec.counter = counter
    plus_ranks = [ranking_spec.rank for ranking_spec in ranking_specs if ranking_spec.diff > 0]
    minus_ranks = [ranking_spec.rank for ranking_spec in ranking_specs if ranking_spec.diff < 0]
    ## sum the ranks separately
    sum_plus_ranks = sum(plus_ranks)
    sum_minus_ranks = sum(minus_ranks)
    ## calculate t and N (N excludes 0-diff pairs)
    t = min(sum_plus_ranks, sum_minus_ranks)
    n = len(plus_ranks) + len(minus_ranks)
    result = WilcoxonIndivComparisonResult(
        label_a=label_a, label_b=label_b,
        diff_specs=diff_specs, ranking_specs=ranking_specs,
        plus_ranks=plus_ranks, minus_ranks=minus_ranks,
        sum_plus_ranks=sum_plus_ranks, sum_minus_ranks=sum_minus_ranks,
        t=t, n=n)
    return result

def linregress(x, y):
    """
    From stats.py. No changes except calling renamed ss (now sum_squares). And
    adding a zero division trap. And Py3 changes.
    -------------------------------------
    Calculates a regression line on x,y pairs.

    Usage:   linregress(x,y)      x,y are equal-length lists of x-y coordinates
    Returns: slope, intercept, r, two-tailed prob, sterr-of-estimate
    """
    TINY = 1.0e-20
    if len(x) != len(y):
        raise ValueError("Input values not paired in linregress. Aborting.")
    n = len(x)
    x = list(map(float, x))
    y = list(map(float, y))
    xmean = mean(x)
    ymean = mean(y)
    r_num = float(n * (summult(x, y)) - sum(x) * sum(y))
    r_den = math.sqrt((n * sum_squares(x) - square_of_sums(x))
                      * (n * sum_squares(y) - square_of_sums(y)))
    try:
        r = r_num / r_den
    except ZeroDivisionError:
        raise Exception("Unable to calculate linear regression because of limited variability in one dimension")
    # z = 0.5*math.log((1.0+r+TINY)/(1.0-r+TINY))
    df = n - 2
    t = r * math.sqrt(df / ((1.0 - r + TINY) * (1.0 + r + TINY)))
    prob = betai(0.5 * df, 0.5, df / (df + t * t))
    slope = r_num / float(n * sum_squares(x) - square_of_sums(x))
    intercept = ymean - slope * xmean
    sterrest = math.sqrt(1 - r * r) * samplestdev(y)
    return slope, intercept, r, prob, sterrest

def pearsonr(x, y) -> CorrelationCalcResult:
    """
    From stats.py. No changes apart from added error trapping, commenting out unused variable calculation,
    and trapping zero division error. And Py3 changes.
    -------------------------------------

    Calculates a Pearson correlation coefficient and the associated probability value.
    Taken from Heiman's Basic Statistics for the Behav. Sci (2nd), p.195.

    Usage: pearsonr(x,y) where x and y are equal-length lists
    Returns: Pearson's r value, two-tailed p-value
    """
    TINY = 1.0e-30
    if len(x) != len(y):
        raise ValueError("Input values not paired in pearsonr. Aborting.")
    n = len(x)
    try:
        x = list(map(float, x))
        y = list(map(float, y))
    except ValueError as e:
        raise Exception(f"Unable to calculate Pearson's R. {e}")
    # xmean = mean(x)
    # ymean = mean(y)
    r_num = n * (summult(x, y)) - sum(x) * sum(y)
    r_den = math.sqrt(
        (n * sum_squares(x) - square_of_sums(x))
        * (n * sum_squares(y) - square_of_sums(y))
    )
    if r_den == 0:
        raise ValueError("Inadequate variability - r_den is 0")
    r = (r_num / r_den)  ## denominator already a float
    df = n - 2
    t = r * math.sqrt(df / ((1.0 - r + TINY) * (1.0 + r + TINY)))
    try:
        prob = betai(0.5 * df, 0.5, df / float(df + t * t))
    except ZeroDivisionError:
        raise Exception("Unable to calculate Pearson's R. "
            "The df value and t are all 0 so trying to divide by df + t*t meant trying to divide by zero "
            "which is an error. "
            "But still worth looking at a scatterplot chart to assess the relationship.")
    return CorrelationCalcResult(r=r, p=prob, degrees_of_freedom=df)

def spearmansr(x, y, *, high_volume_ok=False) -> CorrelationCalcResult:
    """
    From stats.py. No changes apart from minor renaming (spearmanr -> spearmansr), addition of high_volume option,
    and trapping zero division error.
    -------------------------------------
    Calculates a Spearman rank-order correlation coefficient.
    Taken from Heiman's Basic Statistics for the Behav. Sci (1st), p.192.

    Usage:   spearmanr(x,y)      where x and y are equal-length lists
    Returns: Spearman's r, two-tailed p-value
    """
    if len(x) != len(y):
        raise ValueError("Input values not paired in spearmanr. Aborting.")
    n = len(x)
    rankx = rankdata(x, high_volume_ok=high_volume_ok)
    ranky = rankdata(y, high_volume_ok=True)  ## don't ask twice
    dsq = sumdiffsquared(rankx, ranky)
    rs = 1 - 6 * dsq / float(n * (n ** 2 - 1))
    try:
        t = rs * math.sqrt((n - 2) / ((rs + 1.0) * (1.0 - rs)))
    except ZeroDivisionError:
        raise Exception("Unable to calculate Spearman's R. The raw scores value (rs) was {rs} so trying to "
            "divide by 1.0-rs meant trying to divide by zero which is an error. But still worth looking at a "
            "scatterplot chart to assess the relationship.")
    df = n - 2
    probrs = betai(0.5 * df, 0.5, df / (df + t * t))  ## t already a float
    ## probability values for rs are from part 2 of the spearman function in
    ## Numerical Recipes, p.510.  They are close to tables, but not exact. (?)
    return CorrelationCalcResult(r=rs, p=probrs, degrees_of_freedom=df)

def spearmanr_details(sample_x, sample_y, *, high_volume_ok=False) -> SpearmansResult:
    initial_tbl = []
    n_x = len(sample_x)
    if n_x != len(sample_y):
        raise Exception(f"Different sample sizes ({n_x} vs {len(sample_y)})")
    rankx = rankdata(sample_x, high_volume_ok=high_volume_ok)
    x_and_rank = list(zip(sample_x, rankx))
    x_and_rank.sort()
    x2rank = dict(x_and_rank)
    ranky = rankdata(sample_y, high_volume_ok=True)
    y_and_rank = list(zip(sample_y, ranky))
    y_and_rank.sort()
    y2rank = dict(y_and_rank)
    n_cubed_minus_n = (n_x ** 3) - n_x
    diff_squareds = []
    for x, y in zip(sample_x, sample_y):
        x_rank = x2rank[x]
        y_rank = y2rank[y]
        diff = x_rank - y_rank
        diff_squared = diff ** 2
        diff_squareds.append(diff_squared)
        initial_tbl.append(SpearmansInitTbl(x, y, x_rank, y_rank, diff, diff_squared))
    tot_d_squared = sum(diff_squareds)
    pre_rho = (tot_d_squared * 6) / float(n_cubed_minus_n)
    rho = 1 - pre_rho
    if not (-1 <= pre_rho <= 1):
        raise Exception(f"Bad value for pre_rho of {pre_rho} (shouldn't have absolute value > 1)")
    details = SpearmansResult(initial_tbl=initial_tbl, x_and_rank=x_and_rank, y_and_rank=y_and_rank,
        n_x=n_x, n_cubed_minus_n=n_cubed_minus_n,
        tot_d_squared=round(tot_d_squared, 2), tot_d_squared_x_6=round(6 * tot_d_squared, 2),
        pre_rho=round(pre_rho, 4), rho=round(rho, 4)
    )
    return details

def rankdata(inlist, *, high_volume_ok=False):
    """
    From stats.py.

    Ranks the data in inlist, dealing with ties appropriately. Assumes
    a 1D inlist.  Adapted from Gary Perlman's |Stat ranksort.

    Args:
        high_volume_ok: only ever True if you don't mind if the calculation takes a long, long time as long
          as it completes.

    Usage:   rankdata(inlist)
    Returns: a list of length equal to inlist, containing rank scores
    """
    mylist = list(inlist)
    n = len(mylist)
    # -----------------------
    if n > MAX_RANK_DATA_VALS:
        if high_volume_ok:
            logger.info(f"High number of records in randata function (n:,) - will possibly run slowly")
        else:
            raise Exception("Too many records to run rankdata analysis")
    # -----------------------
    svec, ivec = shellsort(mylist)
    sumranks = 0
    dupcount = 0
    newlist = [0] * n
    for i in range(n):
        sumranks = sumranks + i
        dupcount = dupcount + 1
        if i == n - 1 or svec[i] != svec[i + 1]:
            averank = sumranks / float(dupcount) + 1
            for j in range(i - dupcount + 1, i + 1):
                newlist[ivec[j]] = averank
            sumranks = 0
            dupcount = 0
    return newlist


def shellsort(inlist):
    """
    From stats.py. No changes except Py3 changes.
    -------------------------------------
    Shellsort algorithm.  Sorts a 1D-list.

    Usage:   shellsort(inlist)
    Returns: sorted-inlist, sorting-index-vector (for original list)
    """
    n = len(inlist)
    svec = copy.deepcopy(inlist)
    ivec = list(range(n))
    gap = int(n // 2)  ## integer division needed
    while gap > 0:
        for i in range(gap, n):
            for j in range(i - gap, -1, -gap):
                while j >= 0 and svec[j] > svec[j + gap]:
                    temp = svec[j]
                    svec[j] = svec[j + gap]
                    svec[j + gap] = temp
                    itemp = ivec[j]
                    ivec[j] = ivec[j + gap]
                    ivec[j + gap] = itemp
        gap = int(gap // 2)  ## integer division needed
    ## svec is now sorted inlist, and ivec has the order svec[i] = vec[ivec[i]]
    return svec, ivec

def tiecorrect(rankvals):
    """
    From stats.py. No changes.
    -------------------------------------
    Corrects for ties in Mann Whitney U and Kruskal Wallis H tests. See
    Siegel, S. (1956) Nonparametric Statistics for the Behavioral Sciences.
    New York: McGraw-Hill. Code adapted from |Stat rankind.c code.

    Usage:   tiecorrect(rankvals)
    Returns: T correction factor for U or H
    """
    sorted_data, _posn = shellsort(rankvals)
    n = len(sorted_data)
    T = 0.0
    i = 0
    while i < n - 1:
        if sorted_data[i] == sorted_data[i + 1]:
            nties = 1
            while (i < n - 1) and (sorted_data[i] == sorted_data[i + 1]):
                nties = nties + 1
                i = i + 1
            T = T + nties ** 3 - nties
        i = i + 1
    T = T / float(n ** 3 - n)
    return 1.0 - T

def zprob(z):
    """
    From stats.py. No changes.
    -------------------------------------
    Returns the area under the normal curve 'to the left of' the given z value.
    Thus,
        - for z<0, zprob(z) = 1-tail probability
        - for z>0, 1.0-zprob(z) = 1-tail probability
        - for any z, 2.0*(1.0-zprob(abs(z))) = 2-tail probability
    Adapted from z.c in Gary Perlman's |Stat.

    Usage:   zprob(z)
    """
    Z_MAX = 6.0  ## maximum meaningful z-value
    if z == 0.0:
        x = 0.0
    else:
        y = 0.5 * math.fabs(z)
        if y >= (Z_MAX * 0.5):
            x = 1.0
        elif y < 1.0:
            w = y * y
            x = ((((((((0.000124818987 * w
                        - 0.001075204047) * w + 0.005198775019) * w
                      - 0.019198292004) * w + 0.059054035642) * w
                    - 0.151968751364) * w + 0.319152932694) * w
                  - 0.531923007300) * w + 0.797884560593) * y * 2.0
        else:
            y = y - 2.0
            x = (((((((((((((-0.000045255659 * y
                             + 0.000152529290) * y - 0.000019538132) * y
                           - 0.000676904986) * y + 0.001390604284) * y
                         - 0.000794620820) * y - 0.002034254874) * y
                       + 0.006549791214) * y - 0.010557625006) * y
                     + 0.011630447319) * y - 0.009279453341) * y
                   + 0.005353579108) * y - 0.002141268741) * y
                 + 0.000535310849) * y + 0.999936657524
    if z > 0.0:
        prob = ((x + 1.0) * 0.5)
    else:
        prob = ((1.0 - x) * 0.5)
    return prob

def azprob(z):
    """
    From stats.py. No changes except N->np.
    -------------------------------------
    Returns the area under the normal curve 'to the left of' the given z value.
    Thus,
        - for z < 0, zprob(z) = 1-tail probability
        - for z > 0, 1.0-zprob(z) = 1-tail probability
        - for any z, 2.0*(1.0-zprob(abs(z))) = 2 - tail probability
    Adapted from z.c in Gary Perlman's |Stat.  Can handle multiple dimensions.

    Usage:   azprob(z)    where z is a z-value
    """

    def yfunc(y_val):
        x_val = (((((((((((((-0.000045255659 * y_val
                         + 0.000152529290) * y_val - 0.000019538132) * y_val
                       - 0.000676904986) * y_val + 0.001390604284) * y_val
                     - 0.000794620820) * y_val - 0.002034254874) * y_val
                   + 0.006549791214) * y_val - 0.010557625006) * y_val
                 + 0.011630447319) * y_val - 0.009279453341) * y_val
               + 0.005353579108) * y_val - 0.002141268741) * y_val
             + 0.000535310849) * y_val + 0.999936657524
        return x_val

    def wfunc(w_val):
        x_val = ((((((((0.000124818987 * w_val
                    - 0.001075204047) * w_val + 0.005198775019) * w_val
                  - 0.019198292004) * w_val + 0.059054035642) * w_val
                - 0.151968751364) * w_val + 0.319152932694) * w_val
              - 0.531923007300) * w_val + 0.797884560593) * np.sqrt(w_val) * 2.0
        return x_val

    Z_MAX = 6.0  ## maximum meaningful z-value
    # x = np.zeros(z.shape, np.float_) # initialize
    y = 0.5 * np.fabs(z)
    x = np.where(np.less(y, 1.0), wfunc(y * y), yfunc(y - 2.0))  ## get x's
    x = np.where(np.greater(y, Z_MAX * 0.5), 1.0, x)  ## kill those with big Z
    prob = np.where(np.greater(z, 0), (x + 1) * 0.5, (1 - x) * 0.5)
    return prob

def scoreatpercentile(vals, percent):
    """
    From stats.py. No changes except renaming function, vars and params,
    printing only a warning if debug, splitting expressions into sub variables
    for better debugging, and not including uppermost values in top bin when
    using histogram function (i.e. the original stats.py behaviour).
    -------------------------------------
    Returns the score at a given percentile relative to the distribution given
    by vals.

    Usage:   scoreatpercentile(vals,percent)
    """
    if percent > 1:
        logger.debug('\nDividing percent>1 by 100 in scoreatpercentile().\n')
        percent = percent / 100.0
    targetcf = percent * len(vals)
    (bins, lrl,
     binsize, unused) = histogram(vals, inc_uppermost_val_in_top_bin=False)
    cumhist = cumsum(copy.deepcopy(bins))
    i = 0
    for i in range(len(cumhist)):
        if cumhist[i] >= targetcf:
            break
    logger.debug(bins)
    numer = (targetcf - cumhist[i - 1])
    denom = float(bins[i])
    score = binsize * (numer / denom) + (lrl + binsize * i)
    return score

def get_regression_result(xs: Sequence[float], ys: Sequence[float]) -> RegressionResult:
    try:
        slope, intercept, r, unused, unused = linregress(xs, ys)
    except Exception as e:
        raise Exception(f"Unable to get regression details. Orig error: {e}")
    x0 = min(xs)
    x1 = max(ys)
    y0 = (x0*slope) + intercept
    y1 = (x1*slope) + intercept
    return RegressionResult(slope=slope, intercept=intercept, r=r, x0=x0, y0=y0, x1=x1, y1=y1)

def mean(vals, *, high=False):
    """
    From stats.py. No changes except option of using Decimals instead of floats and adding error trapping.
    -------------------------------------
    Returns the arithmetic mean of the values in the passed list.

    Assumes a '1D' list, but will function on the 1st dim of an array(!).

    Usage:   mean(vals)
    """
    vals = list(vals)
    if not high:
        mysum = 0
        for val in vals:
            try:
                mysum += val
            except Exception:
                raise Exception(f'Unable to add "{val}" to running total.')
        mean_val = mysum / float(len(vals))
    else:
        tot = D('0')
        for val in vals:
            try:
                tot += n2d(val)
            except Exception:
                raise Exception(f'Unable to add "{val}" to running total.')
        mean_val = tot / len(vals)
    return mean_val

def amean(inarray, dimension=None, keepdims=0):
    """
    From stats.py.  No changes except renamed functions, and N->np.
    -------------------------------------
    Calculates the arithmetic mean of the values in the passed array.
    That is:  1/n * (x1 + x2 + ... + xn).  Defaults to ALL values in the
    passed array.  Use dimension=None to flatten array first.  REMEMBER: if
    dimension=0, it collapses over dimension 0 ('rows' in a 2D array) only, and
    if dimension is a sequence, it collapses over all specified dimensions.  If
    keepdims is set to 1, the resulting array will have as many dimensions as
    inarray, with only 1 'level' per dim that was collapsed over.

    Usage:   amean(inarray,dimension=None,keepdims=0)
    :return: arithmetic mean calculated over dim(s) in dimension
    """
    if inarray.dtype in [np.int_, np.short, np.ubyte]:
        inarray = inarray.astype(np.float_)
    if dimension is None:
        inarray = np.ravel(inarray)
        mysum = np.add.reduce(inarray)
        denom = float(len(inarray))
    elif isinstance(dimension, (int, float)):
        mysum = asum(inarray, dimension)
        denom = float(inarray.shape[dimension])
        if keepdims == 1:
            shp = list(inarray.shape)
            shp[dimension] = 1
            mysum = np.reshape(mysum, shp)
    else:  ## must be a TUPLE of dims to average over
        dims = list(dimension)
        dims.sort()
        dims.reverse()
        mysum = inarray * 1.0
        for dim in dims:
            mysum = np.add.reduce(mysum, dim)
        denom = np.array(
            np.multiply.reduce(np.take(inarray.shape, dims)), np.float_)
        if keepdims == 1:
            shp = list(inarray.shape)
            for dim in dims:
                shp[dim] = 1
            mysum = np.reshape(mysum, shp)
    return mysum / denom

def variance(vals, *, high=False):
    """
    From stats.py. No changes except option of using Decimals not floats.
    Plus trapping n=1 error (results in div by zero  with /n-1) and n=0.
    -------------------------------------
    Returns the variance of the values in the passed list using N-1
    for the denominator (i.e., for estimating population variance).

    Usage:   variance(vals)
    """
    n = len(vals)
    if n < 2:
        raise Exception('Need more than 1 value to calculate variance. '
                        f'Values supplied: {vals}')
    mn = mean(vals, high=high)
    deviations = [0] * len(vals)
    for i in range(len(vals)):
        val = vals[i]
        if high:
            val = n2d(val)
        deviations[i] = val - mn
    if not high:
        var = sum_squares(deviations) / float(n - 1)
    else:
        var = sum_squares(deviations, high=high) / n2d(n - 1)
    return var

def samplevar(vals, *, high=False):
    """
    From stats.py. No changes except option of using Decimals not floats.
    Plus trapping n=1 error (results in div by zero  with /n-1) and n=0.
    -------------------------------------
    Returns the variance of the values in the passed list using
    N for the denominator (i.e., DESCRIBES the sample variance only).

    Usage:   samplevar(vals)
    """
    n = len(vals)
    if n < 2:
        raise Exception('Need more than 1 value to calculate variance. '
                        f'Values supplied: {vals}')
    mn = mean(vals)
    deviations = []
    for item in vals:
        deviations.append(item - mn)
    if not high:
        var = sum_squares(deviations) / float(n)
    else:
        var = sum_squares(deviations, high=high) / n2d(n)
    return var

def stdev(vals, *, high=False):
    """
    From stats.py. No changes except option of using Decimals instead of floats.
    Uses renamed var (now variance).
    -------------------------------------
    Returns the standard deviation of the values in the passed list
    using N-1 in the denominator (i.e., to estimate population stdev).

    Usage:   stdev(vals)
    """
    try:
        if high:
            std_dev = n2d(math.sqrt(variance(vals, high=high)))
        else:
            std_dev = math.sqrt(variance(vals))
    except ValueError:
        raise Exception(
            'stdev - error getting square root. Negative variance value?')
    return std_dev

def samplestdev(vals, *, high=False):
    """
    From stats.py. No changes except option of using Decimals instead of floats.
    -------------------------------------
    Returns the standard deviation of the values in the passed list using
    N for the denominator (i.e., DESCRIBES the sample stdev only).

    Usage:   samplestdev(vals)
    """
    try:
        if high:
            std_dev = n2d(math.sqrt(samplevar(vals, high=high)))
        else:
            std_dev = math.sqrt(samplevar(vals))
    except ValueError:
        raise Exception(
            'samplestdev - error getting square root. Negative variance value?')
    return std_dev

def betai(a, b, x, *, high=False):
    """
    From stats.py.  No changes apart from adding detail to error message.
    -------------------------------------
    Returns the incomplete beta function:

        I-sub-x(a,b) = 1/B(a,b)*(Integral(0,x) of t^(a-1)(1-t)^(b-1) dt)

    where a,b>0 and B(a,b) = G(a)*G(b)/(G(a+b)) where G(a) is the gamma
    function of a.  The continued fraction formulation is implemented here,
    using the betacf function.  (Adapted from: Numerical Recipes in C.)

    Usage:   betai(a,b,x)
    """
    if high:
        a = n2d(a)
        b = n2d(b)
        x = n2d(x)
        zero = D('0')
        one = D('1')
        two = D('2')
    else:
        zero = 0.0
        one = 1.0
        two = 2.0
    if x < zero or x > one:
        raise ValueError(f'Bad x {x} in betai')
    if x == zero or x == one:
        bt = zero
    else:
        if high:
            bt_raw = math.exp(
                gammln(a + b, high=high)
                - gammln(a, high=high)
                - gammln(b, high=high)
                + a * n2d(math.log(x))
                + b * n2d(math.log(one - x)))
            bt = n2d(bt_raw)
        else:
            bt = math.exp(
                gammln(a + b, high=high)
                - gammln(a, high=high)
                - gammln(b, high=high)
                + a * math.log(x)
                + b * math.log(1.0 - x))
    if x < (a + one) / (a + b + two):
        if high:
            return bt * betacf(a, b, x, high=high) / a
        else:
            return bt * betacf(a, b, x) / float(a)
    else:
        try:
            if high:
                return one - bt * betacf(b, a, one - x, high=high) / b
            else:
                return 1.0 - bt * betacf(b, a, 1.0 - x) / float(b)
        except TypeError as e:
            raise Exception(
                f"Unable to return a result for the incomplete beta statistical function. Original error: {e}")

def sum_squares(vals, *, high=False):
    """
    From stats.py. No changes except option of using Decimal instead of float,
    and changes to variable names. Was called ss
    -------------------------------------
    Squares each value in the passed list, adds up these squares and returns the
    result.

    Usage:   sum_squares(vals)
    """
    if high:
        sum_of_squares = D('0')
        for val in vals:
            decimal_val = n2d(val)
            sum_of_squares += (decimal_val * decimal_val)
    else:
        sum_of_squares = 0
        for val in vals:
            sum_of_squares += (val * val)
    return sum_of_squares

def gammln(xx, *, high=False):
    """
    From stats.py.  No changes except using option of using Decimals not floats.
    -------------------------------------
    Returns the gamma function of xx.
        Gamma(z) = Integral(0,infinity) of t^(z-1)exp(-t) dt.
    (Adapted from: Numerical Recipes in C.)

    Usage:   gammln(xx)
    """
    if high:
        intone = D('1')
        one = D('1.0')
        fiveptfive = D('5.5')
        xx = n2d(xx)
        coeff = [
            D('76.18009173'),
            D('-86.50532033'),
            D('24.01409822'),
            D('-1.231739516'),
            D('0.120858003e-2'),
            D('-0.536382e-5'),
        ]
    else:
        intone = 1
        one = 1.0
        fiveptfive = 5.5
        coeff = [
            76.18009173,
            -86.50532033,
            24.01409822,
            -1.231739516,
            0.120858003e-2,
            -0.536382e-5,
        ]
    x = xx - one
    tmp = x + fiveptfive
    if high:
        tmp = tmp - (x + D('0.5')) * n2d(math.log(tmp))
    else:
        tmp = tmp - (x + 0.5) * math.log(tmp)
    ser = one
    for j in range(len(coeff)):
        x = x + intone
        ser = ser + coeff[j] / x
    if high:
        gammln_res = -tmp + n2d(math.log(D('2.50662827465') * ser))
    else:
        gammln_res = -tmp + math.log(2.50662827465 * ser)
    return gammln_res

def betacf(a, b, x, *, high=False):
    """
    From stats.py. No changes.
    -------------------------------------
    This function evaluates the continued fraction form of the incomplete
    Beta function, betai.  (Adapted from: Numerical Recipes in C.)

    Usage:   betacf(a,b,x)
    """
    if high:
        one = D('1')
        ITMAX = D('200')
        EPS = D('3.0e-7')
        a = n2d(a)
        b = n2d(b)
        x = n2d(x)
        bm = az = am = one
        qab = a + b
        qap = a + one
        qam = a - one
        bz = one - qab * x / qap
    else:
        one = 1.0
        ITMAX = 200
        EPS = 3.0e-7
        bm = az = am = one
        qab = a + b
        qap = a + one
        qam = a - one
        bz = one - qab * x / qap
    for i in range(int(ITMAX) + 1):
        if high:
            i = n2d(i)
        em = i + one
        tem = em + em
        d = em * (b - em) * x / ((qam + tem) * (a + tem))
        ap = az + d * am
        bp = bz + d * bm
        d = -(a + em) * (qab + em) * x / ((qap + tem) * (a + tem))
        app = ap + d * az
        bpp = bp + d * bz
        aold = az
        am = ap / bpp
        bm = bp / bpp
        az = app / bpp
        bz = one
        if abs(az - aold) < (EPS * abs(az)):
            return az
    logger.warning("Unable to return result for continued fraction form of the "
        "incomplete Beta statistical function (betacf) - a or b too big, or ITMAX too small.")

def summult(list1, list2):
    """
    From pstat.py.  No changes (apart from calling abut in existing module
        instead of pstat).
    Multiplies elements in list1 and list2, element by element, and
    returns the sum of all resulting multiplications.  Must provide equal
    length lists.

    Usage:   summult(list1,list2)
    """
    if len(list1) != len(list2):
        raise ValueError(u'Lists not equal length in summult.')
    s = 0
    for item1, item2 in abut(list1, list2):
        s = s + item1 * item2
    return s

def abut(source, *args):
    """
    From pstat.py.
    -------------------------------------
    Like the |Stat abut command.  It concatenates two lists side-by-side
    and returns the result.  '2D' lists are also accommodated for either argument
    (source or addon).  CAUTION:  If one list is shorter, it will be repeated
    until it is as long as the longest list.  If this behavior is not desired,
    use pstat.simpleabut().

    Usage:   abut(source, args)   where args=any # of lists
    Returns: a list of lists as long as the LONGEST list past, source on the
             'left', lists in <args> attached consecutively on the 'right'
    """
    if not isinstance(source, (list, tuple)):
        source = [source]
    for addon in args:
        if not isinstance(addon, (list, tuple)):
            addon = [addon]
        if len(addon) < len(source):  # is source list longer?
            if len(source) % len(addon) == 0:  # are they integer multiples?
                repeats = len(source) / len(addon)  # repeat addon n times
                origadd = copy.deepcopy(addon)
                for _i in range(int(repeats - 1)):
                    addon = addon + origadd
            else:
                repeats = len(source) / len(addon) + 1  # repeat addon x times,
                origadd = copy.deepcopy(addon)  # x is NOT an integer
                for _i in range(int(repeats - 1)):
                    addon = addon + origadd
                    addon = addon[0:len(source)]
        elif len(source) < len(addon):  # is addon list longer?
            if len(addon) % len(source) == 0:  # are they integer multiples?
                repeats = len(addon) / len(source)  # repeat source n times
                origsour = copy.deepcopy(source)
                for _i in range(int(repeats - 1)):
                    source = source + origsour
            else:
                repeats = len(addon) / len(source) + 1  # repeat source x times,
                origsour = copy.deepcopy(source)  # x is NOT an integer
                for _i in range(int(repeats - 1)):
                    source = source + origsour
                source = source[0:len(addon)]
        source = simpleabut(source, addon)
    return source

def simpleabut(source, addon):
    """
    From pstat.py.  No changes except type test updated.
    -------------------------------------
    Concatenates two lists as columns and returns the result.  '2D' lists
    are also accommodated for either argument (source or addon).  This DOES NOT
    repeat either list to make the 2 lists of equal length.  Beware of list
    pairs with different lengths ... the resulting list will be the length of
    the FIRST list passed.

    Usage: simpleabut(source,addon)  where source, addon=list (or list-of-lists)
    Returns: a list of lists as long as source, with source on the 'left' and addon on the 'right'
    """
    if not isinstance(source, (list, tuple)):
        source = [source]
    if not isinstance(addon, (list, tuple)):
        addon = [addon]
    minlen = min(len(source), len(addon))
    mylist = copy.deepcopy(source)  # start abut process
    if not isinstance(source[0], (list, tuple)):
        if not isinstance(addon[0], (list, tuple)):
            for i in range(minlen):
                mylist[i] = [source[i]] + [addon[i]]  # source/addon = column
        else:
            for i in range(minlen):
                mylist[i] = [source[i]] + addon[i]  # addon=list-of-lists
    else:
        if not isinstance(addon[0], (list, tuple)):
            for i in range(minlen):
                mylist[i] = source[i] + [addon[i]]  # source=list-of-lists
        else:
            for i in range(minlen):
                mylist[i] = source[i] + addon[i]  # source/addon = list-of-lists
    source = mylist
    return source

def square_of_sums(inlist):
    """
    From stats.py.  No changes.
    -------------------------------------
    Adds the values in the passed list, squares the sum, and returns
    the result.

    Usage:   square_of_sums(inlist)
    Returns: sum(inlist[i])**2
    """
    s = sum(inlist)
    return float(s) * s

def sumdiffsquared(x, y):
    """
    From stats.py.  No changes.
    -------------------------------------
    Takes pairwise differences of the values in lists x and y, squares
    these differences, and returns the sum of these squares.

    Usage:   sumdiffsquared(x,y)
    Returns: sum[(x[i]-y[i])**2]
    """
    sds = 0
    for i in range(len(x)):
        sds = sds + (x[i] - y[i]) ** 2
    return sds

def chisqprob(chisq, df):
    """
    From stats.py.
    -------------------------------------
    Returns the (1-tailed) probability value associated with the provided
    chi-square value and df.  Adapted from chisq.c in Gary Perlman's |Stat.

    Usage:   chisqprob(chisq,df)
    """
    BIG = 20.0

    def ex(x):
        BIG_in_ex = 20.0
        if x < -BIG_in_ex:
            return 0.0
        else:
            return math.exp(x)

    if chisq <= 0 or df < 1:
        return 1.0
    a = 0.5 * chisq
    if df % 2 == 0:
        even = 1
    else:
        even = 0
    y = None
    if df > 1:
        y = ex(-a)
    if even:
        if y is None:
            raise Exception(f"df {df} is an even number but y is None")
        else:
            s = y
    else:
        s = 2.0 * zprob(-math.sqrt(chisq))
    if df > 2:
        chisq = 0.5 * (df - 1.0)
        if even:
            z = 1.0
        else:
            z = 0.5
        if a > BIG:
            if even:
                e = 0.0
            else:
                e = math.log(math.sqrt(math.pi))
            c = math.log(a)
            while z <= chisq:
                e = math.log(z) + e
                s = s + ex(c * z - a - e)
                z = z + 1.0
            return s
        else:
            if even:
                e = 1.0
            else:
                e = 1.0 / math.sqrt(math.pi) / math.sqrt(a)
            c = 0.0
            while z <= chisq:
                e = e * (a / float(z))
                c = c + e
                z = z + 1.0
            return c * y + s
    else:
        return s

def fprob(dfnum, dfden, F, *, high=False):
    """
    From stats.py. No changes except uses Decimals instead of floats.
    -------------------------------------
    Returns the (1-tailed) significance level (p-value) of an F
    statistic given the degrees of freedom for the numerator (dfR-dfF) and
    the degrees of freedom for the denominator (dfF).

    Usage:   fprob(dfnum, dfden, F) where usually dfnum=dfbn, dfden=dfwn
    """
    if high:
        dfnum = n2d(dfnum)
        dfden = n2d(dfden)
        F = n2d(F)
        a = D('0.5') * dfden
        b = D('0.5') * dfnum
        x = dfden / (dfden + dfnum * F)
        logger.debug('a: %s' % a)
        logger.debug('b: %s' % b)
        logger.debug('x: %s' % x)
        p = betai(a, b, x, high=high)
    else:
        p = betai(0.5 * dfden, 0.5 * dfnum, dfden / float(dfden + dfnum * F), high=high)
    return p

def moment(a, moment_val=1, dimension=None):
    """
    From stats.py.  No changes except renamed function, N->np.
    ------------------------------------
    Calculates the nth moment about the mean for a sample (defaults to the
    1st moment).  Generally used to calculate coefficients of skewness and
    kurtosis.  Dimension can equal None (ravel array first), an integer
    (the dimension over which to operate), or a sequence (operate over
    multiple dimensions).

    Usage:   moment(a, moment=1, dimension=None)
    Returns: appropriate moment along given dimension
    """
    if dimension is None:
        a = np.ravel(a)
        dimension = 0
    if moment_val == 1:
        return 0.0
    else:
        mn = amean(a, dimension, 1)  ## 1=keepdims
        s = np.power((a - mn), moment_val)
        return amean(s, dimension)

def skew(a, dimension=None):
    """
    From stats.py.  No changes except renamed function, N->np, print updated.
    ------------------------------------
    Returns the skewness of a distribution (normal ==> 0.0; >0 means extra
    weight in left tail).  Use skewtest() to see if it's close enough.
    Dimension can equal None (ravel array first), an integer (the
    dimension over which to operate), or a sequence (operate over multiple
    dimensions).

    Usage:   skew(a, dimension=None)
    Returns: skew of vals in a along dimension, returning ZERO where all vals
    equal
    """
    denom = np.power(moment(a, 2, dimension), 1.5)
    zero = np.equal(denom, 0)
    if type(denom) == np.ndarray and asum(zero) != 0:
        logger.info(f'Number of zeros in askew: {asum(zero)}')
    denom = denom + zero  ## prevent divide-by-zero
    return np.where(zero, 0, moment(a, 3, dimension) / denom)

def asum(a, dimension=None, keepdims=0):
    """
    From stats.py.  No changes except N->np and type checks updated.
    ------------------------------------
    An alternative to the Numeric.add.reduce function, which allows one to
    (1) collapse over multiple dimensions at once, and/or (2) to retain
    all dimensions in the original array (squashing one down to size.
    Dimension can equal None (ravel array first), an integer (the
    dimension over which to operate), or a sequence (operate over multiple
    dimensions).  If keepdims=1, the resulting array will have as many
    dimensions as the input array.

    Usage: asum(a, dimension=None, keepdims=0)
    Returns: array summed along 'dimension'(s), same _number_ of dims if
    keepdims=1
    """
    if type(a) == np.ndarray and a.dtype in [np.int_, np.short, np.ubyte]:
        a = a.astype(np.float_)
    if dimension is None:
        s = np.sum(np.ravel(a))
    elif isinstance(dimension, (int, float)):
        s = np.add.reduce(a, dimension)
        if keepdims == 1:
            shp = list(a.shape)
            shp[dimension] = 1
            s = np.reshape(s, shp)
    else:  ## must be a SEQUENCE of dims to sum over
        dims = list(dimension)
        dims.sort()
        dims.reverse()
        s = a * 1.0
        for dim in dims:
            s = np.add.reduce(s, dim)
        if keepdims == 1:
            shp = list(a.shape)
            for dim in dims:
                shp[dim] = 1
            s = np.reshape(s, shp)
    return s

def cumsum(inlist):
    """
    From stats.py. No changes except renamed function.
    ------------------------------------
    Returns a list consisting of the cumulative sum of the items in the
    passed list.

    Usage:   cumsum(inlist)
    """
    newlist = copy.deepcopy(inlist)
    for i in range(1, len(newlist)):
        newlist[i] = newlist[i] + newlist[i - 1]
    return newlist

def kurtosis(a, dimension=None):
    """
    From stats.py.  No changes except renamed function, N->np, print updated,
    and subtracted 3. Using Fisher's definition, which subtracts 3.0 from the
    result to give 0.0 for a normal distribution.
    ------------------------------------
    Returns the kurtosis of a distribution (normal ==> 3.0; >3 means
    heavier in the tails, and usually more peaked).  Use kurtosistest()
    to see if it's close enough.  Dimension can equal None (ravel array
    first), an integer (the dimension over which to operate), or a
    sequence (operate over multiple dimensions).

    Usage:   kurtosis(a,dimension=None)
    Returns: kurtosis of values in a along dimension, and ZERO where all vals
    equal
    """
    denom = np.power(moment(a, 2, dimension), 2)
    zero = np.equal(denom, 0)
    if type(denom) == np.ndarray and asum(zero) != 0:
        logger.info(f'Number of zeros in akurtosis: {asum(zero)}')
    denom = denom + zero  ## prevent divide-by-zero
    return (np.where(zero, 0, moment(a, 4, dimension) / denom)
            - FISHER_KURTOSIS_ADJUSTMENT)

def achisqprob(chisq, df) -> float:
    """
    Returns the (1-tail) probability value associated with the provided
    chi-square value and df.  Heavily modified from chisq.c in Gary Perlman's
    |Stat.  Can handle multiple dimensions.

    Usage: chisqprob(chisq,df)    chisq=chisquare stat., df=degrees of freedom
    """
    BIG = 200.0

    def ex(x):
        BIG_in_ex = 200.0
        exponents = np.where(np.less(x, -BIG_in_ex), -BIG_in_ex, x)
        return np.exp(exponents)

    if type(chisq) != np.ndarray:
        chisq = np.array([chisq])
    if df < 1:
        return np.ones(chisq.shape, np.float)
    probs = np.zeros(chisq.shape, np.float_)
    probs = np.where(np.less_equal(chisq, 0), 1.0, probs)  ##set prob=1 for chisq<0
    a = 0.5 * chisq
    y = None
    if df > 1:
        y = ex(-a)
    if df % 2 == 0:
        even = 1
        if y is None:
            raise Exception(f"df {df} is an even number but y is None")
        else:
            s = y * 1
        s2 = s * 1
    else:
        even = 0
        s = 2.0 * azprob(-np.sqrt(chisq))
        s2 = s * 1
    if df > 2:
        chisq = 0.5 * (df - 1.0)
        if even:
            z = np.ones(probs.shape, np.float_)
        else:
            z = 0.5 * np.ones(probs.shape, np.float_)
        if even:
            e = np.zeros(probs.shape, np.float_)
        else:
            e = np.log(np.sqrt(np.pi)) * np.ones(probs.shape, np.float_)
        c = np.log(a)
        mask = np.zeros(probs.shape)
        a_big = np.greater(a, BIG)
        a_big_frozen = -1 * np.ones(probs.shape, np.float_)
        totalelements = np.multiply.reduce(np.array(probs.shape))
        while asum(mask) != totalelements:
            e = np.log(z) + e
            s = s + ex(c * z - a - e)
            z = z + 1.0
            #            print (z, e, s)
            newmask = np.greater(z, chisq)
            a_big_frozen = np.where(
                newmask * np.equal(mask, 0) * a_big, s, a_big_frozen)
            mask = np.clip(newmask + mask, 0, 1)
        if even:
            z = np.ones(probs.shape, np.float_)
            e = np.ones(probs.shape, np.float_)
        else:
            z = 0.5 * np.ones(probs.shape, np.float_)
            e = 1.0 / np.sqrt(np.pi) / np.sqrt(a) * np.ones(probs.shape,
                                                            np.float_)
        c = 0.0
        mask = np.zeros(probs.shape)
        a_notbig_frozen = -1 * np.ones(probs.shape, np.float_)
        while asum(mask) != totalelements:
            e = e * (a / z.astype(np.float_))
            c = c + e
            z = z + 1.0
            #            print ('#2', z, e, c, s, c*y+s2)
            newmask = np.greater(z, chisq)
            a_notbig_frozen = np.where(
                newmask * np.equal(mask, 0) * (1 - a_big), c * y + s2, a_notbig_frozen)
            mask = np.clip(newmask + mask, 0, 1)
        probs = np.where(
            np.equal(probs, 1), 1,
            np.where(np.greater(a, BIG), a_big_frozen, a_notbig_frozen))
        result = probs[0]
    else:
        result = s[0]
    return result

#####################################
########  NORMALITY TESTS  ##########
#####################################

def skewtest(a, dimension=None):
    """
    From stats.py.  No changes except renamed function, N->np, returns skew
    value, and handles negative number as input to square root.
    ------------------------------------
    Tests whether the skew is significantly different from a normal
    distribution. Dimension can equal None (ravel array first), an integer (the
    dimension over which to operate), or a sequence (operate over multiple
    dimensions).

    Usage:   skewtest(a,dimension=None)
    Returns: z-score and 2-tail z-probability
    """
    if dimension is None:
        a = np.ravel(a)
        dimension = 0
    b2 = skew(a, dimension)
    n = float(a.shape[dimension])
    rooted_var0 = ((n + 1) * (n + 3)) / (6.0 * (n - 2))
    y = b2 * np.sqrt(rooted_var0)
    beta2 = (3.0 * (n * n + 27 * n - 70) * (n + 1) * (n + 3)) / ((n - 2.0) * (n + 5) * (n + 7) * (n + 9))
    rooted_var1 = 2 * (beta2 - 1)
    W2 = -1 + np.sqrt(rooted_var1)
    rooted_var2 = np.log(np.sqrt(W2))
    delta = 1 / np.sqrt(rooted_var2)
    rooted_var3 = 2 / (W2 - 1)
    alpha = np.sqrt(rooted_var3)
    y = np.where(y == 0, 1, y)
    rooted_var4 = (y / alpha) ** 2 + 1
    if rooted_var4 >= 0:
        Z = delta * np.log(y / alpha + np.sqrt(rooted_var4))
        c = (1.0 - azprob(Z)) * 2
    else:
        Z = None
        c = None
    return Z, c, float(b2)

def kurtosistest(a, dimension=None):
    """
    From stats.py.  No changes except renamed function, N->np, print updated,
    returns kurtosis value and add 3 to value to restore to what is expected
    here (removed in kurtosis as per Fisher so normal = 0), and trapping of zero
    division error.
    ------------------------------------
    Tests whether a dataset has normal kurtosis (i.e.,
    kurtosis=3(n-1)/(n+1)) Valid only for n>20.  Dimension can equal None
    (ravel array first), an integer (the dimension over which to operate),
    or a sequence (operate over multiple dimensions).

    Usage:   kurtosistest(a,dimension=None)
    Returns: z-score and 2-tail z-probability, returns 0 for bad pixels
    """
    if dimension is None:
        a = np.ravel(a)
        dimension = 0
    n = float(a.shape[dimension])
    if n < 20:
        logger.warning(f'kurtosistest only valid for n>=20 ... continuing anyway, n={n}')
    kurt = kurtosis(a, dimension)  ## I changed the kurtosis code to subtract the Fischer Adjustment (3)
    b2 = kurt + FISHER_KURTOSIS_ADJUSTMENT  ## added so b2 is exactly as it would have been in the original stats.py
    E = 3.0 * (n - 1) / (n + 1)
    varb2 = 24.0 * n * (n - 2) * (n - 3) / ((n + 1) * (n + 1) * (n + 3) * (n + 5))
    x = (b2 - E) / np.sqrt(varb2)
    try:
        sqrtbeta1 = 6.0 * (n * n - 5 * n + 2) / ((n + 7) * (n + 9)) * np.sqrt((6.0 * (n + 3) * (n + 5)) /
                                                                              (n * (n - 2) * (n - 3)))
    except ZeroDivisionError:
        raise Exception('Unable to calculate kurtosis test. Zero division error')
    A = 6.0 + 8.0 / sqrtbeta1 * (2.0 / sqrtbeta1 + np.sqrt(1 + 4.0 / (sqrtbeta1 ** 2)))
    term1 = 1 - 2 / (9.0 * A)
    denom = 1 + x * np.sqrt(2 / (A - 4.0))
    denom = np.where(np.less(denom, 0), 99, denom)
    term2 = np.where(np.equal(denom, 0), term1, np.power((1 - 2.0 / A) / denom, 1 / 3.0))
    Z = (term1 - term2) / np.sqrt(2 / (9.0 * A))
    Z = np.where(np.equal(denom, 99), 0, Z)
    return Z, (1.0 - azprob(Z)) * 2, kurt  ## I want to return the Fischer Adjusted kurtosis, not b2

# noinspection PyBroadException
def normal_test(a, dimension=None) -> NormalTestResult:
    """NormalTestResult
    From stats.py.  No changes except renamed function, some vars names, N->np,
    included in return the results for skew and kurtosis, and handled errors in
    individual parts e.g. skew.

    This function tests the null hypothesis that a sample comes from a normal
    distribution. It is based on D'Agostino and Pearson's test that combines
    skew and kurtosis to produce an omnibus test of normality.

    D'Agostino, R. B. and Pearson, E. S. (1971),
    "An Omnibus Test of Normality for Moderate and Large Sample Size," Biometrika, 58, 341-348

    D'Agostino, R. B. and Pearson, E. S. (1973),
    "Testing for departures from Normality," Biometrika, 60, 613-622.
    ------------------------------------
    Tests whether skew and/OR kurtosis of dataset differs from normal
    curve.  Can operate over multiple dimensions.  Dimension can equal
    None (ravel array first), an integer (the dimension over which to
    operate), or a sequence (operate over multiple dimensions).

    Usage:   normaltest(a,dimension=None)
    Returns: z-score and 2-tail probability
    """
    if dimension is None:
        a = np.ravel(a)
        dimension = 0
    try:
        z_skew, unused, c_skew = skewtest(a, dimension)
    except Exception:
        z_skew = None
        c_skew = None
    try:
        z_kurtosis, unused, c_kurtosis = kurtosistest(a, dimension)
    except Exception:
        z_kurtosis = None
        c_kurtosis = None
    try:
        k2 = np.power(z_skew, 2) + np.power(z_kurtosis, 2)
        p = achisqprob(k2, 2)
    except Exception:
        k2 = None
        p = None
    return NormalTestResult(k2, p, c_skew, z_skew, c_kurtosis, z_kurtosis)

## misc

def obrientransform(*args):
    """
    From stats.py. One big change - reset TINY to be 1e-7 rather than 1e-10.

    Always "failed to converge" if values were above about 1000.  Unable to
    determine reason for such a tiny threshold of difference.

    No other changes except renamed function and renamed var to variance, plus
    raise ValueError as soon as check = 0 without continuing to pointlessly loop
    through other items. Also raise useful exception if about to have a
    ZeroDivisionError because t3 = 0.

    Also n[j] is cast as int when used in range. And updated error message and
    desc text. And added debug print.
    ------------------------------------
    Computes a transform on input data (any number of columns). Used to test for
    homogeneity of variance prior to running one-way stats. Each array in *args
    is one level of a factor. If an F_oneway() run on the transformed data and
    found significant, variances are unequal. From Maxwell and Delaney, p.112.

    Usage:   obrientransform(*args)
    Returns: transformed data for use in an ANOVA
    """
    TINY = 1e-7  ## 1e-10 was original value
    k = len(args)
    n = [0.0] * k
    v = [0.0] * k
    m = [0.0] * k
    nargs = []
    for i in range(k):
        nargs.append(copy.deepcopy(args[i]))
        n[i] = float(len(nargs[i]))
        if n[i] < 3:
            raise Exception(u'Must have at least 3 values in each sample to run'
                            u' obrientransform.\n%s' % nargs[i])
        v[i] = variance(nargs[i])
        m[i] = mean(nargs[i])
    for j in range(k):
        for i in range(int(n[j])):
            t1 = (n[j] - 1.5) * n[j] * (nargs[j][i] - m[j]) ** 2
            t2 = 0.5 * v[j] * (n[j] - 1.0)
            t3 = (n[j] - 1.0) * (n[j] - 2.0)
            if t3 == 0:
                raise Exception(
                    'Unable to calculate obrientransform because t3 is zero.')
            nargs[j][i] = (t1 - t2) / float(t3)
    ## Check for convergence before allowing results to be returned
    for j in range(k):
        if v[j] - mean(nargs[j]) > TINY:
            logger.debug(f'Diff: {v[j] - mean(nargs[j])}')
            logger.debug(f'\nv[j]: {repr(v[j])}')
            logger.debug(f'\nnargs[j]: {nargs[j]}')
            logger.debug(f'\nmean(nargs[j]): {repr(mean(nargs[j]))}')
            raise ValueError('Lack of convergence in obrientransform.')
    return nargs

def sim_variance(samples: Sequence[Sequence[float]], *, threshold=0.05, high=False) -> tuple[bool, float]:
    """
    From stats.py. From inside lpaired. F_oneway changed to anova and no need to
    column extract to get transformed samples.

    Plus not only able to use 0.05 as threshold. Also changed return.
    ------------------------------------
    Comparing variances.

    Using O'BRIEN'S TEST FOR HOMOGENEITY OF VARIANCE, Maxwell & delaney, p.112
    """
    r = obrientransform(*samples)
    transformed_samples = [r[0], r[1]]
    p = anova_p_only(transformed_samples, high=high)
    is_similar = (p >= threshold)
    return is_similar, p

def normpdf_from_old_mpl(x, *args):
    """
    Return the normal pdf evaluated at *x*; args provides *mu*, *sigma*
    """
    mu, sigma = args
    return 1. / (np.sqrt(2 * np.pi) * sigma) * np.exp(-0.5 * (1. / sigma * (x - mu))**2)

def get_normal_ys(vals, bins):
    """
    Get np array of y values for normal distribution curve with given values
    and bins.
    """
    if len(vals) < 2:
        raise Exception('Need multiple values to calculate normal curve.')
    mu = mean(vals)
    sigma = stdev(vals)
    logger.debug(f"bins={bins}, mu={mu}, sigma={sigma}")
    if sigma == 0:
        raise Exception(
            'Unable to get y-axis values for normal curve with a sigma of 0.')
    norm_ys = list(normpdf_from_old_mpl(bins, mu, sigma))
    return norm_ys
