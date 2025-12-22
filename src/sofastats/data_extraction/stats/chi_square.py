from collections.abc import Sequence
from dataclasses import dataclass
from itertools import product
from typing import Any

from sofastats import logger
from sofastats.conf.main import (
    MAX_CHI_SQUARE_VALS_IN_DIM, MAX_CHI_SQUARE_CELLS, MAX_VALUE_LENGTH_IN_SQL_CLAUSE, MIN_CHI_SQUARE_VALS_IN_DIM,
    DbeName, DbeSpec)
from sofastats.conf.var_labels import SortOrderSpecs
from sofastats.data_extraction.db import ExtendedCursor

@dataclass(frozen=True)
class ChiSquareData:
    """
    Everything we can derive from the source data before we actually do the statistical analysis.
    """
    variable_a_values: Sequence[int | str]  ## e.g. Korea, NZ, USA found in variable A (that also had values in variable B)
    variable_b_values: Sequence[int | str]  ## e.g. Badminton, Basketball, Football, Tennis found in variable B (that also had values in variable A)
    observed_values_a_then_b_ordered: list[float]
    expected_values_a_then_b_ordered: list[float]  ## maintains same order so they can be compared by cell AND so we can populate the observed vs expected table just based on order
    minimum_cell_count: int
    pct_cells_freq_under_5: float
    degrees_of_freedom: int

def get_fractions_of_total_for_variable(*, cur: ExtendedCursor, dbe_spec: DbeSpec,
        src_tbl_name: str, tbl_filt_clause: str, variable_name: str, other_variable_name: str,
        ordered_values: Sequence[Any] | None = None) -> list[float]:
    """
    Looking at the frequencies for each value in the variable, what fractional share does that value have of the total?
    For example, if the numbers are 5, 8, and 7 for young, middle, and old
    then the fractions are .25, .40, .35
    When calculating the frequencies for the variable,
    leave out any rows in the source data where either the variable or the other variable are missing.
    We are only counting frequencies for each intersection of values (non-NULL).

    Order by value order supplied, not by value itself.
    E.g. if the user wants '<20' to come before '20-29' etc then honour that. Simple to get the SQL to do this.
    """
    ## prepare items
    quoted_src_tbl_name = dbe_spec.entity_quoter(src_tbl_name)
    quoted_variable_name = dbe_spec.entity_quoter(variable_name)
    quoted_other_variable_name = dbe_spec.entity_quoter(other_variable_name)
    ## handle value order for main variable
    if ordered_values:
        sorter_clause_bits = [f"CASE {quoted_variable_name}", ]
        for n, value in enumerate(ordered_values, 1):
            clause_ready_value = dbe_spec.str_value_quoter(value) if isinstance(value, str) else value
            sorter_clause_bits.append(f"WHEN {clause_ready_value} THEN {n}")
        sorter_clause_bits.append("END")
        sorter_clause = '\n'.join(sorter_clause_bits)
    else:
        sorter_clause = '1'  ## i.e. all given same sort order
    ## get data
    and_tbl_filt_clause = f"AND ({tbl_filt_clause})" if tbl_filt_clause else ''
    sql_get_fractions = f"""\
    SELECT {quoted_variable_name},
      {sorter_clause} AS sorter,
      COUNT(*) AS n
    FROM {quoted_src_tbl_name} 
    WHERE {quoted_variable_name} IS NOT NULL AND {quoted_other_variable_name} IS NOT NULL
    {and_tbl_filt_clause}
    GROUP BY {quoted_variable_name}, sorter
    ORDER BY sorter, {quoted_variable_name}
    """
    logger.debug(sql_get_fractions)
    cur.exe(sql_get_fractions)
    lst_counts = []
    total = 0
    data = cur.fetchall()
    for value, _sorter, freq in data:
        lst_counts.append(freq)
        total += freq
        if ordered_values and value not in ordered_values:
            raise Exception(f"The custom sort order you supplied for values in variable '{variable_name}' "
                f"didn't include value '{value}' so please fix that and try again.")
    lst_fracs = [( x / float(total)) for x in lst_counts]
    return lst_fracs

def get_cleaned_values(*, original_vals: list[str | float], dbe_spec: DbeSpec) -> list[str | float]:
    """
    Get values ready to use. Check there are no excessively long labels.
    """
    if dbe_spec.dbe_name == DbeName.SQLITE:
        ## SQLite sometimes returns strings even if REAL
        try:
            vals = [float(val) for val in original_vals]
            return vals
        except ValueError:
            pass  ## leave them as strings
    ## if strings, check not too long
    for val in original_vals:
        if len(val) > MAX_VALUE_LENGTH_IN_SQL_CLAUSE:
            raise ValueError(f"'{val}' is too long to be used as a category value "
                f"({len(val)} > maximum value setting: {MAX_VALUE_LENGTH_IN_SQL_CLAUSE})")
    return original_vals

def get_chi_square_data(*, cur: ExtendedCursor, dbe_spec: DbeSpec, src_tbl_name: str, tbl_filt_clause: str,
        variable_a_name: str, variable_b_name: str, sort_orders: SortOrderSpecs) -> ChiSquareData:
    """
    The Chi Square statistical calculation relies on having access to the raw counts per intersection between
    variable A and B. These are the observed values. E.g.

             Badminton | Basketball | Football | Tennis
    ---------------------------------------------------
    Korea          100           10        150        0  <=== note - all cells must be filled (0 if no rows in particular intersection of A and B values)
    NZ              15           25         25       25
    USA            100          500        150      250

    There is then a calculation of the expected values for each intersection.
    These values are calculated so that the distribution within, for example, sports, is the same for each country.
    In other words, as if there were no relationship between country and sport.
    Later on, we will look at the difference between the actual, observed values and the matching expected values.
    The important thing with the lists of actual and observed values is that they are in the same order as each other
    so they can be compared to calculate how large a difference there is between them.
    The lists are B within A (e.g. a1b1, a1b2, a1b3, a2b1, a2b2 ...) but the nature of the ordering doesn't matter,
    only the fact that it is the same between the observed and expected lists.
    Also required are some other attributes of the result, e.g. minimum cell count, that are needed to
    handle and interpret the result of the statistical calculation.

    Control the order of values for both A and B.
    Note - also need to control it inside the SQL in get_fractions_of_total_for_variable()

    See output.stats.chi_square.chi_square_from_df (similar logic with pandas base)
    """
    ## prepare items
    quoted_src_tbl_name = dbe_spec.entity_quoter(src_tbl_name)
    quoted_variable_a_name = dbe_spec.entity_quoter(variable_a_name)
    quoted_variable_b_name = dbe_spec.entity_quoter(variable_b_name)
    and_tbl_filt_clause = f"AND ({tbl_filt_clause})" if tbl_filt_clause else ''
    ## A) get ROW vals used ***********************
    sql_row_vals_used = f"""\
    SELECT {quoted_variable_a_name}
    FROM {quoted_src_tbl_name}
    WHERE {quoted_variable_a_name} IS NOT NULL AND {quoted_variable_b_name} IS NOT NULL
    {and_tbl_filt_clause}
    GROUP BY {quoted_variable_a_name}
    ORDER BY {quoted_variable_a_name}
    """
    cur.exe(sql_row_vals_used)
    row_data = cur.fetchall()
    row_vals = [x[0] for x in row_data]
    variable_a_values = get_cleaned_values(original_vals=row_vals, dbe_spec=dbe_spec)
    try:
        values_in_order = sort_orders[variable_a_name]
    except KeyError:
        pass
    else:
        value2order = {val: order for order, val in enumerate(values_in_order)}
        try:
            variable_a_values.sort(key=lambda val: value2order[val])
        except KeyError:
            raise Exception(f"The custom sort order you supplied for values in variable '{variable_a_name}' "
                "didn't include all the values in your analysis so please fix that and try again.")
    n_variable_a_vals = len(variable_a_values)
    if n_variable_a_vals > MAX_CHI_SQUARE_VALS_IN_DIM:
        raise Exception(f"Too many separate values ({n_variable_a_vals} vs "
            f"maximum allowed of {MAX_CHI_SQUARE_VALS_IN_DIM}) in variable '{quoted_variable_a_name}'")
    if n_variable_a_vals < MIN_CHI_SQUARE_VALS_IN_DIM:
        raise Exception(f"Not enough separate values ({n_variable_a_vals} vs "
            f"minimum allowed of {MIN_CHI_SQUARE_VALS_IN_DIM}) in variable '{quoted_variable_a_name}'")
    ## B) get COL vals used (almost a repeat) ***********************
    sql_col_vals_used = f"""\
    SELECT {quoted_variable_b_name}
    FROM {quoted_src_tbl_name}
    WHERE {quoted_variable_a_name} IS NOT NULL AND {quoted_variable_b_name} IS NOT NULL
    {and_tbl_filt_clause}
    GROUP BY {quoted_variable_b_name}
    ORDER BY {quoted_variable_b_name}
    """
    cur.exe(sql_col_vals_used)
    col_data = cur.fetchall()
    col_vals = [x[0] for x in col_data]
    variable_b_values = get_cleaned_values(original_vals=col_vals, dbe_spec=dbe_spec)
    try:
        values_in_order = sort_orders[variable_b_name]
    except KeyError:
        pass
    else:
        value2order = {val: order for order, val in enumerate(values_in_order)}
        try:
            variable_b_values.sort(key=lambda val: value2order[val])
        except KeyError:
            raise Exception(f"The custom sort order you supplied for values in variable '{variable_b_name}' "
                "didn't include all the values in your analysis so please fix that and try again.")
    n_variable_b_vals = len(variable_b_values)
    if n_variable_b_vals > MAX_CHI_SQUARE_VALS_IN_DIM:
        raise Exception(f"Too many separate values ({n_variable_b_vals} vs "
            f"maximum allowed of {MAX_CHI_SQUARE_VALS_IN_DIM}) in variable '{quoted_variable_b_name}'")
    if n_variable_b_vals < MIN_CHI_SQUARE_VALS_IN_DIM:
        raise Exception(f"Not enough separate values ({n_variable_b_vals} vs "
            f"minimum allowed of {MIN_CHI_SQUARE_VALS_IN_DIM}) in variable '{quoted_variable_b_name}'")
    ## C) combine results of A) and B) ***********************
    n_cells = len(variable_a_values) * len(variable_b_values)
    if n_cells > MAX_CHI_SQUARE_CELLS:
        raise Exception(f"Too many cells in Chi Square cross tab ({n_cells:,} "
            f"vs maximum allowed of {MAX_CHI_SQUARE_CELLS:,})")
    ## observed ********************************************************************************************************
    ## Build SQL to get all observed values (for each A, through B's)
    ## This order is useful when running row by row into an HTML table
    ## Get frequency per A and B intersection
    sql_get_observed_freqs_bits = ['SELECT ', ]
    freq_per_a_b_intersection_clauses_bits = []
    ## need to filter by vals within SQL so may need quoting observed values etc
    for val_a, val_b in product(variable_a_values, variable_b_values):
        quoted_val_a = dbe_spec.str_value_quoter(val_a)
        quoted_val_b = dbe_spec.str_value_quoter(val_b)
        clause = (
            f"SUM(CASE WHEN {quoted_variable_a_name} = {quoted_val_a} AND {quoted_variable_b_name} = {quoted_val_b} "
            "THEN 1 ELSE 0 END)")
        freq_per_a_b_intersection_clauses_bits.append(clause)
    freq_per_a_b_intersection_clauses = ',\n'.join(freq_per_a_b_intersection_clauses_bits)
    sql_get_observed_freqs_bits.append(freq_per_a_b_intersection_clauses)
    sql_get_observed_freqs_bits.append(f"FROM {quoted_src_tbl_name}")
    if tbl_filt_clause:
        sql_get_observed_freqs_bits.append(f"WHERE {tbl_filt_clause}")
    sql_get_observed_freqs = '\n'.join(sql_get_observed_freqs_bits)
    logger.debug(f"{sql_get_observed_freqs=}")
    cur.exe(sql_get_observed_freqs)
    observed_values_a_then_b_ordered = cur.fetchone()  ## ordered according to the order of A values and B values as supplied
    if not observed_values_a_then_b_ordered:
        raise Exception("No observed values")
    observed_values_a_then_b_ordered = list(observed_values_a_then_b_ordered)
    logger.debug(f"{observed_values_a_then_b_ordered=}")
    total_observed_values = float(sum(observed_values_a_then_b_ordered))
    ## expected values *************************************************************************************************
    fractions_of_total_for_variable_a = get_fractions_of_total_for_variable(
        cur=cur, dbe_spec=dbe_spec, src_tbl_name=src_tbl_name, tbl_filt_clause=tbl_filt_clause,
        variable_name=variable_a_name, other_variable_name=variable_b_name,
        ordered_values=sort_orders.get(variable_a_name))
    fractions_of_total_for_variable_b = get_fractions_of_total_for_variable(
        cur=cur, dbe_spec=dbe_spec, src_tbl_name=src_tbl_name, tbl_filt_clause=tbl_filt_clause,
        variable_name=variable_b_name, other_variable_name=variable_a_name,
        ordered_values=sort_orders.get(variable_b_name))
    degrees_of_freedom = (n_variable_a_vals - 1) * (n_variable_b_vals - 1)
    expected_values_a_then_b_ordered = []
    for fraction_of_val_in_variable_a, fraction_of_val_in_variable_b in product(
            fractions_of_total_for_variable_a, fractions_of_total_for_variable_b):
        expected_values_a_then_b_ordered.append(fraction_of_val_in_variable_a * fraction_of_val_in_variable_b * total_observed_values)
    logger.debug(f"{expected_values_a_then_b_ordered=}")
    if len(observed_values_a_then_b_ordered) != len(expected_values_a_then_b_ordered):
        raise Exception('Different number of observed and expected values. '
            f'{len(observed_values_a_then_b_ordered)} vs {len(expected_values_a_then_b_ordered)}')
    minimum_cell_count = min(expected_values_a_then_b_ordered)
    cells_freq_under_5 = [x for x in expected_values_a_then_b_ordered if x < 5]
    pct_cells_freq_under_5 = (100 * len(cells_freq_under_5)) / float(len(expected_values_a_then_b_ordered))
    return ChiSquareData(
        variable_a_values=variable_a_values,
        variable_b_values=variable_b_values,
        observed_values_a_then_b_ordered=observed_values_a_then_b_ordered,
        expected_values_a_then_b_ordered=expected_values_a_then_b_ordered,
        minimum_cell_count=minimum_cell_count,
        pct_cells_freq_under_5=pct_cells_freq_under_5,
        degrees_of_freedom=degrees_of_freedom,
    )
