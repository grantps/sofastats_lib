import pandas as pd

from sofastats_lib.stats_calc.interfaces import Sample

def get_samples_from_df(df: pd.DataFrame, *, n_expected_groups: int | None = None) -> list[Sample]:
    df.columns = ['group', 'val']
    group_vals = df['group'].unique()
    if n_expected_groups is None:
        if len(group_vals) != n_expected_groups:
            raise ValueError(f"Expected {n_expected_groups:,} group values but received {len(group_vals):,}")
    else:
        if not 2 <= len(group_vals) <= 15:
            raise ValueError(f"Expected between 2 and 15 group values but received {len(group_vals):,}")
    samples = []
    for group_val in group_vals:
        vals = list(df.loc[df['group'] == group_val, 'val'])
        sample = Sample(lbl=str(group_val), vals=vals)
        samples.append(sample)
    return samples

def get_optimal_axis_bounds(x_axis_min_val: float, x_axis_max_val: float, *, debug=False) -> tuple[float, float]:
    """
    Useful for boxplots and scatterplots.

    axis_min -- the minimum y value exactly
    axis_max -- the maximum y value exactly

    Generally, we want box and scatter plots to have y-axes starting from just
    below the minimum point (e.g. lowest outlier). That is to avoid the common case
    where we have the y-axis start at 0, and all our values range tightly
    together. In which case, for boxplots, we will have a series of tiny
    boxplots up the top, and we won't be able to see the different parts of it
    e.g. LQ, median etc. For scatter plots our data will be too tightly
    scrunched up to see any spread.

    But sometimes the lowest point is not that far above 0, in which case we
    should set it to 0. A 0-based axis is preferable unless the values are a
    long way away. Going from 0.5-12 is silly. Might as well go from 0-12.
    4 scenarios:

    1) min and max are both the same
    Just try to set the max differently to the min so there is a range on the
    axis to display. See implementation for more details.

    2) min and max are both +ve
    |   *
    |
    -------
    Snap min to 0 if gap small rel to range, otherwise make min y-axis just
    below min point. Make max y-axis just above the max point. Make the
    padding from 0 the least of 0.1 of axis_min and 0.1 of val_range. The
    outer padding can be the least of the axis_max and 0.1 of val_range.

    3) min and max are -ve
    -------
    |   *
    |
    Snap max to 0 if gap small rel to range, otherwise make max y-axis just
    above max point. Make min y-axis just below min point. Make the
    padding the least of 0.1 of gap and 0.1 of val_range.

    4) min is -ve and max is +ve
    |   *
    -------
    |   *
    Make max 1.1 * axis_max. No harm if 0.
    Make min 1.1 * axis_min. No harm if 0.
    """
    if debug: print(f"Orig min max: {x_axis_min_val} {x_axis_max_val}")
    if x_axis_min_val == x_axis_max_val:
        my_val = x_axis_min_val
        if my_val < 0:
            x_axis_min_val = 1.1 * my_val
            x_axis_max_val = 0
        elif my_val == 0:
            x_axis_min_val = -1
            x_axis_max_val = 1
        elif my_val > 0:
            x_axis_min_val = 0
            x_axis_max_val = 1.1 * my_val
    elif x_axis_min_val >= 0 and x_axis_max_val >= 0:  ## both +ve
        """
        Snap min to 0 if gap small rel to range, otherwise make min y-axis just
        below min point. Make max y-axis just above the max point. Make the
        padding from 0 the lesser of 0.1 of axis_min and 0.1 of val_range. The
        outer padding can be the lesser of the axis_max and 0.1 of val_range.
        """
        gap = x_axis_min_val
        val_range = (x_axis_max_val - x_axis_min_val)
        try:
            gap2range = gap / (val_range * 1.0)
            if gap2range < 0.6:  ## close enough to snap to 0
                x_axis_min_val = 0
            else:  ## can't just be 0.9 min - e.g. looking at years from 2000-2010 would be 1800 upwards!
                x_axis_min_val -= min(0.1 * gap, 0.1 * val_range)  ## gap is never 0 and is at least 0.6 of valrange
        except ZeroDivisionError:
            pass
        x_axis_max_val += min(0.1 * x_axis_max_val, 0.1 * val_range)
    elif x_axis_min_val <= 0 and x_axis_max_val <= 0:  ## both -ve
        """
        Snap max to 0 if gap small rel to range, otherwise make max y-axis just
        above max point. Make min y-axis just below min point. Make the padding
        the lesser of 0.1 of gap and 0.1 of val_range.
        """
        gap = abs(x_axis_max_val)
        val_range = abs(x_axis_max_val - x_axis_min_val)
        try:
            gap2range = gap / (val_range * 1.0)
            if gap2range < 0.6:
                x_axis_max_val = 0
            else:
                x_axis_max_val += min(0.1 * gap, 0.1 * val_range)
        except ZeroDivisionError:
            pass
        x_axis_min_val -= min(0.1 * abs(x_axis_min_val), 0.1 * val_range)  ## make even more negative, but by the least possible
    elif x_axis_min_val <= 0 <= x_axis_max_val:  ## spanning y-axis (even if all 0s ;-))
        """
        Pad min with 0.1 * x_axis_min_val. No harm if 0.
        Pad max - no harm if 0.
        """
        x_axis_min_val = 1.1 * x_axis_min_val
        x_axis_max_val = 1.1 * x_axis_max_val
    else:
        pass
    if debug: print(f"Final {x_axis_min_val=}; Final {x_axis_max_val=}")
    return x_axis_min_val, x_axis_max_val
