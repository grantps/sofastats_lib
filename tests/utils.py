from collections.abc import Sequence
import re
from typing import Any

import pandas as pd
from sofastats.utils.misc import display_float_as_nice_str

def display_float_fraction_as_nice_pct_str(*, float_fraction: float, decimal_points: int = 3) -> str:
    raw_pct = round(100 * float_fraction, decimal_points)
    return display_float_as_nice_str(raw=raw_pct, decimal_points=decimal_points, show_pct=False)

def display_amount_as_nice_str(raw: float, *, decimal_points: int = 3) -> str:
    return display_float_as_nice_str(raw, decimal_points=decimal_points, show_pct=False)

def display_pct_as_nice_str(raw: float, *, decimal_points: int = 3) -> str:
    return display_float_as_nice_str(raw, decimal_points=decimal_points, show_pct=True)

def strip_unnecessary_decimal_point_from_str_val(raw: str) -> str:
    if raw[-2:] == '.0':
        new = raw.removesuffix('.0')
    else:
        new = raw
    return new

def contains_subsequence(*, sequence: Sequence[Any], subsequence: Sequence[Any], debug=False) -> bool:
    found = False
    for i in range(len(sequence) - len(subsequence) + 1):
        slice2check = list(sequence[i:i + len(subsequence)])
        list2check_against = list(subsequence)
        if slice2check == list2check_against:
            found = True
            break
    if debug:
        if found:
            print(f"Found {subsequence} in {sequence}")
        else:
            print(f"Didn't find {subsequence} in {sequence}")
    return found

def found_amount_sequence_in_html_table(*, text: str, vals2find: Sequence[str | float], debug=False):
    """
    Can I see if there is a sequence of 97, 171.123, 50, 318.678 in the total sequence?
    Why Yes I can :-)
    """
    m = re.findall(r"<td.+?>(\d+(?:\.\d+)?)</td>", text, flags=re.MULTILINE)  ## (\d+(?:\.\d+)?) as per https://stackoverflow.com/questions/46205807/extracting-decimal-numbers-from-string-with-python-regex
    if debug:
        print(f"Raw result of findall regex:\n{m}")
    all_str_vals = [strip_unnecessary_decimal_point_from_str_val(str(val)) for val in m]
    str_vals2find = [str(val) for val in vals2find]
    return contains_subsequence(sequence=all_str_vals, subsequence=str_vals2find, debug=debug)

def sort_index_following_pattern(series: pd.Series, *, sorted_items_providing_pattern: Sequence[Any]):
    """
    Apply a new index which, when sorted, will be in the desired order
    """
    idxs_in_sorted_list = [''.join(sorted_items_providing_pattern).index(s) for s in series]
    new_index = pd.Series(idxs_in_sorted_list)
    return new_index
