from typing import Any

from sofastats.conf.main import DbeName, DbeSpec, SortOrder, SortOrderSpecs
from sofastats.data_extraction.db import ExtendedCursor
from sofastats.data_extraction.interfaces import ValFilterSpec
from sofastats.stats_calc.interfaces import PairedSamples, Sample
from sofastats.utils.misc import apply_custom_sorting_to_values

def to_sorted_values(*, orig_vals: list[Any], field_name: str,
        sort_orders: SortOrderSpecs, sort_order: SortOrder) -> list[Any]:
    if sort_order == SortOrder.VALUE:
        sorted_series_vals = sorted(orig_vals)
    elif sort_order == SortOrder.CUSTOM:
        sorted_series_vals = apply_custom_sorting_to_values(
            variable_name=field_name, values=orig_vals, sort_orders=sort_orders)
    else:
        raise Exception(f"Unexpected sort_order ({sort_order})"
            "\nINCREASING and DECREASING not allowed when multiple series of charts.")
    return sorted_series_vals

def get_paired_data(*, cur: ExtendedCursor, dbe_spec: DbeSpec, source_table_name: str,
        variable_a_name: str, variable_b_name: str,
        table_filter_sql: str | None = None, unique=False) -> PairedSamples:
    """
    For each field, returns a list of all non-missing values where there is also a non-missing value in the other field.
    Used in, for example, the paired samples t-test.

    Args:
        unique: if True only look at unique pairs. Useful for scatter plotting.
    """
    variable_a_name_quoted = dbe_spec.entity_quoter(variable_a_name)
    variable_b_name_quoted = dbe_spec.entity_quoter(variable_b_name)
    source_table_name_quoted = dbe_spec.entity_quoter(source_table_name)
    AND_table_filter_sql = f"AND {table_filter_sql}" if table_filter_sql else ''
    if unique:
        sql_get_pairs = f"""\
        SELECT {variable_a_name_quoted }, {variable_b_name_quoted}
        FROM {source_table_name_quoted}
        WHERE {variable_a_name_quoted } IS NOT NULL
        AND {variable_b_name_quoted} IS NOT NULL {AND_table_filter_sql}
        GROUP BY {variable_a_name_quoted }, {variable_b_name_quoted}"""
    else:
        sql_get_pairs = f"""\
        SELECT {variable_a_name_quoted }, {variable_b_name_quoted}
        FROM {source_table_name_quoted}
        WHERE {variable_a_name_quoted } IS NOT NULL
        AND {variable_b_name_quoted} IS NOT NULL {AND_table_filter_sql}"""
    cur.exe(sql_get_pairs)
    a_b_val_tuples = cur.fetchall()
    ## SQLite sometimes returns strings even if REAL
    variable_a_vals = [float(x[0]) for x in a_b_val_tuples]
    variable_b_vals = [float(x[1]) for x in a_b_val_tuples]
    return PairedSamples(
        sample_a=Sample(label=f'Sample A - {variable_a_name}', vals=variable_a_vals),
        sample_b=Sample(label=f'Sample B - {variable_b_name}', vals=variable_b_vals),
    )

def get_paired_diffs_sample(*, cur: ExtendedCursor, dbe_spec: DbeSpec, source_table_name: str,
        variable_a_name: str, variable_b_name: str, table_filter_sql: str | None = None) -> Sample:
    """
    For every pair of A and B get the difference - those are the values in this sample.
    """
    ## prepare items
    variable_a_name_quoted = dbe_spec.entity_quoter(variable_a_name)
    variable_b_name_quoted = dbe_spec.entity_quoter(variable_b_name)
    source_table_name_quoted = dbe_spec.entity_quoter(source_table_name)
    AND_table_filter_sql = f"AND {table_filter_sql}" if table_filter_sql else ''
    ## assemble SQL
    sql = f"""\
    SELECT {variable_a_name_quoted} - {variable_b_name_quoted} AS diff
    FROM {source_table_name_quoted}
    WHERE {variable_a_name_quoted} IS NOT NULL
    AND {variable_b_name_quoted} IS NOT NULL {AND_table_filter_sql}"""
    ## get data
    cur.exe(sql)
    data = cur.fetchall()
    sample_vals = [row[0] for row in data]
    ## coerce into floats because SQLite sometimes returns strings even if REAL TODO: reuse coerce logic and desc
    if dbe_spec.dbe_name == DbeName.SQLITE:
        sample_vals = [float(val) for val in sample_vals]
    sample_desc = f'difference between "{variable_a_name}" and "{variable_b_name}"'
    if len(sample_vals) < 2:
        raise Exception(f"Too few values for {sample_desc} in sample for analysis.")
    sample = Sample(label=sample_desc.title(), vals=sample_vals)
    return sample

def get_sample(*, cur: ExtendedCursor, dbe_spec: DbeSpec, source_table_name: str,
        measure_field_name: str, grouping_filt: ValFilterSpec | None = None,
        table_filter_sql: str | None = None) -> Sample:
    """
    Get list of non-missing values in numeric measure field for a group defined by another field
    e.g. getting weights for males.
    Must return list of floats.
    SQLite sometimes returns strings even though REAL data type. Not known why.
    Used, for example, in the independent samples t-test.
    Note - various filters might apply e.g. we want a sample for male weight
    but only where age > 10

    Args:
        source_table_name: name of table containing the data
        measure_field_name: e.g. weight
        grouping_filt: the grouping variable details
        table_filter_sql: clause ready to put after AND in a WHERE filter.
            E.g. WHERE ... AND age > 10
            Sometimes there is a global filter active in SOFA for a table e.g. age > 10,
            and we will need to apply that filter to ensure we are only getting the correct values
    """
    ## prepare items
    AND_table_filter_sql = f"AND {table_filter_sql}" if table_filter_sql else ''
    if grouping_filt:
        if grouping_filt.val_is_numeric:
            grouping_filt_clause = f"{dbe_spec.entity_quoter(grouping_filt.variable_name)} = {grouping_filt.value}"
        else:
            grouping_filt_clause = f"{dbe_spec.entity_quoter(grouping_filt.variable_name)} = '{grouping_filt.value}'"
        and_grouping_filt_clause = f"AND {grouping_filt_clause}"
    else:
        and_grouping_filt_clause = ''
    source_table_name_quoted = dbe_spec.entity_quoter(source_table_name)
    measure_field_name_quoted = dbe_spec.entity_quoter(measure_field_name)
    ## assemble SQL
    sql = f"""
    SELECT {measure_field_name_quoted}
    FROM {source_table_name_quoted}
    WHERE {measure_field_name_quoted} IS NOT NULL
    {AND_table_filter_sql}
    {and_grouping_filt_clause}
    """
    ## get data
    cur.exe(sql)
    data = cur.fetchall()
    sample_vals = [row[0] for row in data]
    ## coerce into floats because SQLite sometimes returns strings even if REAL TODO: reuse coerce logic and desc
    if dbe_spec.dbe_name == DbeName.SQLITE:
        sample_vals = [float(val) for val in sample_vals]
    if len(sample_vals) < 2:
        raise Exception(f"Too few {measure_field_name} values in sample for analysis "
            f"when getting sample for {and_grouping_filt_clause}")
    label = grouping_filt.value if grouping_filt else ''
    sample = Sample(label=label, vals=sample_vals)
    return sample
