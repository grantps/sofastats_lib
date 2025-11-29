from dataclasses import dataclass
from functools import partial

import pandas as pd

from sofastats.conf.var_labels import VarLabels
from sofastats.output.interfaces import (
    DEFAULT_SUPPLIED_BUT_MANDATORY_ANYWAY, HTMLItemSpec, OutputItemType, CommonDesign, add_from_parent)
from sofastats.output.tables.interfaces import BLANK, PctType, Row
from sofastats.output.styles.utils import get_style_spec
from sofastats.output.tables.utils.html_fixes import fix_top_left_box, merge_cols_of_blanks
from sofastats.output.tables.utils.misc import (apply_index_styles, correct_str_dps, get_data_from_spec,
                                                get_df_pre_pivot_with_pcts, get_order_rules_for_multi_index_branches, get_raw_df, set_table_styles)
from sofastats.output.tables.utils.multi_index_sort import get_metric2order, get_sorted_multi_index_list

def get_all_metrics_df_from_vars(data, var_labels: VarLabels, *, row_vars: list[str],
        n_row_fillers: int = 0, inc_col_pct=False, dp: int = 2, debug=False) -> pd.DataFrame:
    """
    Includes at least the Freq metric but potentially the percentage ones as well.

    Start with a column for each row var, then one for each col var, then freq. All in a fixed order we can rely on.
    Which is why we can build the columns from the input variable names, with _val suffix, in order.
    We know the last column is the count so we add 'n' as the final column.
    E.g. country_val, gender_val, n.

       country_val gender_val    n
    0            1          1   43
    1            1          2   34
    2            2          1   25
    3            2          2   21
    4            3          1   37
    5            3          2   44
    6        TOTAL          1  105
    7        TOTAL          2   99
    8            1      TOTAL   77
    9            2      TOTAL   46
    10           3      TOTAL   81
    11       TOTAL      TOTAL  204
    ...

    Note - the source, un-pivoted df has all TOTAL values calculated and identified in the val columns already.

    OK, so now we have a proper df. Time to add extra columns e.g. alongside country_val's 1s, 2s, etc.
    we add country_var with all values set to 'Country', and country as 'USA', 'South Korea', etc

       country_val gender_val    n country_var      country gender_var  gender metric
    0            1          1   43     Country          USA     Gender    Male   Freq
    1            1          2   34     Country          USA     Gender  Female   Freq
    2            2          1   25     Country  South Korea     Gender    Male   Freq
    3            2          2   21     Country  South Korea     Gender  Female   Freq
    4            3          1   37     Country           NZ     Gender    Male   Freq
    5            3          2   44     Country           NZ     Gender  Female   Freq
    6        TOTAL          1  105     Country        TOTAL     Gender    Male   Freq
    7        TOTAL          2   99     Country        TOTAL     Gender  Female   Freq
    8            1      TOTAL   77     Country          USA     Gender   TOTAL   Freq
    9            2      TOTAL   46     Country  South Korea     Gender   TOTAL   Freq
    10           3      TOTAL   81     Country           NZ     Gender   TOTAL   Freq
    11       TOTAL      TOTAL  204     Country        TOTAL     Gender   TOTAL   Freq

    Then add in any row or column filler columns (some will pivot to rows and others to columns in the final df)
    with __BLANK__ e.g. (if another config from that followed through in this example):

       country_val gender_val agegroup_val    n country_var      country gender_var  gender agegroup_var agegroup col_filler_var_0 col_filler_0 metric
    0            1          1            1    3     Country          USA     Gender    Male    Age Group     < 20        __blank__    __blank__   Freq
    ...

    Finally, round numbers
    """
    all_variables = row_vars
    columns = []
    for var in all_variables:
        columns.append(var_labels.var2var_label_spec[var].pandas_val)  ## e.g. agegroup_val
    columns.append('n')
    df_pre_pivot = pd.DataFrame(data, columns=columns)
    index_cols = []
    column_cols = []
    for var in all_variables:
        var2var_label_spec = var_labels.var2var_label_spec[var]
        ## var set to lbl e.g. "Age Group" goes into cells
        df_pre_pivot[var2var_label_spec.pandas_var] = var2var_label_spec.lbl
        ## val set to val lbl e.g. 1 => '< 20'
        df_pre_pivot[var2var_label_spec.name] = df_pre_pivot[var2var_label_spec.pandas_val].apply(
            lambda x: var2var_label_spec.val2lbl.get(x, str(x)))
        cols2add = [var2var_label_spec.pandas_var, var2var_label_spec.name]
        if var in row_vars:
            index_cols.extend(cols2add)
        else:
            raise Exception(f"{var=} not found in either {row_vars=}")
    ## only add what is needed to fill gaps
    for i in range(n_row_fillers):
        df_pre_pivot[f'row_filler_var_{i}'] = BLANK
        df_pre_pivot[f'row_filler_{i}'] = BLANK
        index_cols.extend([f'row_filler_var_{i}', f'row_filler_{i}'])
    column_cols.append('metric')
    df_pre_pivot['metric'] = 'Freq'
    df_pre_pivot['n'] = df_pre_pivot['n'].astype(pd.Int64Dtype())
    if debug: print(df_pre_pivot)
    df_pre_pivots = [df_pre_pivot, ]
    column_cols = ['metric', ]  ## simple cf a cross_tab
    df = df_pre_pivot.pivot(index=index_cols, columns=column_cols, values='n')  ## missing rows e.g. if we have no rows for females < 20 in the USA, now appear as NAs so we need to fill them in df
    ## https://stackoverflow.com/questions/77900971/pandas-futurewarning-downcasting-object-dtype-arrays-on-fillna-ffill-bfill
    ## https://medium.com/@felipecaballero/deciphering-the-cryptic-futurewarning-for-fillna-in-pandas-2-01deb4e411a1
    with pd.option_context('future.no_silent_downcasting', True):
        df = df.fillna(0).infer_objects(copy=False)  ## needed so we can round values (can't round a NA). Also need to do later because of gaps appearing when pivoted then too
    if inc_col_pct:
        df_pre_pivot_inc_row_pct = get_df_pre_pivot_with_pcts(
            df, is_cross_tab=False, pct_type=PctType.COL_PCT, dp=dp, debug=debug)
        df_pre_pivots.append(df_pre_pivot_inc_row_pct)
    df_pre_pivot = pd.concat(df_pre_pivots)
    df_pre_pivot['__throwaway__'] = 'Metric'
    df = df_pre_pivot.pivot(index=index_cols, columns=['__throwaway__', ] + column_cols, values='n')
    with pd.option_context('future.no_silent_downcasting', True):
        df = df.fillna(0).infer_objects(copy=False)
    df = df.astype(str)
    ## have to ensure all significant digits are showing e.g. 3.33 and 1.0 or 0.0 won't align nicely
    correct_string_dps = partial(correct_str_dps, dp=dp)
    df = df.map(correct_string_dps)
    return df


@add_from_parent
@dataclass(frozen=False, kw_only=True)
class FrequencyTableDesign(CommonDesign):
    rows: list[Row] = DEFAULT_SUPPLIED_BUT_MANDATORY_ANYWAY

    style_name: str = 'default'

    include_column_percent: bool = False
    decimal_points: int = 3
    debug: bool = False
    verbose: bool = False

    @property
    def totalled_vars(self) -> list[str]:
        tot_vars = []
        for row_spec in self.rows:
            tot_vars.extend(row_spec.self_and_descendant_totalled_vars)
        return tot_vars

    @property
    def max_row_depth(self) -> int:
        max_depth = 0
        for row_spec in self.rows:
            row_depth = len(row_spec.self_and_descendant_vars)
            if row_depth > max_depth:
                max_depth = row_depth
        return max_depth

    def __post_init__(self):
        CommonDesign.__post_init__(self)
        row_vars = [spec.variable for spec in self.rows]
        row_dupes = set()
        seen = set()
        for row_var in row_vars:
            if row_var in seen:
                row_dupes.add(row_var)
            else:
                seen.add(row_var)
        if row_dupes:
            raise ValueError(f"Duplicate top-level variable(s) detected in row dimension - {sorted(row_dupes)}")

    def get_row_df(self, cur, *, row_idx: int, dp: int = 2) -> pd.DataFrame:
        """
        See cross_tab docs
        """
        row_spec = self.rows[row_idx]
        totalled_variables = row_spec.self_and_descendant_totalled_vars
        row_vars = row_spec.self_and_descendant_vars
        data = get_data_from_spec(cur, src_tbl_name=self.source_table_name, tbl_filt_clause=self.table_filter,
            all_variables=row_vars, totalled_variables=totalled_variables, debug=self.debug)
        n_row_fillers = self.max_row_depth - len(row_vars)
        df = get_all_metrics_df_from_vars(
            data, self.data_labels, row_vars=row_vars, n_row_fillers=n_row_fillers,
            inc_col_pct=self.include_column_percent,
            dp=dp, debug=self.debug)
        return df

    def get_tbl_df(self, cur) -> pd.DataFrame:
        """
        See cross_tab docs
        """
        dfs = [self.get_row_df(cur, row_idx=row_idx, dp=self.decimal_points) for row_idx in range(len(self.rows))]
        df_t = dfs[0].T
        dfs_remaining = dfs[1:]
        for df_next in dfs_remaining:
            df_t = df_t.join(df_next.T, how='outer')
        df = df_t.T  ## re-transpose back so cols are cols and rows are rows again
        if self.debug: print(f"\nCOMBINED:\n{df}")
        ## Sorting indexes
        raw_df = get_raw_df(cur, src_tbl_name=self.source_table_name)
        order_rules_for_multi_index_branches = get_order_rules_for_multi_index_branches(self.rows)
        ## ROWS
        unsorted_row_multi_index_list = list(df.index)
        sorted_row_multi_index_list = get_sorted_multi_index_list(
            unsorted_row_multi_index_list, order_rules_for_multi_index_branches=order_rules_for_multi_index_branches,
            var_labels=self.data_labels, raw_df=raw_df, has_metrics=False, debug=self.debug)
        sorted_row_multi_index = pd.MultiIndex.from_tuples(
            sorted_row_multi_index_list)  ## https://pandas.pydata.org/docs/user_guide/advanced.html
        sorted_col_multi_index_list = sorted(
            df.columns, key=lambda metric_lbl_and_metric: get_metric2order(metric_lbl_and_metric[1]))
        sorted_col_multi_index = pd.MultiIndex.from_tuples(sorted_col_multi_index_list)
        df = df.reindex(index=sorted_row_multi_index, columns=sorted_col_multi_index)
        if self.debug: print(f"\nORDERED:\n{df}")
        return df

    def to_html_design(self) -> HTMLItemSpec:
        get_tbl_df_for_cur = partial(self.get_tbl_df)
        df = get_tbl_df_for_cur(self.cur)
        pd_styler = set_table_styles(df.style)
        style_spec = get_style_spec(style_name=self.style_name)
        pd_styler = apply_index_styles(df, style_spec, pd_styler, axis='rows')
        pd_styler = apply_index_styles(df, style_spec, pd_styler, axis='columns')
        raw_tbl_html = pd_styler.to_html()
        if self.debug:
            print(raw_tbl_html)
        ## Fix
        html = raw_tbl_html
        html = fix_top_left_box(html, style_spec, debug=self.debug, verbose=self.verbose)
        html = merge_cols_of_blanks(html, debug=self.debug)
        if self.debug:
            print(pd_styler.uuid)  ## A unique identifier to avoid CSS collisions; generated automatically.
            print(html)
        return HTMLItemSpec(
            html_item_str=html,
            style_name=self.style_name,
            output_item_type=OutputItemType.MAIN_TABLE,
        )
