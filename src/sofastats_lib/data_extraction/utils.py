from sofastats_lib.conf.main import DbeName, DbeSpec
from sofastats_lib.data_extraction.db import ExtendedCursor
from sofastats_lib.data_extraction.interfaces import ValFilterSpec, ValSpec
from sofastats_lib.stats_calc.interfaces import PairedSamples, Sample

def get_paired_data(*, cur: ExtendedCursor, dbe_spec: DbeSpec, src_tbl_name: str,
        variable_a_name: str, variable_a_label: str, variable_b_name: str, variable_b_label: str,
        tbl_filt_clause: str | None = None, unique=False) -> PairedSamples:
    """
    For each field, returns a list of all non-missing values where there is also a non-missing value in the other field.
    Used in, for example, the paired samples t-test.

    Args:
        unique: if True only look at unique pairs. Useful for scatter plotting.
    """
    and_tbl_filt_clause = f"AND {tbl_filt_clause}" if tbl_filt_clause else ''
    src_tbl_name_quoted = dbe_spec.entity_quoter(src_tbl_name)
    variable_a_name_quoted = dbe_spec.entity_quoter(variable_a_name)
    variable_b_name_quoted = dbe_spec.entity_quoter(variable_b_name)
    if unique:
        sql_get_pairs = f"""\
        SELECT {variable_a_name_quoted }, {variable_b_name_quoted}
        FROM {src_tbl_name_quoted}
        WHERE {variable_a_name_quoted } IS NOT NULL
        AND {variable_b_name_quoted} IS NOT NULL {and_tbl_filt_clause}
        GROUP BY {variable_a_name_quoted }, {variable_b_name_quoted}"""
    else:
        sql_get_pairs = f"""\
        SELECT {variable_a_name_quoted }, {variable_b_name_quoted}
        FROM {src_tbl_name_quoted}
        WHERE {variable_a_name_quoted } IS NOT NULL
        AND {variable_b_name_quoted} IS NOT NULL {and_tbl_filt_clause}"""
    cur.exe(sql_get_pairs)
    a_b_val_tuples = cur.fetchall()
    ## SQLite sometimes returns strings even if REAL
    variable_a_vals = [float(x[0]) for x in a_b_val_tuples]
    variable_b_vals = [float(x[1]) for x in a_b_val_tuples]
    return PairedSamples(
        sample_a=Sample(lbl=f'Sample A - {variable_a_label}', vals=variable_a_vals),
        sample_b=Sample(lbl=f'Sample B - {variable_b_label}', vals=variable_b_vals),
    )

def get_paired_diffs_sample(*, cur: ExtendedCursor, dbe_spec: DbeSpec, src_tbl_name: str,
        variable_a_name: str, variable_a_label: str, variable_b_name: str, variable_b_label: str,
        tbl_filt_clause: str | None = None) -> Sample:
    """
    For every pair of A and B get the difference - those are the values in this sample.
    """
    ## prepare items
    src_tbl_name_quoted = dbe_spec.entity_quoter(src_tbl_name)
    variable_a_name_quoted = dbe_spec.entity_quoter(variable_a_name)
    variable_b_name_quoted = dbe_spec.entity_quoter(variable_b_name)
    and_tbl_filt_clause = f"AND {tbl_filt_clause}" if tbl_filt_clause else ''
    ## assemble SQL
    sql = f"""\
    SELECT {variable_a_name_quoted} - {variable_b_name_quoted} AS diff
    FROM {src_tbl_name_quoted}
    WHERE {variable_a_name_quoted} IS NOT NULL
    AND {variable_b_name_quoted} IS NOT NULL {and_tbl_filt_clause}"""
    ## get data
    cur.exe(sql)
    data = cur.fetchall()
    sample_vals = [row[0] for row in data]
    ## coerce into floats because SQLite sometimes returns strings even if REAL TODO: reuse coerce logic and desc
    if dbe_spec.dbe_name == DbeName.SQLITE:
        sample_vals = [float(val) for val in sample_vals]
    sample_desc = f'difference between "{variable_a_label}" and "{variable_b_label}"'
    if len(sample_vals) < 2:
        raise Exception(f"Too few values for {sample_desc} in sample for analysis.")
    sample = Sample(lbl=sample_desc.title(), vals=sample_vals)
    return sample

def get_sample(*, cur: ExtendedCursor, dbe_spec: DbeSpec, src_tbl_name: str,
        measure_fld_name: str, grouping_filt: ValFilterSpec | None = None,
        tbl_filt_clause: str | None = None) -> Sample:
    """
    Get list of non-missing values in numeric measure field for a group defined by another field
    e.g. getting weights for males.
    Must return list of floats.
    SQLite sometimes returns strings even though REAL data type. Not known why.
    Used, for example, in the independent samples t-test.
    Note - various filters might apply e.g. we want a sample for male weight
    but only where age > 10

    Args:
        src_tbl_name: name of table containing the data
        measure_fld_name: e.g. weight
        grouping_filt: the grouping variable details
        tbl_filt_clause: clause ready to put after AND in a WHERE filter.
            E.g. WHERE ... AND age > 10
            Sometimes there is a global filter active in SOFA for a table e.g. age > 10,
            and we will need to apply that filter to ensure we are only getting the correct values
    """
    ## prepare items
    and_tbl_filt_clause = f"AND {tbl_filt_clause}" if tbl_filt_clause else ''
    if grouping_filt:
        if grouping_filt.val_is_numeric:
            grouping_filt_clause = f"{dbe_spec.entity_quoter(grouping_filt.variable_name)} = {grouping_filt.val_spec.val}"
        else:
            grouping_filt_clause = f"{dbe_spec.entity_quoter(grouping_filt.variable_name)} = '{grouping_filt.val_spec.val}'"
        and_grouping_filt_clause = f"AND {grouping_filt_clause}"
    else:
        and_grouping_filt_clause = ''
    src_tbl_name_quoted = dbe_spec.entity_quoter(src_tbl_name)
    measure_fld_name_quoted = dbe_spec.entity_quoter(measure_fld_name)
    ## assemble SQL
    sql = f"""
    SELECT {measure_fld_name_quoted}
    FROM {src_tbl_name_quoted}
    WHERE {measure_fld_name_quoted} IS NOT NULL
    {and_tbl_filt_clause}
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
        raise Exception(f"Too few {measure_fld_name} values in sample for analysis "
            f"when getting sample for {and_grouping_filt_clause}")
    lbl = grouping_filt.val_spec.lbl if grouping_filt else ''
    sample = Sample(lbl=lbl, vals=sample_vals)
    return sample
