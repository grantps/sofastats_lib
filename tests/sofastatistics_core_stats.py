from collections import defaultdict, namedtuple, OrderedDict
import copy
import decimal
import logging
import math

import numpy as np

from sofastatistics import (
    basic_lib as b, my_globals as mg, lib, my_exceptions, getdata)

D = decimal.Decimal
decimal.getcontext().prec = 200

SpearmansInitTbl = namedtuple(
    'SpearmansInitTbl', 'x, y, rank_x, rank_y, diff, diff_squared')

"""
Don't use dd - this and any other modules we wish to run as a standalone script
must have dbe, db etc explicitly fed in. If the script is built by the GUI, the
GUI reads dd values and feeds them into the script.

The "minus 3" at the end of this formula is often explained as a correction to
make the kurtosis of the normal distribution equal to zero. Another reason can
be seen by looking at the formula for the kurtosis of the sum of random
variables. ... This formula would be much more complicated if kurtosis were
defined just as μ4 / σ4 (without the minus 3).
http://en.wikipedia.org/wiki/Kurtosis
"""
FISHER_KURTOSIS_ADJUSTMENT = 3.0

def saw_toothing(y_vals, period, start_idx=0):
    """
    Sawtoothing is where every nth bin has values, but the others have none.
    """
    period_vals = y_vals[start_idx::period]
    sum_period = sum(period_vals)
    sum_all = sum(y_vals)
    sum_non_period = sum_all - sum_period
    return sum_non_period == 0

def fix_sawtoothing(raw_data, n_bins, y_vals, start, bin_width):
    """
    Look for sawtoothing on commonly found periods (5 and 2). If found, reduce
    bins until problem gone or too few bins to keep shrinking.
    """
    while n_bins > 5:
        if saw_toothing(y_vals, period=5):
            shrink_factor = 5.0
        elif saw_toothing(y_vals, period=2):
            shrink_factor = 2.0
        elif saw_toothing(y_vals, period=2, start_idx=1):
            shrink_factor = 2.0
        else:
            break
        n_bins = int(math.ceil(n_bins/shrink_factor))
        (y_vals, start,
            bin_width, unused) = histogram(raw_data, n_bins)
        logging.debug(y_vals)
    return y_vals, start, bin_width

def normpdf_from_old_mpl(x, *args):
    "Return the normal pdf evaluated at *x*; args provides *mu*, *sigma*"
    mu, sigma = args
    return 1./(np.sqrt(2*np.pi)*sigma)*np.exp(-0.5 * (1./sigma*(x - mu))**2)

def get_normal_ys(vals, bins):
    """
    Get np array of y values for normal distribution curve with given values
    and bins.
    """
    if len(vals) < 2:
        raise Exception(_('Need multiple values to calculate normal curve.'))
    mu = mean(vals)
    sigma = stdev(vals)
    logging.debug(f"bins={bins}, mu={mu}, sigma={sigma}")
    if sigma == 0:
        raise Exception(
            'Unable to get y-axis values for normal curve with a sigma of 0.')
    norm_ys = normpdf_from_old_mpl(bins, mu, sigma)
    return norm_ys

def get_regression_dets(list_x, list_y):
    try:
        slope, intercept, r, unused, unused = linregress(list_x, list_y)
    except Exception as e:
        raise Exception(f'Unable to get regression details. Orig error: {e}')
    x0 = min(list_x)
    x1 = max(list_x)
    y0 = (x0*slope) + intercept
    y1 = (x1*slope) + intercept
    return slope, intercept, r, y0, y1

def get_indiv_regression_msg(list_x, list_y, series_lbl):
    try:
        slope, intercept, unused, unused, unused = linregress(list_x, list_y)
    except Exception:
        return mg.REGRESSION_ERR
    dp = 3
    indiv_regression_msg = (
        f'Slope: {round(slope, dp)}; Intercept: {round(intercept, dp)}')
    if series_lbl:
        indiv_regression_msg = f'{series_lbl}: {indiv_regression_msg}'
    return indiv_regression_msg

def unique(sample):
    """
    From pstat.py. Renamed inlist to sample.
    -------------------------------------
    Returns all unique items in the passed list.  If the a list-of-lists
    is passed, unique LISTS are found (i.e., items in the first dimension are
    compared).

    Usage:   unique (sample)
    Returns: the unique elements (or rows) in sample
    """
    uniques = []
    for item in sample:
        if item not in uniques:
            uniques.append(item)
    return uniques

def mode(sample):
    """
    From stats.py. Renamed inlist to sample.
    -------------------------------------
    Returns a list of the modal (most common) score(s) in the passed list. If
        there is more than one such score, all are returned. The bin-count for
        the mode(s) is also returned.

    Usage:   mode(sample)
    Returns: bin-count for mode(s), a list of modal value(s)
    """
    scores = unique(sample)
    scores.sort()
    freq = []
    for item in scores:
        freq.append(sample.count(item))
    maxfreq = max(freq)
    mode = []
    stillmore = 1
    while stillmore:
        try:
            indx = freq.index(maxfreq)
            mode.append(scores[indx])
            del freq[indx]
            del scores[indx]
        except ValueError:
            stillmore=0
    return maxfreq, mode

def get_freqs(sample):
    """
    From a given data sample, return a sorted list of values and frequencies.
    Useful for line plotting.
    NB when in Python 2.7 or 3.1+ use collection Counter
    http://docs.python.org/dev/py3k/library/collections.html#collections.Counter
    """
    d = defaultdict(int)
    xs = []
    ys = []
    for item in sample:
        d[item] += 1
    keys = sorted(d.keys())
    for key in keys:
        xs.append(key)
        ys.append(d[key])
    return xs, ys

def get_list(dbe, cur, tbl, tbl_filt, flds, fld_measure,
        fld_filter, filter_val):
    """
    Get list of non-missing values in field. Must return list of floats. SQLite
    sometimes returns strings even though REAL data type. Not known why. Used,
    for example, in the independent samples t-test.

    :param str fld_filter: the grouping variable
    """
    fld_val_clause = getdata.make_fld_val_clause(
        dbe, flds, fld_filter, filter_val)
    objqtr = getdata.get_obj_quoter_func(dbe)
    unused, and_tbl_filt = lib.FiltLib.get_tbl_filts(tbl_filt)
    SQL_get_list = f"""SELECT {objqtr(fld_measure)}
        FROM {getdata.tblname_qtr(dbe, tbl)}
        WHERE {objqtr(fld_measure)} IS NOT NULL
        AND {fld_val_clause + and_tbl_filt}"""
    logging.debug(SQL_get_list)
    cur.execute(SQL_get_list)
    ## SQLite sometimes returns strings even if REAL
    lst = [float(x[0]) for x in cur.fetchall()]
    if len(lst) < 2:
        raise my_exceptions.TooFewValsInSamplesForAnalysis(fld_filter,
            filter_val)
    return lst

def get_paired_data(dbe, cur, tbl, tbl_filt, fld_a, fld_b, unique=False):
    """
    For each field, returns a list of all non-missing values where there is also
    a non-missing value in the other field. Used in, for example, the paired
    samples t-test.

    :param bool unique: if True only look at unique pairs. Useful for scatter
     plotting.
    """
    objqtr = getdata.get_obj_quoter_func(dbe)
    unused, and_tbl_filt = lib.FiltLib.get_tbl_filts(tbl_filt)
    fld_a_str = objqtr(fld_a)
    fld_b_str = objqtr(fld_b)
    tbl_str = getdata.tblname_qtr(dbe, tbl)
    if unique:
        SQL_get_pairs = f"""\
        SELECT {fld_a_str}, {fld_b_str}
        FROM {tbl_str}
        WHERE {fld_a_str} IS NOT NULL
        AND {fld_b_str} IS NOT NULL {and_tbl_filt}
        GROUP BY {fld_a_str}, {fld_b_str}"""
    else:
        SQL_get_pairs = f"""\
        SELECT {fld_a_str}, {fld_b_str}
        FROM {tbl_str}
        WHERE {fld_a_str} IS NOT NULL
        AND {fld_b_str} IS NOT NULL {and_tbl_filt}"""
    cur.execute(SQL_get_pairs)
    data_tups = cur.fetchall()
    ## SQLite sometimes returns strings even if REAL
    lst_a = [float(x[0]) for x in data_tups]
    lst_b = [float(x[1]) for x in data_tups]
    return lst_a, lst_b, data_tups

def get_val_quoter(dbe, flds, fld, val):
    """
    Get function for quoting values according to field type and value.

    NB "5" is a string and must be quoted otherwise we will be matching 5s
    instead.
    """
    num = True
    if not flds[fld][mg.FLD_BOLNUMERIC]:
        num = False
    elif dbe == mg.DBE_SQLITE:
        if not lib.TypeLib.is_basic_num(val):
            num = False
    if num:
        val_quoter = lambda s: s
    else:
        val_quoter = getdata.get_val_quoter_func(dbe)
    return val_quoter

def get_unique_dim_vals(vals_used, dbe, flds, fld):
    """
    Get unique values for dimension (row or column) in form ready to use. And
    check there are no excessively long labels.
    """
    if dbe == mg.DBE_SQLITE and flds[fld][mg.FLD_BOLNUMERIC]:
        ## SQLite sometimes returns strings even if REAL
        try:
            vals = [float(x[0]) for x in vals_used]
            return vals
        except Exception:
            pass  ## leave them as strings
    vals = []
    for row_tup in vals_used:
        row_val = row_tup[0]
        if len(row_val) > mg.MAX_VAL_LEN_IN_SQL_CLAUSE:
            raise my_exceptions.CategoryTooLong(fld)
        vals.append(row_val)
    return vals

def get_obs_exp(dbe, cur, tbl, tbl_filt,
        where_tbl_filt, and_tbl_filt, flds,
        fld_a, fld_b):
    """
    Get list of observed and expected values ready for inclusion in Pearson's
    Chi Square test.

    NB must return 0 if nothing. All cells must be filled.

    Returns lst_obs, lst_exp, min_count, perc_cells_lt_5, df.

    NB some dbes return integers and some return Decimals.

    The lists are b within a e.g. a1b1, a1b2, a1b3, a2b1, a2b2 ...
    """
    objqtr = getdata.get_obj_quoter_func(dbe)
    qtbl = getdata.tblname_qtr(dbe, tbl)
    qfld_a = objqtr(fld_a)
    qfld_b = objqtr(fld_b)
    ## A) get ROW vals used ***********************
    SQL_row_vals_used = f"""\
    SELECT {qfld_a}
    FROM {qtbl}
    WHERE {qfld_b} IS NOT NULL AND {qfld_a} IS NOT NULL
    {and_tbl_filt}
    GROUP BY {qfld_a}
    ORDER BY {qfld_a}
    """
    cur.execute(SQL_row_vals_used)
    row_vals_used = cur.fetchall()
    vals_a = get_unique_dim_vals(row_vals_used, dbe, flds, fld_a)
    if len(vals_a) > mg.MAX_CHI_DIMS:
        raise my_exceptions.TooManyRowsInChiSquare
    if len(vals_a) < mg.MIN_CHI_DIMS:
        raise my_exceptions.TooFewRowsInChiSquare
    ## B) get COL vals used (almost a repeat) ***********************
    SQL_col_vals_used = f"""\
    SELECT {qfld_b}
    FROM {qtbl}
    WHERE {qfld_a} IS NOT NULL AND {qfld_b} IS NOT NULL
    {and_tbl_filt}
    GROUP BY {qfld_b}
    ORDER BY {qfld_b}
    """
    cur.execute(SQL_col_vals_used)
    col_vals_used = cur.fetchall()
    vals_b = get_unique_dim_vals(col_vals_used, dbe, flds, fld_b)
    if len(vals_b) > mg.MAX_CHI_DIMS:
        raise my_exceptions.TooManyColsInChiSquare
    if len(vals_b) < mg.MIN_CHI_DIMS:
        raise my_exceptions.TooFewColsInChiSquare
    if len(vals_a)*len(vals_b) > mg.MAX_CHI_CELLS:
        raise my_exceptions.TooManyCellsInChiSquare
    ## C) combine results of A) and B) ***********************
    ## build SQL to get all observed values (for each a, through b's)
    SQL_get_obs = 'SELECT '
    sql_lst = []
    ## need to filter by vals within SQL so may need quoting observed values etc
    for val_a in vals_a:
        val_quoter_a = get_val_quoter(dbe, flds, fld_a, val_a)
        for val_b in vals_b:
            val_quoter_b = get_val_quoter(dbe, flds, fld_b, val_b)
            clause = (f'\nSUM(CASE WHEN {qfld_a} = {val_quoter_a(val_a)} '
                f'AND {qfld_b} = {val_quoter_b(val_b)} THEN 1 ELSE 0 END)')
            sql_lst.append(clause)
    SQL_get_obs += ', '.join(sql_lst)
    SQL_get_obs += f'\nFROM {qtbl} '
    SQL_get_obs += f'\n{where_tbl_filt} '
    logging.debug(SQL_get_obs)
    cur.execute(SQL_get_obs)
    tup_obs = cur.fetchall()[0]
    if not tup_obs:
        raise Exception('No observed values')
    else:
        logging.debug(tup_obs)
    lst_obs = list(tup_obs)
    logging.debug(f'lst_obs: {lst_obs}')
    obs_total = float(sum(lst_obs))
    ## expected values
    lst_fracs_a = get_fracs(cur, tbl_filt, qtbl, qfld_a, qfld_b)
    lst_fracs_b = get_fracs(cur, tbl_filt, qtbl, qfld_b, qfld_a)
    df = (len(lst_fracs_a)-1)*(len(lst_fracs_b)-1)
    lst_exp = []
    for frac_a in lst_fracs_a:
        for frac_b in lst_fracs_b:
            lst_exp.append(frac_a*frac_b*obs_total)
    logging.debug(f'lst_exp: {lst_exp}')
    if len(lst_obs) != len(lst_exp):
        raise Exception('Different number of observed and expected values. '
            f'{len(lst_obs)} vs {len(lst_exp)}')
    min_count = min(lst_exp)
    lst_lt_5 = [x for x in lst_exp if x < 5]
    perc_cells_lt_5 = (100 * len(lst_lt_5)) / float(len(lst_exp))
    return vals_a, vals_b, lst_obs, lst_exp, min_count, perc_cells_lt_5, df

def get_fracs(cur, tbl_filt, qtbl, qfld, oth_qfld):
    """
    What fraction of the cross tab values are for each value in field? Leaves
    out values where either bit of the data pair is missing. Returns lst_fracs.
    """
    unused, and_tbl_filt = lib.FiltLib.get_tbl_filts(tbl_filt)
    SQL_get_fracs = f"""\
    SELECT {qfld}, COUNT(*)
    FROM {qtbl} 
    WHERE {qfld} IS NOT NULL
    AND {oth_qfld} IS NOT NULL
    {and_tbl_filt}
    GROUP BY {qfld}
    ORDER BY {qfld} """
    logging.debug(SQL_get_fracs)
    cur.execute(SQL_get_fracs)
    lst_counts = []
    total = 0
    for data_tup in cur.fetchall():
        val = data_tup[1]
        lst_counts.append(val)
        total += val
    lst_fracs = [x/float(total) for x in lst_counts]
    return lst_fracs

def pearsons_chisquare(dbe, cur, tbl, flds, fld_a, fld_b,
        tbl_filt, where_tbl_filt, and_tbl_filt):
    """
    Returns chisq, p, min_count, perc_cells_lt_5
    """
    (vals_a, vals_b, lst_obs,
     lst_exp, min_count,
     perc_cells_lt_5, df ) = get_obs_exp(dbe, cur, tbl, tbl_filt,
                                where_tbl_filt, and_tbl_filt, flds,
                                fld_a, fld_b)
    logging.debug(f"lst_obs={lst_obs}, lst_exp={lst_exp}")
    chisq, p = chisquare(lst_obs, lst_exp, df)
    return (chisq, p,
        vals_a, vals_b,
        lst_obs, lst_exp,
        min_count, perc_cells_lt_5, df)

def chisquare_details(vals_a, vals_b, lst_obs, df):
    n_a = len(vals_a)
    n_b = len(vals_b)
    ## Restructure lst_obs to nested lists following pattern of contingency table
    ## The lists are b within a e.g. a1b1, a1b2, a1b3, a2b1, a2b2 ...
    ## (i.e. across the rows)
    obs = np.reshape(lst_obs, (n_a, n_b))
    grand_total = sum(lst_obs)
    obs_idx = 0
    row_sums = defaultdict(int)
    col_sums = defaultdict(int)
    row_obs = defaultdict(list)
    col_obs = defaultdict(list)
    cells_data = OrderedDict()
    ## round 1
    for col_n, unused in enumerate(vals_b, 1):
        for row_n, unused in enumerate(vals_a, 1):
            observed = obs[row_n - 1][col_n - 1]  ## need zero-based indexing for numpy
            row_sums[row_n] += observed
            col_sums[col_n] += observed
            row_obs[row_n].append(observed)
            col_obs[col_n].append(observed)
            cells_data[(row_n, col_n)] = {  ## can't add any more details until calculated row and column totals
                mg.CHI_OBSERVED: observed,
            }
            obs_idx += 1
    ## round 2 (now that we have row and column totals we can calculate the missing bits)
    pre_chis = []
    chi_squ = 0
    for coord, cell_data in cells_data.items():
        row_n, col_n = coord
        row_sum = row_sums[row_n]
        col_sum = col_sums[col_n]
        observed = cell_data[mg.CHI_OBSERVED]
        expected = (row_sum * col_sum)/float(grand_total)
        cell_data[mg.CHI_CELL_ROW_SUM] = row_sum
        cell_data[mg.CHI_CELL_COL_SUM] = col_sum
        cell_data[mg.CHI_EXPECTED] = round(expected, 3)
        max_obs_exp = max([observed, expected])
        min_obs_exp = min([observed, expected])
        cell_data[mg.CHI_MAX_OBS_EXP] = round(max_obs_exp, 3)
        cell_data[mg.CHI_MIN_OBS_EXP] = round(min_obs_exp, 3)
        diff = max_obs_exp - min_obs_exp
        cell_data[mg.CHI_DIFF] = round(diff, 3)
        diff_squ = diff ** 2
        cell_data[mg.CHI_DIFF_SQU] = round(diff_squ, 3)
        raw_pre_chi = diff_squ / float(expected)
        chi_squ += raw_pre_chi
        pre_chi = round(raw_pre_chi, 3)
        cell_data[mg.CHI_PRE_CHI] = pre_chi
        pre_chis.append(pre_chi)
    details = {
        mg.CHI_GRAND_TOT: grand_total,
        mg.CHI_ROW_SUMS: row_sums,
        mg.CHI_ROW_OBS: row_obs,
        mg.CHI_COL_SUMS: col_sums,
        mg.CHI_COL_OBS: col_obs,
        mg.CHI_ROW_N: n_a,
        mg.CHI_COL_N: n_b,
        mg.CHI_ROW_N_MINUS_1: n_a - 1,
        mg.CHI_COL_N_MINUS_1: n_b - 1,
        mg.CHI_CELLS_DATA: cells_data,
        mg.CHI_PRE_CHIS: pre_chis,
        mg.CHI_CHI_SQU: round(chi_squ, 3),
        mg.CHI_DF: df,
    }
    return details

# Taken from v1.1 of statlib http://code.google.com/p/python-statlib/
# NB lots of ongoing change at
# http://projects.scipy.org/scipy/browser/trunk/scipy/stats/stats.py

# code below here is modified versions of code in stats.py and pstats.py

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

def histogram (inlist, numbins=10, defaultreallimits=None, printextras=0, *,
        inc_uppermost_val_in_top_bin=True):
    """
    From stats.py. Modified to include uppermost value in top bin. This is
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
    if (defaultreallimits != None):
        if (not isinstance(defaultreallimits, (list, tuple))) or \
                len(defaultreallimits) == 1:  ## only one limit given, assumed to be lower one & upper is calc'd
            lowerreallimit = defaultreallimits
            upperreallimit = 1.000001 * max(inlist)
        else:  ## assume both limits given
            lowerreallimit = defaultreallimits[0]
            upperreallimit = defaultreallimits[1]
        binsize = (upperreallimit-lowerreallimit)/float(numbins)
    else:  ## no limits given for histogram, both must be calc'd
        estbinwidth=(max(inlist)-min(inlist))/float(numbins) +1e-6  ##1=>cover all
        binsize = ((max(inlist)-min(inlist)+estbinwidth))/float(numbins)
        lowerreallimit = min(inlist) - binsize/2  ## lower real limit,1st bin
        upperreallimit = 1.000001 * max(inlist)  ## added by me so able to include top val in final bin. Use same code as orig to calc upp from lower
    bins = [0]*(numbins)
    extrapoints = 0
    for num in inlist:
        try:
            if (num-lowerreallimit) < 0 and inc_uppermost_val_in_top_bin:
                extrapoints = extrapoints + 1
            else:
                if num == upperreallimit:  ## includes uppermost value in top bin
                    bins[numbins-1] += 1
                else:  ## the original always did this if not (num-lowerreallimit) < 0
                    bintoincrement = int((num-lowerreallimit)/float(binsize))
                    bins[bintoincrement] = bins[bintoincrement] + 1
        except:
            extrapoints = extrapoints + 1
    if (extrapoints > 0 and printextras == 1):
        logging.warning('\nPoints outside given histogram range =', extrapoints)
    logging.debug(f"bins={bins}, lowerreallimit={lowerreallimit}, "
        f"binsize={binsize}, extrapoints={extrapoints}")
    return (bins, lowerreallimit, binsize, extrapoints)

def chisquare(f_obs,f_exp=None, df=None):
    """
    From stats.py.  Modified to receive df e.g. when in a crosstab.
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
    if f_exp == None:
        f_exp = [sum(f_obs) / float(k)] * len(f_obs)  ## create k bins with = freq.
    chisq = 0
    for i in range(len(f_obs)):
        chisq = chisq + (float(f_obs[i])-float(f_exp[i]))**2 / float(f_exp[i])
    if not df: df = k-1
    return chisq, chisqprob(chisq, df)

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
    a = len(lst_samples)           # ANOVA on 'a' groups, each in its own list
    n = len(lst_samples[0])
    #ns = [0]*a
    alldata = []
    dics = []
    for i in range(a):
        sample = lst_samples[i]
        label = lst_labels[i]
        dics.append({
            mg.STATS_DIC_LBL: label,
            mg.STATS_DIC_N: n,
            mg.STATS_DIC_MEAN: mean(sample),
            mg.STATS_DIC_SD: stdev(sample),
            mg.STATS_DIC_MIN: min(sample),
            mg.STATS_DIC_MAX: max(sample)})
    #ns = map(len, lst_samples)
    for i in range(len(lst_samples)):
        alldata = alldata + lst_samples[i]
    bign = len(alldata)
    sstot = sum_squares(alldata)-(square_of_sums(alldata)/float(bign))
    ssbn = 0
    for sample in lst_samples:
        ssbn = ssbn + square_of_sums(sample)/float(len(sample))
    ssbn = ssbn - (square_of_sums(alldata)/float(bign))
    sswn = sstot-ssbn
    dfbn = a-1
    dfwn = bign - a
    msb = ssbn/float(dfbn)
    msw = sswn/float(dfwn)
    F = msb/msw
    p = fprob(dfbn, dfwn, F)
    logging.info(f'Using orig with F: {F}')
    return p, F, dics, sswn, dfwn, msw, ssbn, dfbn, msb

def has_decimal_type_mix(numbers):
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
    logging.debug(f"mysd={mysd}, denom={denom}")
    if has_decimal_type_mix(numbers=(mysd, denom)):
        raise Exception("Can't mix decimals and other numbers for division when"
            ' calculating SE')
    se = mysd/denom
    return se

def get_ci95(sample=None, mymean=None, mysd=None, n=None, *, high=False):
    if sample is None and (n is None or mymean is None or mysd is None):
        raise Exception('Unable to calculate confidence interval without either'
            ' a sample or all of n, mean, and sd.')
    if n is None:
        n = len(sample)
        if high:
            n = D(n)
    mymean = mymean if mymean is not None else mean(sample, high=high)
    mysd = mysd if mysd is not None else stdev(sample, high=high)
    if has_decimal_type_mix(numbers=(mymean, mysd, n)):
        raise Exception('Cannot mix decimals and other numbers for some '
            'calculations e.g. division')
    if n < 30:  ## ok for mix decimals and non-dec
        logging.warning(
            'Using sample sd instead of population sd even though n < 30. '
            'May not be reliable.')
    se = get_se(n, mysd, high=high)
    sds = 1.96
    if high:
        sds = D(sds)
    diff = sds*se
    if has_decimal_type_mix(numbers=(mymean,diff)):
        raise Exception('Cannot mix decimals and other numbers for some '
            'calculations e.g. addition and subtraction when calculating CI '
            'lower and upper bounds')
    lower95 = mymean - diff
    upper95 = mymean + diff
    return (lower95, upper95)

def anova(samples, labels, *, high=True):
    """
    From NIST algorithm used for their ANOVA tests.

    Added correction factor. And a zero division trap.

    :param bool high: high precision but much, much slower. Multiplies each by
     10 (and divides by 10 and 100 as appropriate) plus uses decimal rather than
     floating point. Needed to handle difficult datasets e.g. ANOVA test 9 from
     NIST site.
    """
    n_samples = len(samples)
    sample_ns = list(map(len, samples))
    dics = []
    for i in range(n_samples):
        sample = samples[i]
        label = labels[i]
        mymean = mean(sample, high=high)
        mysd = stdev(sample, high=high)
        ci95 = get_ci95(sample, mymean, mysd, n=None, high=high)
        dics.append({mg.STATS_DIC_LBL: label, 
                     mg.STATS_DIC_N: sample_ns[i], 
                     mg.STATS_DIC_MEAN: mymean, 
                     mg.STATS_DIC_SD: mysd, 
                     mg.STATS_DIC_MIN: min(sample), 
                     mg.STATS_DIC_MAX: max(sample),
                     mg.STATS_DIC_CI: ci95})
    if high:  ## inflate
        ## if to 1 decimal point will push from float to integer (reduce errors)
        inflated_samples = []
        for sample in samples:
            inflated_samples.append([x * 10 for x in sample])  ## NB inflated
        samples = inflated_samples
        sample_means = [lib.n2d(mean(x, high=high)) for x in samples]  ## NB inflated
    else:
        sample_means = [mean(x, high=high) for x in samples]
    sswn = get_sswn(samples, sample_means, high=high)
    dfwn = sum(sample_ns) - n_samples
    mean_squ_wn = sswn/dfwn
    if mean_squ_wn == 0:
        raise my_exceptions.InadequateVariability
    ssbn = get_ssbn(samples, sample_means, n_samples, sample_ns, high=high)
    dfbn = n_samples - 1
    mean_squ_bn = ssbn/dfbn
    F = mean_squ_bn/mean_squ_wn
    p = fprob(dfbn, dfwn, F, high=high)
    return p, F, dics, sswn, dfwn, mean_squ_wn, ssbn, dfbn, mean_squ_bn

def get_sswn(samples, sample_means, *, high=False):
    "Get sum of squares within treatment"
    if not high:
        sswn = 0  ## sum of squares within treatment
        for i, sample in enumerate(samples):
            diffs = []
            sample_mean = sample_means[i]
            for val in sample:
                diffs.append(val - sample_mean)
            squ_diffs = [(x**2) for x in diffs]
            sum_squ_diffs = sum(squ_diffs)
            sswn += sum_squ_diffs
    else:    
        sswn = D('0')  ## sum of squares within treatment
        for i, sample in enumerate(samples):
            diffs = []
            sample_mean = sample_means[i]
            for val in sample:
                diffs.append(lib.n2d(val) - sample_mean)
            squ_diffs = [(x**2) for x in diffs]
            sum_squ_diffs = sum(squ_diffs)
            sswn += sum_squ_diffs
        sswn = sswn/10**2  ## deflated
    return sswn

def get_ssbn(samples, sample_means, n_samples, sample_ns, *, high=False):
    """
    Get sum of squares between treatment.

    Has high-precision (but slower) version. NB Samples and sample means are
    inflated uniformly in the high precision versions.
    """
    if not high:
        sum_all_vals = sum(sum(x) for x in samples)
        n_tot = sum(sample_ns)
        grand_mean = sum_all_vals/float(n_tot)  ## correction factor
        squ_diffs = []
        for i in range(n_samples):
            squ_diffs.append((sample_means[i] - grand_mean)**2)
        sum_n_x_squ_diffs = 0
        for i in range(n_samples):
            sum_n_x_squ_diffs += sample_ns[i]*squ_diffs[i]
        ssbn = sum_n_x_squ_diffs
    else:
        sum_all_vals = lib.n2d(sum(lib.n2d(sum(x)) for x in samples))
        n_tot = lib.n2d(sum(sample_ns))
        grand_mean = sum_all_vals/n_tot  ## NB inflated
        squ_diffs = []
        for i in range(n_samples):
            squ_diffs.append((sample_means[i] - grand_mean)**2)
        sum_n_x_squ_diffs = D('0')
        for i in range(n_samples):
            sum_n_x_squ_diffs += sample_ns[i]*squ_diffs[i]
        ssbn = sum_n_x_squ_diffs/(10**2)  ## deflated
    return ssbn

def get_summary_dics(samples, labels, quant=False):
    """
    Get a list of dictionaries - one for each sample. Each contains label, n,
    median, min, and max.

    :param list labels: must be in same order as samples with one label for each
     sample.
    :param bool quant: if True, dics also include mean and standard deviation.
    """
    dics = []
    for i, sample in enumerate(samples):
        dic = {mg.STATS_DIC_LBL: labels[i],
               mg.STATS_DIC_N: len(sample),
               mg.STATS_DIC_MEDIAN: np.median(sample),
               mg.STATS_DIC_MIN: min(sample),
               mg.STATS_DIC_MAX: max(sample),
               }
        if quant:
            dic[mg.STATS_DIC_MEAN] = mean(sample)
            dic[mg.STATS_DIC_SD] = stdev(sample)
        dics.append(dic)
    return dics

def kruskalwallish(samples, labels):
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
    dics = get_summary_dics(samples, labels)
    #n = [0]*len(samples)
    all_data = []
    n = list(map(len, samples))
    for i in range(len(samples)):
        all_data = all_data + samples[i]
    ranked = rankdata(all_data)
    T = tiecorrect(ranked)
    for i in range(len(samples)):
        samples[i] = ranked[0:n[i]]
        del ranked[0:n[i]]
    rsums = []
    for i in range(len(samples)):
        rsums.append(sum(samples[i])**2)
        rsums[i] = rsums[i] / float(n[i])
    ssbn = sum(rsums)
    totaln = sum(n)
    h = 12.0 / (totaln*(totaln+1)) * ssbn - 3*(totaln+1)
    df = len(samples) - 1
    if T == 0:
        raise my_exceptions.InadequateVariability
    h = h / float(T)
    return h, chisqprob(h,df), dics, df

def ttest_ind(sample_a, sample_b, label_a, label_b, *, use_orig_var=False):
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

    :return: t, p, dic_a, dic_b, df (p is the two-tailed probability)
    :rtype: tuple

    ---------------------------------------------------------------------
    Calculates the t-obtained T-test on TWO INDEPENDENT samples of
    scores a, and b. From Numerical Recipes, p.483.
    """
    mean_a = mean(sample_a)
    mean_b = mean(sample_b)
    if use_orig_var:
        se_a = stdev(sample_a)**2
        se_b = stdev(sample_b)**2
        sd_a = math.sqrt(se_a)
        sd_b = math.sqrt(se_b)
    else:
        se_a = variance(sample_a)
        se_b = variance(sample_b)
        sd_a = stdev(sample_a)
        sd_b = stdev(sample_b)
    n_a = len(sample_a)
    n_b = len(sample_b)
    df = n_a + n_b - 2
    svar = ((n_a - 1)*se_a + (n_b - 1)*se_b)/float(df)
    denom = math.sqrt(svar*(1.0/n_a + 1.0/n_b))
    if denom == 0:
        raise my_exceptions.InadequateVariability
    t = (mean_a - mean_b)/denom
    p = betai(0.5*df, 0.5, df/(df + t*t))
    min_a = min(sample_a)
    min_b = min(sample_b)
    max_a = max(sample_a)
    max_b = max(sample_b)
    ci95_a = get_ci95(sample_a, mean_a, sd_a)
    ci95_b = get_ci95(sample_b, mean_b, sd_b)
    dic_a = {mg.STATS_DIC_LBL: label_a, mg.STATS_DIC_N: n_a,
             mg.STATS_DIC_MEAN: mean_a, mg.STATS_DIC_SD: sd_a,
             mg.STATS_DIC_MIN: min_a, mg.STATS_DIC_MAX: max_a,
             mg.STATS_DIC_CI: ci95_a}
    dic_b = {mg.STATS_DIC_LBL: label_b, mg.STATS_DIC_N: n_b,
             mg.STATS_DIC_MEAN: mean_b, mg.STATS_DIC_SD: sd_b,
             mg.STATS_DIC_MIN: min_b, mg.STATS_DIC_MAX: max_b,
             mg.STATS_DIC_CI: ci95_b}
    return t, p, dic_a, dic_b, df

def ttest_rel (sample_a, sample_b, label_a='Sample1', label_b='Sample2'):
    """
    From stats.py - there are changes to variable labels and comments; and the
    output is extracted early to give greater control over presentation. A list
    of the differences is extracted along the way. There are no changes to
    algorithms. Also added trap for zero division error.

    :return: t, p, dic_a, dic_b (p is the two-tailed probability), diffs
    :rtype: tuple
    ---------------------------------------------------------------------
    Calculates the t-obtained T-test on TWO RELATED samples of scores,
    a and b. From Numerical Recipes, p.483.
    """
    if len(sample_a)!=len(sample_b):
        raise ValueError('Unequal length lists in ttest_rel.')
    mean_a = mean(sample_a)
    mean_b = mean(sample_b)
    var_a = variance(sample_a)
    var_b = variance(sample_b)
    n = len(sample_a)
    cov = 0
    diffs = []
    for i in range(n):
        item_a = sample_a[i]
        item_b = sample_b[i]
        diff = item_b - item_a
        diffs.append(diff)
        cov = cov + (item_a - mean_a) * (item_b - mean_b)
    df = n - 1
    cov = cov / float(df)
    sd = math.sqrt((var_a + var_b - 2.0*cov) / float(n))
    if sd == 0:
        raise Exception('Unable to calculate t statistic - insufficient '
            'variability in at least one variable.')
    t = (mean_a - mean_b)/sd
    p = betai(0.5*df, 0.5, df / (df + t*t))
    min_a = min(sample_a)
    min_b = min(sample_b)
    max_a = max(sample_a)
    max_b = max(sample_b)
    sd_a = math.sqrt(var_a)
    sd_b = math.sqrt(var_b)
    ci95_a = get_ci95(sample_a, mean_a, sd_a)
    ci95_b = get_ci95(sample_b, mean_b, sd_b)
    dic_a = {mg.STATS_DIC_LBL: label_a, mg.STATS_DIC_N: n,
             mg.STATS_DIC_MEAN: mean_a, mg.STATS_DIC_SD: sd_a,
             mg.STATS_DIC_MIN: min_a, mg.STATS_DIC_MAX: max_a,
             mg.STATS_DIC_CI: ci95_a}
    dic_b = {mg.STATS_DIC_LBL: label_b, mg.STATS_DIC_N: n,
             mg.STATS_DIC_MEAN: mean_b, mg.STATS_DIC_SD: sd_b,
             mg.STATS_DIC_MIN: min_b, mg.STATS_DIC_MAX: max_b,
             mg.STATS_DIC_CI: ci95_b}
    return t, p, dic_a, dic_b, df, diffs

def mannwhitneyu(sample_a, sample_b, label_a='Sample1', label_b='Sample2', *,
        headless=False):
    """
    From stats.py - there are changes to variable labels and comments; and the
    output is extracted early to give greater control over presentation. Also
    added calculation of mean ranks, plus min and max values. And changed error
    type. And added headless option.
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
    n_a = len(sample_a)
    n_b = len(sample_b)
    ranked = rankdata(sample_a + sample_b, headless=headless)
    rank_a = ranked[0:n_a]  ## get the sample_a ranks
    rank_b = ranked[n_a:]  ## the rest are sample_b ranks
    avg_rank_a = mean(rank_a)
    avg_rank_b = mean(rank_b)
    u_a = n_a*n_b + (n_a*(n_a + 1))/2.0 - sum(rank_a)  ## calc U for sample_a
    u_b = n_a*n_b - u_a  ## remainder is U for sample_b
    bigu = max(u_a, u_b)
    smallu = min(u_a, u_b)
    T = math.sqrt(tiecorrect(ranked))  ## correction factor for tied scores
    if T == 0:
        raise my_exceptions.InadequateVariability
    sd = math.sqrt(T*n_a*n_b*(n_a + n_b + 1)/12.0)
    z = abs((bigu-n_a*n_b/2.0) / sd)  ## normal approximation for prob calc
    p = 1.0 - zprob(z)
    min_a = min(sample_a)
    min_b = min(sample_b)
    max_a = max(sample_a)
    max_b = max(sample_b)
    dic_a = {mg.STATS_DIC_LBL: label_a, mg.STATS_DIC_N: n_a,
        'avg rank': avg_rank_a,
        mg.STATS_DIC_MEDIAN: np.median(sample_a),
        mg.STATS_DIC_MIN: min_a, mg.STATS_DIC_MAX: max_a}
    dic_b = {mg.STATS_DIC_LBL: label_b, mg.STATS_DIC_N: n_b,
        'avg rank': avg_rank_b,
        mg.STATS_DIC_MEDIAN: np.median(sample_b),
        mg.STATS_DIC_MIN: min_b,
        mg.STATS_DIC_MAX: max_b}
    return smallu, p, dic_a, dic_b, z

def mannwhitneyu_details(
        sample_a, sample_b,
        label_a='Sample1',
        label_b='Sample2', *,
        headless=False):
    """
    The example in "Simple Statistics - A course book for the social sciences"
    Frances Clegg pp.164-166 refers to A as the shorted list (if uneven lengths)
    so there is some risk of confusion because A in SOFA refers to the leftmost
    variable. So using _1 and _2 for sample names. Doesn't alter result which is
    1 or 2 - purely to reduce amount of calculation.

    Note - the rank all the data approach vs the make every individual
    comparison approach yield exactly the same results. The comparison approach
    is more intuitive in meaning - the ranked approach is much faster.
    """
    len_a = len(sample_a)
    len_b = len(sample_b)
    if len_b < len_a:  ## make a first unless b shorter
        sample_1 = sample_b
        sample_2 = sample_a
        label_1 = label_b
        label_2 = label_a
    else:
        sample_1 = sample_a
        sample_2 = sample_b
        label_1 = label_a
        label_2 = label_b
    len_1 = len(sample_1)
    len_2 = len(sample_2)
    ## vals, counter, ranking
    val_dets_1 = [{'sample': 1, 'val': val} for val in sample_1]
    val_dets_2 = [{'sample': 2, 'val': val} for val in sample_2]
    val_dets = val_dets_1 + val_dets_2
    val_dets.sort(key=lambda s: s['val'])
    vals = sample_1 + sample_2
    vals_ranked = rankdata(vals, headless=headless)
    val_ranks = dict(zip(vals, vals_ranked))  ## works because all abs diffs which are the same share a single rank
    for counter, val_det in enumerate(val_dets, 1):
        val_det['rank'] = val_ranks[val_det['val']]
        val_det['counter'] = counter
    ranks_1 = [val_det['rank'] for val_det in val_dets
        if val_det['sample'] == 1]
    sum_rank_1 = sum(val_det['rank'] for val_det in val_dets
        if val_det['sample'] == 1)
    u_1 = len_1*len_2 + (len_1*(len_1 + 1))/2.0 - sum_rank_1
    u_2 = len_1*len_2 - u_1
    u = min(u_1, u_2)
    details = {
        mg.MANN_WHITNEY_LABEL_1: label_1,
        mg.MANN_WHITNEY_LABEL_2: label_2,
        mg.MANN_WHITNEY_N_1: len_1,
        mg.MANN_WHITNEY_N_2: len_2,
        mg.MANN_WHITNEY_RANKS_1: ranks_1,
        mg.MANN_WHITNEY_VAL_DETS: val_dets,
        mg.MANN_WHITNEY_SUM_RANK_1: sum_rank_1,
        mg.MANN_WHITNEY_U_1: u_1,
        mg.MANN_WHITNEY_U_2: u_2,
        mg.MANN_WHITNEY_U: u,
    }
    return details

def wilcoxont(
        sample_a, sample_b,
        label_a='Sample1', label_b='Sample2', *,
        headless=False):
    """
    From stats.py.  Added error trapping. Changes to variable labels.
    Added calculation of n, medians, plus min and max values. And added headless
    option.
    -------------------------------------
    Calculates the Wilcoxon T-test for related samples and returns the
    result.  A non-parametric T-test.

    Usage:   wilcoxont(sample_a,sample_b)
    Returns: a t-statistic, two-tail probability estimate, z
    """
    if len(sample_a) != len(sample_b):
        raise ValueError('Unequal N in wilcoxont. Aborting.')
    n = len(sample_a)
    d=[]
    for i in range(len(sample_a)):
        try:
            diff = sample_a[i] - sample_b[i]
        except TypeError:            
            raise Exception(
                'Both values in pair must be numeric:'
                f' {sample_a[i]} and {sample_b[i]}')
        if diff != 0:
            d.append(diff)
    count = len(d)
    absd = list(map(abs, d))
    absranked = rankdata(absd, headless=headless)
    r_plus = 0.0
    r_minus = 0.0
    for i in range(len(list(absd))):
        if d[i] < 0:
            r_minus = r_minus + absranked[i]
        else:
            r_plus = r_plus + absranked[i]
    wt = min(r_plus, r_minus)
    mn = count * (count+1) * 0.25
    se =  math.sqrt(count*(count+1)*(2.0*count+1.0)/24.0)
    z = math.fabs(wt-mn) / se
    prob = 2*(1.0 -zprob(abs(z)))
    min_a = min(sample_a)
    min_b = min(sample_b)
    max_a = max(sample_a)
    max_b = max(sample_b)
    dic_a = {mg.STATS_DIC_LBL: label_a, mg.STATS_DIC_N: n,  
             mg.STATS_DIC_MEDIAN: np.median(sample_a), 
             mg.STATS_DIC_MIN: min_a, mg.STATS_DIC_MAX: max_a}
    dic_b = {mg.STATS_DIC_LBL: label_b, mg.STATS_DIC_N: n,
             mg.STATS_DIC_MEDIAN: np.median(sample_b),  
             mg.STATS_DIC_MIN: min_b, 
             mg.STATS_DIC_MAX: max_b}
    return wt, prob, dic_a, dic_b

def wilcoxont_details(sample_a, sample_b):
    """
    Only return worked example if a small amount of data. Otherwise return an
    empty dict.

    See "Simple Statistics - A course book for the social sciences"
    Frances Clegg pp.158-160

    Not focused on performance - just clarity
    """
    pairs = zip(sample_a, sample_b)
    ## diffs between pairs (always in same order but which order doesn't matter
    diff_dets = [{'a': a, 'b': b, 'diff': a-b} for a, b in pairs]
    ## get ranks on absolutes and then attach back
    abs_diffs = [abs(x['diff']) for x in diff_dets]
    abs_diffs.sort()
    ranks = rankdata(abs_diffs)
    ## link ranks to diffs and abs diffs
    abs_diff_ranks = dict(zip(abs_diffs, ranks))  ## works because all abs diffs which are the same share a single rank
    ranking_dets = []
    for diff in diff_dets:
        if diff['diff'] != 0:
            ranking_dets.append(
                {'diff': diff['diff'],
                 'abs_diff': abs(diff['diff']),
                 'rank': abs_diff_ranks[abs(diff['diff'])], })  ## remember - the ranks relates to the absolute value not the original value
    ranking_dets.sort(key=lambda s: (abs(s['diff']), s['diff']))
    ## add counter
    for counter, ranking_det in enumerate(ranking_dets, 1):
        ranking_det['counter'] = counter
    plus_ranks = [x['rank'] for x in ranking_dets if x['diff'] > 0]
    minus_ranks = [x['rank'] for x in ranking_dets if x['diff'] < 0]
    ## sum the ranks separately
    sum_plus_ranks = sum(plus_ranks)
    sum_minus_ranks = sum(minus_ranks)
    ## calculate t and N (N excludes 0-diff pairs)
    t = min(sum_plus_ranks, sum_minus_ranks)
    n = len(plus_ranks) + len(minus_ranks)
    details = {
        mg.WILCOXON_DIFF_DETS: diff_dets,
        mg.WILCOXON_RANKING_DETS: ranking_dets,
        mg.WILCOXON_PLUS_RANKS : plus_ranks,
        mg.WILCOXON_MINUS_RANKS : minus_ranks,
        mg.WILCOXON_SUM_PLUS_RANKS : round(sum_plus_ranks, 2),
        mg.WILCOXON_SUM_MINUS_RANKS : round(sum_minus_ranks, 2),
        mg.WILCOXON_T: t,
        mg.WILCOXON_N: n,
        }
    return details

def linregress(x,y):
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
        raise ValueError('Input values not paired in linregress. Aborting.')
    n = len(x)
    x = list(map(float, x))
    y = list(map(float, y))
    xmean = mean(x)
    ymean = mean(y)
    r_num = float(n*(summult(x,y)) - sum(x)*sum(y))
    r_den = math.sqrt((n*sum_squares(x) - square_of_sums(x))
        *(n*sum_squares(y) - square_of_sums(y)))
    try:
        r = r_num / r_den
    except ZeroDivisionError:
        raise Exception('Unable to calculate linear regression because of '
            'limited variability in one dimension')
    #z = 0.5*math.log((1.0+r+TINY)/(1.0-r+TINY))
    df = n-2
    t = r*math.sqrt(df/((1.0-r+TINY)*(1.0+r+TINY)))
    prob = betai(0.5*df,0.5,df/(df+t*t))
    slope = r_num / float(n*sum_squares(x) - square_of_sums(x))
    intercept = ymean - slope*xmean
    sterrest = math.sqrt(1-r*r)*samplestdev(y)
    return slope, intercept, r, prob, sterrest

def pearsonr(x,y):
    """
    From stats.py. No changes apart from added error trapping, commenting out
    unused variable calculation, and trapping zero division error. And Py3
    changes.
    -------------------------------------

    Calculates a Pearson correlation coefficient and the associated probability
    value. Taken from Heiman's Basic Statistics for the Behav. Sci (2nd), p.195.

    Usage:   pearsonr(x,y)      where x and y are equal-length lists
    Returns: Pearson's r value, two-tailed p-value
    """
    TINY = 1.0e-30
    if len(x) != len(y):
        raise ValueError('Input values not paired in pearsonr. Aborting.')
    n = len(x)
    try:
        x = list(map(float, x))
        y = list(map(float, y))
    except ValueError as e:
        raise Exception(f"Unable to calculate Pearson's R. {b.ue(e)}")
    #xmean = mean(x)
    #ymean = mean(y)
    r_num = n*(summult(x,y)) - sum(x)*sum(y)
    r_den = math.sqrt((n*sum_squares(x) - square_of_sums(x))
        * (n*sum_squares(y)-square_of_sums(y)))
    if r_den == 0:
        raise my_exceptions.InadequateVariability
    r = (r_num / r_den)  ## denominator already a float
    df = n-2
    t = r*math.sqrt(df/((1.0-r+TINY)*(1.0+r+TINY)))
    try:
        prob = betai(0.5*df,0.5,df/float(df+t*t))
    except ZeroDivisionError:
        raise Exception("Unable to calculate Pearson's R. The df value and t "
            'are all 0 so trying to divide by df + t*t meant trying to divide '
            'by zero which is an error. But still worth looking at a '
            'scatterplot chart to assess the relationship.')
    return r, prob, df

def spearmanr(x, y, *, headless=False):
    """
    From stats.py. No changes apart from addition of headless option and
    trapping zero division error.
    -------------------------------------
    Calculates a Spearman rank-order correlation coefficient. Taken
    from Heiman's Basic Statistics for the Behav. Sci (1st), p.192.

    Usage:   spearmanr(x,y)      where x and y are equal-length lists
    Returns: Spearman's r, two-tailed p-value
    """
    if len(x) != len(y):
        raise ValueError('Input values not paired in spearmanr. Aborting.')
    n = len(x)
    rankx = rankdata(x, headless=headless)
    ranky = rankdata(y, headless=True)  ## don't ask twice
    dsq = sumdiffsquared(rankx,ranky)
    rs = 1 - 6*dsq / float(n*(n**2-1))
    try:
        t = rs * math.sqrt((n-2) / ((rs+1.0)*(1.0-rs)))
    except ZeroDivisionError:
        raise Exception("Unable to calculate Spearman's R. The raw scores value"
            f' (rs) was {rs} so trying to divide by 1.0-rs meant trying to '
            'divide by zero which is an error. But still worth looking at a '
            'scatterplot chart to assess the relationship.')
    df = n - 2
    probrs = betai(0.5*df, 0.5, df / (df+t*t))  ## t already a float
    ## probability values for rs are from part 2 of the spearman function in
    ## Numerical Recipes, p.510.  They are close to tables, but not exact. (?)
    return rs, probrs, df

def spearmanr_details(sample_x, sample_y, *, headless=False):
    initial_tbl = []
    n_x = len(sample_x)
    if n_x != len(sample_y):
        raise Exception(f'Different sample sizes ({n_x} vs {len(sample_y)})')
    rankx = rankdata(sample_x, headless=headless)
    x_and_rank = list(zip(sample_x, rankx))
    x_and_rank.sort()
    x2rank = dict(x_and_rank)
    ranky = rankdata(sample_y, headless=True)
    y_and_rank = list(zip(sample_y, ranky))
    y_and_rank.sort()
    y2rank = dict(y_and_rank)
    n_cubed_minus_n = (n_x**3) - n_x
    diff_squareds = []
    for x, y in zip(sample_x, sample_y):
        x_rank = x2rank[x]
        y_rank = y2rank[y]
        diff = x_rank - y_rank
        diff_squared = diff**2
        diff_squareds.append(diff_squared)
        initial_tbl.append(SpearmansInitTbl(x, y, x_rank, y_rank, diff,
            diff_squared))
    tot_d_squared = sum(diff_squareds)
    pre_rho = (tot_d_squared * 6) / float(n_cubed_minus_n)
    rho = 1 - pre_rho
    if not (-1 <= pre_rho <= 1):
        raise Exception(f'Bad value for pre_rho of {pre_rho} '
            "(shouldn't have absolute value > 1)")
    details = {
        mg.SPEARMANS_INIT_TBL: initial_tbl,
        mg.SPEARMANS_X_RANKED: x_and_rank,
        mg.SPEARMANS_Y_RANKED: y_and_rank,
        mg.SPEARMANS_N: n_x,
        mg.SPEARMANS_N_CUBED_MINUS_N: n_cubed_minus_n,
        mg.SPEARMANS_TOT_D_SQUARED: round(tot_d_squared, 2),
        mg.SPEARMANS_TOT_D_SQUARED_x_6: round(6*tot_d_squared, 2),
        mg.SPEARMANS_PRE_RHO: round(pre_rho, 4),
        mg.SPEARMANS_RHO: round(rho, 4),
    }
    return details

def rankdata(inlist, *, headless=False):
    """
    From stats.py. No changes apart from headless addition and Py3 changes.
    -------------------------------------
    Ranks the data in inlist, dealing with ties appropriately. Assumes
    a 1D inlist.  Adapted from Gary Perlman's |Stat ranksort.

    Usage:   rankdata(inlist)
    Returns: a list of length equal to inlist, containing rank scores
    """
    mylist = list(inlist)
    n = len(mylist)
    # -----------------------
    if not headless and n > mg.MAX_RANKDATA_VALS:
        import wx
        if wx.MessageBox(_('The rankdata function will run very slowly with '
                "this many records (%s). Do you wish to continue?") % n,
                caption=_('HIGH NUMBER OF RECORDS'),
                style=wx.YES_NO) == wx.NO:
            raise Exception('Too many records to continue with analysis')
    # -----------------------
    svec, ivec = shellsort(mylist)
    sumranks = 0
    dupcount = 0
    newlist = [0]*n
    for i in range(n):
        sumranks = sumranks + i
        dupcount = dupcount + 1
        if i==n-1 or svec[i] != svec[i+1]:
            averank = sumranks / float(dupcount) + 1
            for j in range(i-dupcount+1,i+1):
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
            for j in range(i-gap,-1,-gap):
                while j>=0 and svec[j]>svec[j+gap]:
                    temp        = svec[j]
                    svec[j]     = svec[j+gap]
                    svec[j+gap] = temp
                    itemp       = ivec[j]
                    ivec[j]     = ivec[j+gap]
                    ivec[j+gap] = itemp
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
    while (i<n-1):
        if sorted_data[i] == sorted_data[i+1]:
            nties = 1
            while (i<n-1) and (sorted_data[i] == sorted_data[i+1]):
                nties = nties +1
                i = i +1
            T = T + nties**3 - nties
        i = i+1
    T = T / float(n**3-n)
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
        if y >= (Z_MAX*0.5):
            x = 1.0
        elif (y < 1.0):
            w = y*y
            x = ((((((((0.000124818987 * w
                        -0.001075204047) * w +0.005198775019) * w
                      -0.019198292004) * w +0.059054035642) * w
                    -0.151968751364) * w +0.319152932694) * w
                  -0.531923007300) * w +0.797884560593) * y * 2.0
        else:
            y = y - 2.0
            x = (((((((((((((-0.000045255659 * y
                             +0.000152529290) * y -0.000019538132) * y
                           -0.000676904986) * y +0.001390604284) * y
                         -0.000794620820) * y -0.002034254874) * y
                       +0.006549791214) * y -0.010557625006) * y
                     +0.011630447319) * y -0.009279453341) * y
                   +0.005353579108) * y -0.002141268741) * y
                 +0.000535310849) * y +0.999936657524
    if z > 0.0:
        prob = ((x+1.0)*0.5)
    else:
        prob = ((1.0-x)*0.5)
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
    def yfunc(y):
        x = (((((((((((((-0.000045255659 * y
                         +0.000152529290) * y -0.000019538132) * y
                       -0.000676904986) * y +0.001390604284) * y
                     -0.000794620820) * y -0.002034254874) * y
                   +0.006549791214) * y -0.010557625006) * y
                 +0.011630447319) * y -0.009279453341) * y
               +0.005353579108) * y -0.002141268741) * y
             +0.000535310849) * y +0.999936657524
        return x

    def wfunc(w):
        x = ((((((((0.000124818987 * w
                    -0.001075204047) * w +0.005198775019) * w
                  -0.019198292004) * w +0.059054035642) * w
                -0.151968751364) * w +0.319152932694) * w
              -0.531923007300) * w +0.797884560593) * np.sqrt(w) * 2.0
        return x

    Z_MAX = 6.0  ## maximum meaningful z-value
    #x = np.zeros(z.shape, np.float_) # initialize
    y = 0.5 * np.fabs(z)
    x = np.where(np.less(y,1.0),wfunc(y*y),yfunc(y-2.0))  ## get x's
    x = np.where(np.greater(y, Z_MAX*0.5), 1.0, x)  ## kill those with big Z
    prob = np.where(np.greater(z,0), (x+1)*0.5, (1-x)*0.5)
    return prob

def scoreatpercentile (vals, percent):
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
        logging.debug('\nDividing percent>1 by 100 in scoreatpercentile().\n')
        percent = percent / 100.0
    targetcf = percent*len(vals)
    (bins, lrl,
     binsize, unused) = histogram(vals, inc_uppermost_val_in_top_bin=False)
    cumhist = cumsum(copy.deepcopy(bins))
    for i in range(len(cumhist)):
        if cumhist[i] >= targetcf:
            break
    logging.debug(bins)
    numer = (targetcf - cumhist[i-1])
    denom = float(bins[i])
    score = binsize * (numer/denom) + (lrl+binsize*i)
    return score

def get_quartiles(vals):
    """
    From Wild & Seber Introduction to Probability and Statistics 1996 pp.74-77
    Depth of quartiles is (int(n/2)+1)/2
    (from left for LQ and from right for UQ).
    """
    newvals = vals[:]
    newvals.sort()  ## leaving vals untouched
    n = len(newvals)
    if not n:
        raise Exception('No values supplied to get_quartiles.')
    depth = (int(n/2.0)+1.0) / 2.0
    logging.debug(depth)
    ldepth = int(depth)
    ## NB zero-based so subtract 1 for position going upwards
    if int(depth) == depth:
        lq = newvals[ldepth-1]
        uq = newvals[-ldepth]
    else:  ## int truncates towards 0 but depth is always a positive number
        ## 1,3,4,5,60 depth = 5/2 i.e. [2.5] i.e. 2 -> 2+1 i.e. 3 -> 3/2 i.e. 1.5 
        # so lq = (1+3)/2 i.e. 2 and uq = (5+60)/2 i.e. 32.5
        udepth = int(depth) + 1
        lq = (newvals[ldepth-1] + newvals[udepth - 1]) / 2.0
        uq = (newvals[-ldepth] + newvals[-udepth]) / 2.0
    return lq, uq

def mean(vals, *, high=False):
    """
    From stats.py. No changes except option of using Decimals instead of floats
    and adding error trapping.
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
        mean = mysum / float(len(vals))
    else:
        tot = D('0')
        for val in vals:
            try:
                tot += lib.n2d(val)
            except Exception:
                raise Exception(f'Unable to add "{val}" to running total.')
        mean = tot / len(vals)
    return mean

def amean (inarray, dimension=None, keepdims=0):
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
    :return: arithematic mean calculated over dim(s) in dimension
    """
    if inarray.dtype in [np.int_, np.short, np.ubyte]:
        inarray = inarray.astype(np.float_)
    if dimension == None:
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
        mysum = inarray *1.0
        for dim in dims:
            mysum = np.add.reduce(mysum, dim)
        denom = np.array(
            np.multiply.reduce(np.take(inarray.shape,dims)), np.float_)
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
    deviations = [0]*len(vals)
    for i in range(len(vals)):
        val = vals[i]
        if high:
            val = lib.n2d(val)
        deviations[i] = val - mn
    if not high:
        var = sum_squares(deviations) / float(n-1)
    else:
        var = sum_squares(deviations, high=high) / lib.n2d(n-1)
    return var

def samplevar (vals, *, high=False):
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
        deviations.append(item-mn)
    if not high:
        var = sum_squares(deviations) / float(n)
    else:
        var = sum_squares(deviations, high=high) / lib.n2d(n)
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
            stdev = lib.n2d(math.sqrt(variance(vals, high=high)))
        else:
            stdev = math.sqrt(variance(vals))
    except ValueError:
        raise Exception(
            'stdev - error getting square root. Negative variance value?')
    return stdev

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
            stdev = lib.n2d(math.sqrt(samplevar(vals, high=high)))
        else:
            stdev = math.sqrt(samplevar(vals))
    except ValueError:
        raise Exception(
            'samplestdev - error getting square root. Negative variance value?')
    return stdev

def betai(a, b, x, *, high=False):
    """
    From stats.py.  No changes apart from adding detail to error message.
    -------------------------------------
    Returns the incomplete beta function:

        I-sub-x(a,b) = 1/B(a,b)*(Integral(0,x) of t^(a-1)(1-t)^(b-1) dt)

    where a,b>0 and B(a,b) = G(a)*G(b)/(G(a+b)) where G(a) is the gamma
    function of a.  The continued fraction formulation is implemented here,
    using the betacf function.  (Adapted from: Numerical Recipies in C.)

    Usage:   betai(a,b,x)
    """
    if high:        
        a = lib.n2d(a)
        b = lib.n2d(b)
        x = lib.n2d(x)
        zero = D('0')
        one = D('1')
        two = D('2')
    else:
        zero = 0.0
        one = 1.0
        two = 2.0
    if (x < zero or x > one):
        raise ValueError(f'Bad x {x} in betai')
    if (x==zero or x==one):
        bt = zero
    else:
        if high:
            bt_raw = math.exp(
                gammln(a+b, high=high)
                - gammln(a, high=high)
                - gammln(b, high=high)
                + a*lib.n2d(math.log(x))
                + b*lib.n2d(math.log(one - x)))
            bt = lib.n2d(bt_raw)
        else:
            bt = math.exp(
                gammln(a+b, high=high)
                - gammln(a, high=high)
                - gammln(b, high=high)
                + a*math.log(x)
                + b*math.log(1.0 - x))
    if (x < (a + one)/(a + b + two)):
        if high:
            return bt*betacf(a,b,x, high=high)/a
        else:
            return bt*betacf(a,b,x)/float(a)
    else:
        if high:
            return one-bt*betacf(b, a, one-x, high=high)/b
        else:
            return 1.0-bt*betacf(b,a,1.0-x)/float(b)

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
        sum_squares = D('0')
        for val in vals:
            decval = lib.n2d(val)
            sum_squares += (decval * decval)
    else:
        sum_squares = 0
        for val in vals:
            sum_squares += (val * val)
    return sum_squares

def gammln(xx, *, high=False):
    """
    From stats.py.  No changes except using option of using Decimals not floats.
    -------------------------------------
    Returns the gamma function of xx.
        Gamma(z) = Integral(0,infinity) of t^(z-1)exp(-t) dt.
    (Adapted from: Numerical Recipies in C.)

    Usage:   gammln(xx)
    """
    if high:
        intone = D('1')
        one = D('1.0')
        fiveptfive = D('5.5')
        xx = lib.n2d(xx)
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
        tmp = tmp - (x + D('0.5')) * lib.n2d(math.log(tmp))
    else:
        tmp = tmp - (x + 0.5) * math.log(tmp)
    ser = one
    for j in range(len(coeff)):
        x = x + intone
        ser = ser + coeff[j] / x
    if high:
        gammln = -tmp + lib.n2d(math.log(D('2.50662827465')*ser))
    else:
        gammln = -tmp + math.log(2.50662827465*ser)
    return gammln

def betacf(a, b, x, *, high=False):
    """
    From stats.py. No changes.
    -------------------------------------
    This function evaluates the continued fraction form of the incomplete
    Beta function, betai.  (Adapted from: Numerical Recipies in C.)

    Usage:   betacf(a,b,x)
    """
    if high:
        one = D('1')
        ITMAX = D('200')
        EPS = D('3.0e-7')
        a = lib.n2d(a)
        b = lib.n2d(b)
        x = lib.n2d(x)
        bm = az = am = one
        qab = a+b
        qap = a+one
        qam = a-one
        bz = one-qab*x/qap
    else:
        one = 1.0
        ITMAX = 200
        EPS = 3.0e-7
        bm = az = am = one
        qab = a+b
        qap = a+one
        qam = a-one
        bz = one-qab*x/qap
    for i in range(int(ITMAX)+1):
        if high:
            i = lib.n2d(i)
        em = i + one
        tem = em + em
        d = em*(b-em)*x/((qam+tem)*(a+tem))
        ap = az + d*am
        bp = bz+d*bm
        d = -(a+em)*(qab+em)*x/((qap+tem)*(a+tem))
        app = ap+d*az
        bpp = bp+d*bz
        aold = az
        am = ap/bpp
        bm = bp/bpp
        az = app/bpp
        bz = one
        if (abs(az-aold)<(EPS*abs(az))):
            return az
    logging.warning('a or b too big, or ITMAX too small in Betacf.')

def summult (list1, list2):
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
    for item1,item2 in abut(list1,list2):
        s = s + item1*item2
    return s

def abut (source, *args):
    """
    From pstat.py.  No changes except for type check updating and i -> _i.  
    -------------------------------------
    Like the |Stat abut command.  It concatenates two lists side-by-side
    and returns the result.  '2D' lists are also accomodated for either argument
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
        if len(addon) < len(source):                # is source list longer?
            if len(source) % len(addon) == 0:        # are they integer multiples?
                repeats = len(source)/len(addon)    # repeat addon n times
                origadd = copy.deepcopy(addon)
                for _i in range(repeats-1):
                    addon = addon + origadd
            else:
                repeats = len(source)/len(addon)+1  # repeat addon x times,
                origadd = copy.deepcopy(addon)      #    x is NOT an integer
                for _i in range(repeats-1):
                    addon = addon + origadd
                    addon = addon[0:len(source)]
        elif len(source) < len(addon):                # is addon list longer?
            if len(addon) % len(source) == 0:        # are they integer multiples?
                repeats = len(addon)/len(source)    # repeat source n times
                origsour = copy.deepcopy(source)
                for _i in range(repeats-1):
                    source = source + origsour
            else:
                repeats = len(addon)/len(source)+1  # repeat source x times,
                origsour = copy.deepcopy(source)    #   x is NOT an integer
                for _i in range(repeats-1):
                    source = source + origsour
                source = source[0:len(addon)]

        source = simpleabut(source,addon)
    return source

def simpleabut (source, addon):
    """
    From pstat.py.  No changes except type test updated.  
    -------------------------------------
    Concatenates two lists as columns and returns the result.  '2D' lists
    are also accomodated for either argument (source or addon).  This DOES NOT
    repeat either list to make the 2 lists of equal length.  Beware of list
    pairs with different lengths ... the resulting list will be the length of 
    the FIRST list passed.
    
    Usage: simpleabut(source,addon)  where source, addon=list (or list-of-lists)
    Returns: a list of lists as long as source, with source on the 'left' and
                     addon on the 'right'
    """
    if not isinstance(source, (list, tuple)):
        source = [source]
    if not isinstance(addon, (list, tuple)):
        addon = [addon]
    minlen = min(len(source),len(addon))
    mylist = copy.deepcopy(source)                # start abut process
    if not isinstance(source[0], (list, tuple)):
        if not isinstance(addon[0], (list, tuple)):
            for i in range(minlen):
                mylist[i] = [source[i]] + [addon[i]]     # source/addon = column
        else:
            for i in range(minlen):
                mylist[i] = [source[i]] + addon[i]      # addon=list-of-lists
    else:
        if not isinstance(addon[0], (list, tuple)):
            for i in range(minlen):
                mylist[i] = source[i] + [addon[i]]     # source=list-of-lists
        else:
            for i in range(minlen):
                mylist[i] = source[i] + addon[i]    # source/addon = list-of-lists
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
    return float(s)*s

def sumdiffsquared(x,y):
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
        sds = sds + (x[i]-y[i])**2
    return sds

def chisqprob(chisq, df):
    """
    From stats.py.  No changes.
    -------------------------------------
    Returns the (1-tailed) probability value associated with the provided
    chi-square value and df.  Adapted from chisq.c in Gary Perlman's |Stat.

    Usage:   chisqprob(chisq,df)
    """
    BIG = 20.0
    def ex(x):
        BIG = 20.0
        if x < -BIG:
            return 0.0
        else:
            return math.exp(x)

    if chisq <=0 or df < 1:
        return 1.0
    a = 0.5 * chisq
    if df%2 == 0:
        even = 1
    else:
        even = 0
    if df > 1:
        y = ex(-a)
    if even:
        s = y
    else:
        s = 2.0 * zprob(-math.sqrt(chisq))
    if (df > 2):
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
            while (z <= chisq):
                e = math.log(z) + e
                s = s + ex(c*z-a-e)
                z = z + 1.0
            return s
        else:
            if even:
                e = 1.0
            else:
                e = 1.0 / math.sqrt(math.pi) / math.sqrt(a)
            c = 0.0
            while (z <= chisq):
                e = e * (a/float(z))
                c = c + e
                z = z + 1.0
            return (c*y+s)
    else:
        return s

def fprob (dfnum, dfden, F, *, high=False):
    """
    From stats.py. No changes except uses Decimals instead of floats.  
    -------------------------------------
    Returns the (1-tailed) significance level (p-value) of an F
    statistic given the degrees of freedom for the numerator (dfR-dfF) and
    the degrees of freedom for the denominator (dfF).

    Usage:   fprob(dfnum, dfden, F) where usually dfnum=dfbn, dfden=dfwn
    """
    if high:
        dfnum = lib.n2d(dfnum)
        dfden = lib.n2d(dfden)
        F = lib.n2d(F)
        a = D('0.5')*dfden
        b = D('0.5')*dfnum
        x = dfden/(dfden + dfnum*F)
        logging.debug('a: %s' % a)
        logging.debug('b: %s' % b)
        logging.debug('x: %s' % x)
        p = betai(a, b, x, high=high)
    else:
        p = betai(0.5*dfden, 0.5*dfnum, dfden/float(dfden+dfnum*F), high=high)
    return p

def moment(a, moment=1, dimension=None):
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
    if dimension == None:
        a = np.ravel(a)
        dimension = 0
    if moment == 1:
        return 0.0
    else:
        mn = amean(a, dimension, 1)  ## 1=keepdims
        s = np.power((a-mn), moment)
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
        logging.info(f'Number of zeros in askew: {asum(zero)}')
    denom = denom + zero   ## prevent divide-by-zero
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
    if dimension == None:
        s = np.sum(np.ravel(a))
    elif isinstance(dimension, (int, float)):
        s = np.add.reduce(a, dimension)
        if keepdims == 1:
            shp = list(a.shape)
            shp[dimension] = 1
            s = np.reshape(s,shp)
    else:  ## must be a SEQUENCE of dims to sum over
        dims = list(dimension)
        dims.sort()
        dims.reverse()
        s = a *1.0
        for dim in dims:
            s = np.add.reduce(s,dim)
        if keepdims == 1:
            shp = list(a.shape)
            for dim in dims:
                shp[dim] = 1
            s = np.reshape(s,shp)
    return s

def cumsum (inlist):
    """
    From stats.py. No changes except renamed function.
    ------------------------------------
    Returns a list consisting of the cumulative sum of the items in the
    passed list.

    Usage:   cumsum(inlist)
    """
    newlist = copy.deepcopy(inlist)
    for i in range(1,len(newlist)):
        newlist[i] = newlist[i] + newlist[i-1]
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
        logging.info(f'Number of zeros in akurtosis: {asum(zero)}')
    denom = denom + zero   ## prevent divide-by-zero
    return (np.where(zero, 0, moment(a, 4, dimension) / denom) 
        - FISHER_KURTOSIS_ADJUSTMENT)

def achisqprob(chisq, df):
    """
    From stats.py.  No changes except renamed function, N->np, print updated.
    ------------------------------------
    Returns the (1-tail) probability value associated with the provided
    chi-square value and df.  Heavily modified from chisq.c in Gary Perlman's
    |Stat.  Can handle multiple dimensions.

    Usage: chisqprob(chisq,df)    chisq=chisquare stat., df=degrees of freedom
    """
    BIG = 200.0
    def ex(x):
        BIG = 200.0
        exponents = np.where(np.less(x,-BIG),-BIG,x)
        return np.exp(exponents)

    if type(chisq) != np.ndarray:
        chisq = np.array([chisq])
    if df < 1:
        return np.ones(chisq.shape, np.float)
    probs = np.zeros(chisq.shape, np.float_)
    probs = np.where(np.less_equal(chisq,0), 1.0, probs)  ##set prob=1 for chisq<0
    a = 0.5 * chisq
    if df > 1:
        y = ex(-a)
    if df%2 == 0:
        even = 1
        s = y*1
        s2 = s*1
    else:
        even = 0
        s = 2.0 * azprob(-np.sqrt(chisq))
        s2 = s*1
    if (df > 2):
        chisq = 0.5 * (df - 1.0)
        if even:
            z = np.ones(probs.shape, np.float_)
        else:
            z = 0.5 *np.ones(probs.shape, np.float_)
        if even:
            e = np.zeros(probs.shape, np.float_)
        else:
            e = np.log(np.sqrt(np.pi)) *np.ones(probs.shape, np.float_)
        c = np.log(a)
        mask = np.zeros(probs.shape)
        a_big = np.greater(a, BIG)
        a_big_frozen = -1 *np.ones(probs.shape, np.float_)
        totalelements = np.multiply.reduce(np.array(probs.shape))
        while asum(mask)!=totalelements:
            e = np.log(z) + e
            s = s + ex(c*z-a-e)
            z = z + 1.0
    #            print (z, e, s)
            newmask = np.greater(z,chisq)
            a_big_frozen = np.where(
                newmask*np.equal(mask,0)*a_big, s, a_big_frozen)
            mask = np.clip(newmask + mask, 0, 1)
        if even:
            z = np.ones(probs.shape, np.float_)
            e = np.ones(probs.shape, np.float_)
        else:
            z = 0.5 *np.ones(probs.shape, np.float_)
            e = 1.0 / np.sqrt(np.pi) / np.sqrt(a) * np.ones(probs.shape,
                                                            np.float_)
        c = 0.0
        mask = np.zeros(probs.shape)
        a_notbig_frozen = -1 *np.ones(probs.shape, np.float_)
        while asum(mask)!=totalelements:
            e = e * (a/z.astype(np.float_))
            c = c + e
            z = z + 1.0
    #            print ('#2', z, e, c, s, c*y+s2)
            newmask = np.greater(z, chisq)
            a_notbig_frozen = np.where(
                newmask*np.equal(mask,0)*(1-a_big), c*y+s2, a_notbig_frozen)
            mask = np.clip(newmask+mask,0,1)
        probs = np.where(
            np.equal(probs,1),1,
            np.where(np.greater(a,BIG), a_big_frozen, a_notbig_frozen))
        return probs
    else:
        return s

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
    if dimension == None:
        a = np.ravel(a)
        dimension = 0
    b2 = skew(a, dimension)
    n = float(a.shape[dimension])
    rooted_var0 = ((n+1)*(n+3)) / (6.0*(n-2))
    y = b2 * np.sqrt(rooted_var0)
    beta2 = ( 3.0*(n*n+27*n-70)*(n+1)*(n+3) ) / ( (n-2.0)*(n+5)*(n+7)*(n+9) )
    rooted_var1 = 2*(beta2-1)
    W2 = -1 + np.sqrt(rooted_var1)
    rooted_var2 = np.log(np.sqrt(W2))
    delta = 1/np.sqrt(rooted_var2)
    rooted_var3 = 2/(W2-1)
    alpha = np.sqrt(rooted_var3)
    y = np.where(y==0,1,y)
    rooted_var4 = (y/alpha)**2+1
    if rooted_var4 >= 0:
        Z = delta*np.log(y/alpha + np.sqrt(rooted_var4))
        c = (1.0-azprob(Z))*2
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
    if dimension == None:
        a = np.ravel(a)
        dimension = 0
    n = float(a.shape[dimension])
    if n < 20:
        logging.warning(
            f'kurtosistest only valid for n>=20 ... continuing anyway, n={n}')
    kurt = kurtosis(a, dimension)  ## I changed the kurtosis code to subtract the Fischer Adjustment (3)
    b2 = kurt + FISHER_KURTOSIS_ADJUSTMENT  ## added so that b2 is exactly as it would have been in the original stats.py
    E = 3.0*(n-1) /(n+1)
    varb2 = 24.0*n*(n-2)*(n-3) / ((n+1)*(n+1)*(n+3)*(n+5))
    x = (b2-E)/np.sqrt(varb2)
    try:
        sqrtbeta1 = 6.0*(n*n-5*n+2)/((n+7)*(n+9)) * np.sqrt((6.0*(n+3)*(n+5))/
                                                           (n*(n-2)*(n-3)))
    except ZeroDivisionError:
        raise Exception(
            'Unable to calculate kurtosis test. Zero division error')
    A = 6.0 + 8.0/sqrtbeta1 *(2.0/sqrtbeta1 + np.sqrt(1+4.0/(sqrtbeta1**2)))
    term1 = 1 -2/(9.0*A)
    denom = 1 +x*np.sqrt(2/(A-4.0))
    denom = np.where(np.less(denom,0), 99, denom)
    term2 = np.where(np.equal(denom,0), term1, np.power((1-2.0/A)/denom,1/3.0))
    Z = ( term1 - term2 ) / np.sqrt(2/(9.0*A))
    Z = np.where(np.equal(denom,99), 0, Z)
    return Z, (1.0-azprob(Z))*2, kurt  ## I want to return the Fischer Adjusted kurtosis, not b2

def normaltest(a, dimension=None):
    """
    From stats.py.  No changes except renamed function, some vars names, N->np,
    included in return the results for skew and kurtosis, and handled errors in
    individual parts e.g. skew.

    This function tests the null hypothesis that a sample comes from a normal
    distribution. It is based on D'Agostino and Pearson's test that combines
    skew and kurtosis to produce an omnibus test of normality.

    D'Agostino, R. B. and Pearson, E. S. (1971), "An Omnibus Test of Normality
    for Moderate and Large Sample Size," Biometrika, 58, 341-348

    D'Agostino, R. B. and Pearson, E. S. (1973), "Testing for departures from
    Normality," Biometrika, 60, 613-622.
    ------------------------------------
    Tests whether skew and/OR kurtosis of dataset differs from normal
    curve.  Can operate over multiple dimensions.  Dimension can equal
    None (ravel array first), an integer (the dimension over which to
    operate), or a sequence (operate over multiple dimensions).

    Usage:   normaltest(a,dimension=None)
    Returns: z-score and 2-tail probability
    """
    if dimension == None:
        a = np.ravel(a)
        dimension = 0
    try:
        zskew, unused, cskew = skewtest(a, dimension)
    except Exception:
        zskew = None
        cskew = None
    try:
        zkurtosis, unused, ckurtosis = kurtosistest(a, dimension)
    except Exception:
        zkurtosis = None
        ckurtosis = None
    try:
        k2 = np.power(zskew, 2) + np.power(zkurtosis, 2)
        p_arr = achisqprob(k2, 2)
    except Exception:
        k2 = None
        p_arr = None
    return k2, p_arr, cskew, zskew, ckurtosis, zkurtosis

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
    n = [0.0]*k
    v = [0.0]*k
    m = [0.0]*k
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
            t1 = (n[j]-1.5)*n[j]*(nargs[j][i]-m[j])**2
            t2 = 0.5*v[j]*(n[j]-1.0)
            t3 = (n[j]-1.0)*(n[j]-2.0)
            if t3 == 0:
                raise Exception(
                    'Unable to calculate obrientransform because t3 is zero.')
            nargs[j][i] = (t1-t2) / float(t3)
    ## Check for convergence before allowing results to be returned
    for j in range(k):
        if v[j] - mean(nargs[j]) > TINY:
            logging.debug(f'Diff: {v[j] - mean(nargs[j])}')
            logging.debug(f'\nv[j]: {repr(v[j])}')
            logging.debug(f'\nnargs[j]: {nargs[j]}')
            logging.debug(f'\nmean(nargs[j]): {repr(mean(nargs[j]))}')
            raise ValueError('Lack of convergence in obrientransform.')
    return nargs

def sim_variance(samples, threshold=0.05):
    """
    Returns bolsim, p

    From stats.py. From inside lpaired. F_oneway changed to anova and no need to
    column extract to get transformed samples.

    Plus not only able to use 0.05 as threshold. Also changed return.
    ------------------------------------
    Comparing variances.

    Using O'BRIEN'S TEST FOR HOMOGENEITY OF VARIANCE, Maxwell & delaney, p.112
    """
    r = obrientransform(*samples)
    trans_samples = [r[0], r[1]]
    labels = ['sample a', 'sample b']
    p, *_unused = anova(trans_samples, labels)
    bolsim = (p >= threshold)
    return bolsim, p
