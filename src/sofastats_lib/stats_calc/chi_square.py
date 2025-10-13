from collections.abc import Sequence
from collections import defaultdict
from dataclasses import dataclass

from numpy import reshape

@dataclass(frozen=False)
class WorkedResultCell:
    observed_value: int
    row_sum: int  ## sum of the row this value is from
    col_sum: int  ## sum of the column this value is from
    expected_value: float
    min_of_observed_and_expected: float
    max_of_observed_and_expected: float
    diff_of_min_and_max: float
    diff_squared: float
    pre_chi: float

@dataclass(frozen=True)
class WorkedResult:
    grand_tot: int
    row_n2row_sum: dict[int, int]
    row_n2obs_row: dict[int, Sequence[int]]
    col_n2col_sum: dict[int, int]
    col_n2obs_row: dict[int, Sequence[int]]
    row_n: int
    col_n: int
    row_n_minus_1: int
    col_n_minus_1: int
    cells_data: dict[tuple[int, int], WorkedResultCell]
    pre_chis: Sequence[float]
    chi_square: float
    degrees_of_freedom: int

def get_worked_result(*, variable_a_values: Sequence[int | str], variable_b_values: Sequence[int | str],
        observed_values_a_then_b_ordered: Sequence[float],
        degrees_of_freedom: int) -> WorkedResult:
    n_a = len(variable_a_values)
    n_b = len(variable_b_values)
    ## Restructure observed_values_a_then_b_ordered to nested lists following pattern of contingency table
    ## The lists are b within a e.g. a1b1, a1b2, a1b3, a2b1, a2b2 ...
    ## (i.e. across the rows)
    obs = reshape(observed_values_a_then_b_ordered, (n_a, n_b))
    grand_total = sum(observed_values_a_then_b_ordered)
    row_n2row_sum = defaultdict(int)
    col_n2col_sum = defaultdict(int)
    row_n2obs_row = defaultdict(list)
    col_n2obs_row = defaultdict(list)
    coord2observed = dict()
    ## round 1
    for col_n, _val_b in enumerate(variable_b_values, 1):
        for row_n, _val_a in enumerate(variable_a_values, 1):
            observed_value = int(obs[row_n - 1][col_n - 1])  ## need zero-based indexing for numpy to get our individual value
            row_n2row_sum[row_n] += observed_value
            col_n2col_sum[col_n] += observed_value
            row_n2obs_row[row_n].append(observed_value)
            col_n2obs_row[col_n].append(observed_value)
            coord2observed[(row_n, col_n)] = observed_value  ## can't add any more details until calculated row and column totals
    ## round 2 (now that we have row and column totals we can calculate the missing bits)
    cells_data = {}
    pre_chis = []
    chi_square = 0
    for coord, observed_value in coord2observed.items():
        row_n, col_n = coord
        row_sum = row_n2row_sum[row_n]
        col_sum = col_n2col_sum[col_n]
        expected_value = (row_sum * col_sum) / float(grand_total)
        min_of_observed_and_expected = min([observed_value, expected_value])
        max_of_observed_and_expected = max([observed_value, expected_value])
        diff_of_min_and_max = max_of_observed_and_expected - min_of_observed_and_expected
        diff_of_min_and_max = round(diff_of_min_and_max, 3)
        min_of_observed_and_expected = round(min_of_observed_and_expected, 3)
        max_of_observed_and_expected = round(max_of_observed_and_expected, 3)
        diff_squared = round(diff_of_min_and_max ** 2, 3)
        raw_pre_chi = diff_squared / float(expected_value)
        chi_square += raw_pre_chi
        pre_chi = round(raw_pre_chi, 3)
        pre_chis.append(pre_chi)
        cell_data = WorkedResultCell(
            observed_value=observed_value,
            row_sum=row_sum,
            col_sum=col_sum,
            expected_value=round(expected_value, 3),
            min_of_observed_and_expected=min_of_observed_and_expected,
            max_of_observed_and_expected=max_of_observed_and_expected,
            diff_of_min_and_max=diff_of_min_and_max,
            diff_squared=diff_squared,
            pre_chi=pre_chi,
        )
        cells_data[coord] = cell_data
    return WorkedResult(
        grand_tot=grand_total,
        row_n2row_sum=row_n2row_sum,
        row_n2obs_row=row_n2obs_row,
        col_n2col_sum=col_n2col_sum,
        col_n2obs_row=col_n2obs_row,
        row_n=n_a,
        col_n=n_b,
        row_n_minus_1=n_a - 1,
        col_n_minus_1=n_b - 1,
        cells_data=cells_data,
        pre_chis=pre_chis,
        chi_square=chi_square,
        degrees_of_freedom=degrees_of_freedom,
    )
