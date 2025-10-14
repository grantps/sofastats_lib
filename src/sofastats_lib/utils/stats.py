"""
Needed by dc's in conf.misc as well as other code
so putting it here at the lowest level so only one direction through layers
"""
from collections.abc import Sequence
from typing import Callable

from sofastats_lib.utils.maths import to_precision

def get_quartiles(vals):
    """
    From Wild & Seber Introduction to Probability and Statistics 1996 pp.74-77
    Depth of quartiles is (int(n/2)+1)/2
    (from left for LQ and from right for UQ).
    """
    new_vals = vals[:]
    new_vals.sort()  ## leaving vals untouched
    n = len(new_vals)
    if not n:
        raise Exception('No values supplied to get_quartiles.')
    depth = (int(n / 2.0) + 1.0) / 2.0
    l_depth = int(depth)
    ## NB zero-based so subtract 1 for position going upwards
    if int(depth) == depth:
        lq = new_vals[l_depth - 1]
        uq = new_vals[-l_depth]
    else:  ## int truncates towards 0 but depth is always a positive number
        ## 1,3,4,5,60 depth = 5/2 i.e. [2.5] i.e. 2 -> 2+1 i.e. 3 -> 3/2 i.e. 1.5
        # so lq = (1+3)/2 i.e. 2 and uq = (5+60)/2 i.e. 32.5
        u_depth = int(depth) + 1
        lq = (new_vals[l_depth - 1] + new_vals[u_depth - 1]) / 2.0
        uq = (new_vals[-l_depth] + new_vals[-u_depth]) / 2.0
    return lq, uq

## TODO: clarify what goes in here and what in sofastats_lib.output.utils

def get_p_str(p: float) -> str:
    """
    Get a nice representation of p value including significance if relevant.
    """
    p_str = to_precision(num=p, precision=4)
    if p < 0.001:
        p_str = f'< 0.001 ({p_str})'
    return p_str

def get_obriens_msg(samples_vals: Sequence[Sequence[float]], sim_variance_fn: Callable, *,
        high=False, debug=False) -> str:
    try:
        ## sim_variance threshold parameter not used or relevant because ignoring is_similar part of output
        _is_similar, p_sim = sim_variance_fn(samples_vals, high=high)
        obriens_msg = get_p_str(p_sim)
    except Exception as e:
        if debug: print(f"Unable to calculate O'Briens test for homogeneity of variance.\nOrig error: {e}")
        obriens_msg = "Unable to calculate O'Briens test for homogeneity of variance"
    return obriens_msg
