from collections.abc import Sequence

from sofastats.stats_calc.engine import rankdata
from sofastats.stats_calc.interfaces import SpearmansInitTbl, SpearmansResult

def get_worked_result(*,
        variable_a_values: Sequence[float], variable_b_values: Sequence[float]) -> SpearmansResult:
    n_x = len(variable_a_values)
    if n_x != len(variable_b_values):
        raise Exception(f'Different sample sizes ({n_x} vs {len(variable_b_values)})')
    rankx = rankdata(variable_a_values, high_volume_ok=False)
    x_and_rank = list(zip(variable_a_values, rankx))
    x_and_rank.sort()
    x2rank = dict(x_and_rank)
    ranky = rankdata(variable_b_values, high_volume_ok=False)
    y_and_rank = list(zip(variable_b_values, ranky))
    y_and_rank.sort()
    y2rank = dict(y_and_rank)
    n_cubed_minus_n = (n_x ** 3) - n_x

    diff_squareds = []
    initial_tbl = []
    for x, y in zip(variable_a_values, variable_b_values):
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
    return SpearmansResult(
        initial_tbl=initial_tbl,
        x_and_rank=x_and_rank,
        y_and_rank=y_and_rank,
        n_x=n_x,
        n_cubed_minus_n=n_cubed_minus_n,
        tot_d_squared=round(tot_d_squared, 2),
        tot_d_squared_x_6=round(6 * tot_d_squared, 2),
        pre_rho=round(pre_rho, 4),
        rho=round(rho, 4),
    )
