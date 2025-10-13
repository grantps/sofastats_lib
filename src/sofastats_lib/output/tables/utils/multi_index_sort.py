"""
Central idea - multi-indexes need sorting. Multi-indexes are basically lists so sorting is simple at one level.
We should be able to use sorting or .sort() with a clever sort function as the key argument.
Basically we convert a row into a tuple that, when sorted upon as the key, orders the multi-index rows as configured.

E.g. imagine we start with an index like this:
[
  ['a', 'cat', 'banana', 123],
  ['b', 'dog', 'apple', 989],
]

We then apply a function to the list to create a sorting-ready tuple. E.g.:

['a', 'cat', 'banana', 123]
=>
(1, 12, 2, 5)  ## Note - not necessarily alphabetical - might be based on the values underlying the labels or something
and
['b', 'dog', 'apple', 989]
=> (0, 3, 6, 12)  ## also, just for the purposes of illustration, imagine if this were the result of the same function

Simple sorting would put (0, 3, 6, 12) before (1, 12, 2, 5) and so we would end up with the following sorted multi-index:
[
  ['b', 'dog', 'apple', 989],
  ['a', 'cat', 'banana', 123],
]

So how should sorting occur?

There are two things being sorted. Variables and values e.g. agegroup and '< 20', '20-29' etc.
Variables get their sort order from the order in which they are configured in the table design.
For example, if we have the following variable design:

      agegroup                    browser
         |                           |
         |              ----------------------------
         |              |                          |
         |          agegroup                      car

we end up with a df like:

     Age Group                                       Web Browser
Young  Middle  Old                       Firefox                                      Chrome
                           Age Group               Car                   Age Group               Car
                      Young  Middle  Old    Tesla  Mini  Porsche    Young  Middle  Old    Tesla  Mini  Porsche
Freq   Freq    Freq   Freq   Freq   Freq    Freq   Freq  Freq       Freq   Freq   Freq    Freq   Freq  Freq
--------------------------------------------------------------------------------------------------------------

and a multi-index like:
[
  ...
  ('Age Group', 'Middle', '__blank__', '__blank__', 'Freq'),
  ...
  ('Web Browser', 'Chrome', 'Age Group', 'Young', 'Freq'),
  ...
]

We need to first configure the sort order:

Remember, there are two parts - variables, and their values. The variables are simple index values based on the order
they were configured. E.g. at the top level, agegroup is 0 and browser 1.
Under browser, agegroup is 0, and car is 1.
For values, we have three sort order options:
 * by value e.g. 1 then 2 then 3 etc.
 * by label e.g. 'Apple', then 'Banana' etc.
 * or by frequency (subdivided into either increasing or decreasing).
We also have the metric where Freq then Row % then Col %.

So ... we might have:

               age   age  (no need to define sort order for metrics - standard and fixed)
               var   val
                |     |
{               v     v
    ('age', ): (0, Sort.VAL),
                               browser  browser   age   age
                                 var      val     var   val
                                  |        |       |    |
                                  v        v       v    v
    ('browser', 'age', ):        (1,    Sort.LBL,  0, Sort.VAL),

                               browser  browser   car   car
                                 var      val     var   val
                                  |        |       |    |
                                  v        v       v    v
    ('browser', 'car', ):        (1, Sort.LBL, 1, Sort.LBL),
}

Then apply the sort order knowing it is var, val, ... (skipping __blank__ - leave it as is), measure:

('Age Group', 'Middle', '__blank__', '__blank__', 'Freq'),

Note - assumed variable labels will always be different for different variables. No duplicates.
Also assumed no value labels are repeated within a variable.
Both assumptions are enforced in labels.VarLabels.
Duplicates would make it impossible to route from label to value or variable
and we need to do this to know how to sort something.

1) Convert variable labels to variables. E.g.
'Web Browser' => 'browser'
'Car' => 'car'

so

('Web Browser', 'Firefox', 'Car', 'AUDI', Metric.FREQ)
=>
('browser', 'Firefox', 'car', 'AUDI', Metric.FREQ)

2) Get from the index row tuple to the branch of variable keys e.g.
('browser', 'Firefox', 'car', 'AUDI', Metric.FREQ)
=>
('browser', 'car', )

3) Find the matching sort order for that branch of variables key
(in this case, a branch from browser to car).

4) Apply that sort order to the original index row.
"""
from functools import partial
from itertools import count

import pandas as pd

from sofastats_lib.conf.main import SortOrder
from sofastats_lib.conf.var_labels import VarLabels
from sofastats_lib.output.tables.interfaces import BLANK, TOTAL, Metric

pd.set_option('display.max_rows', 200)
pd.set_option('display.min_rows', 30)
pd.set_option('display.max_columns', 50)
pd.set_option('display.width', 750)

def index_row2branch_of_vars_key(orig_tuple: tuple, *, debug=False) -> tuple:
    """
    We need this so we can look up the sorting required for this variable sequence.

             |                    |
             v                    v
    e.g. ('browser', 'Firefox', 'car', 'AUDI', Metric.FREQ)
    =>
    ('browser', 'car', )

      |
      v
    ('age', '20-29', BLANK, BLANK, Metric.FREQ)
    =>
    ('age', )
    """
    items = []
    for idx in count(0, 2):
        try:
            item = orig_tuple[idx]
        except IndexError:
            break
        if item in Metric or item == BLANK:
            break
        items.append(item)
        if debug:
            print(f"{idx=}")
        if idx > 1_000:
            raise Exception(
                "Seriously?! Over 1,000 items in multi-index tuple?! Something has gone badly wrong! Abort!!")
    items = tuple(items)
    if debug:
        print(f"{orig_tuple} => {items}")
    return tuple(items)

def get_metric2order(metric: Metric) -> int:
    return {Metric.FREQ: 1, Metric.ROW_PCT: 2, Metric.COL_PCT: 3}[metric]

def by_freq(variable: str, lbl: str, df: pd.DataFrame, filts: tuple[tuple[str, str]] | None = None, *,
        increasing=True) -> tuple[int, float]:
    """
    Args:
        filts: [('browser', 'Firefox'), ...] or [('agegroup', '< 20'), ...]
    """
    if lbl == TOTAL:
        sort_val = (1, 'anything ;-)')
    else:
        df_filt = df.copy().loc[df[variable] == lbl]
        for filt_variable, filt_val_lbl in filts:
            df_filt = df_filt.loc[df_filt[filt_variable] == filt_val_lbl]
        freq = len(df_filt)
        if increasing:
            sort_val = freq
        else:
            try:
                sort_val = 1 / freq
            except ZeroDivisionError as e:
                sort_val = 1.1  ## so always at end after lbls with freq of at least one (given we are decreasing)
        sort_val = (0, sort_val)
    return sort_val

def get_branch_of_variables_key(index_with_lbls: tuple, var_lbl2var: dict[str, int | str], *, debug=False) -> tuple:
    """
    How should we sort the multi-index? The details are configured against variable branch trees. E.g.
    {
        ('age', ): (0, Sort.VAL),
        ('browser', 'age', ): (1, Sort.LBL, 0, Sort.VAL),
        ('browser', 'car', ): (1, Sort.LBL, 1, Sort.LBL),
    }
    So we need to extract the key (in the form of a branch of variables) from the multi-index
    so we can read the sort configuration for it. E.g.
    ('browser', 'Firefox', 'car', 'AUDI', Metric.FREQ)
    =>
    ('browser', 'car', )
    """
    index_with_vars = []
    for i, item in enumerate(index_with_lbls):
        vars_finished = ((item == BLANK) or i == len(index_with_lbls) - 1)
        if vars_finished:
            index_with_vars.append(item)
            continue
        is_a_variable = (i % 2 == 0)
        if is_a_variable:
            var = var_lbl2var.get(item, item)  ## assumed that if not in dict, we just used the variable (but if the label is '1' was the original var 1 or '1'? TODO: resolve)
            index_with_vars.append(var)
        else:
            index_with_vars.append(item)
    branch_of_variables_key = index_row2branch_of_vars_key(tuple(index_with_vars), debug=debug)
    return branch_of_variables_key

def get_tuple_for_sorting(orig_index_tuple: tuple, *, order_rules_for_multi_index_branches: dict,
        var_labels: VarLabels, raw_df: pd.DataFrame, has_metrics: bool, debug=False) -> tuple:
    """
    Use this method for the key arg for sorting
    such as sorting(unsorted_multi_index_list, key=SortUtils.get_tuple_for_sorting)

    E.g.
    ('Age Group', '<20', '__blank__', '__blank__', 'Freq')
    => (we get key to branch of variables key ('age, ) and then lookup sorting e.g. (0, Sort.VAL))
    (0, 1, 0, 0, 1) given 1 is the val for '< 20' and 0 is our index for Freq (cf Row % and Col %)

    ('Age Group', '65+', '__blank__', '__blank__', 'Row %')
    =>
    (0, 5, 0, 0, 1) given 5 is the val for '65+' and 1 is our index for Row %

    Params:
        multi_index_tuple: needed so we can create the sorting tuple from the actual content of the multi-index row
        multi_index_tuple_with_vars_not_lbls: needed only so we can get to sort config (which is by variables not labels)
    """
    max_idx = len(orig_index_tuple) - 1
    metric_idx = max_idx if has_metrics else None
    branch_of_variables_key = get_branch_of_variables_key(
        index_with_lbls=orig_index_tuple, var_lbl2var=var_labels.var_lbl2var)
    order_rule = order_rules_for_multi_index_branches[branch_of_variables_key]  ## e.g. (1, Sort.LBL, 0, Sort.INCREASING)
    list_for_sorting = []
    variable_value_lbl_pairs = []  ## so we know what filters apply depending on how far across the index we have come e.g. if we have passed Gender Female then we need to filter to that
    if debug:
        print(f"{orig_index_tuple=}; {max_idx=}; {order_rule=}")
    for idx in count():
        if idx > max_idx:
            break
        ## get order for sorting
        is_metric_idx = (idx == metric_idx) if has_metrics else False
        is_var_idx = (idx % 2 == 0 and not is_metric_idx)
        is_val_idx = not (is_var_idx or is_metric_idx)
        if is_var_idx:
            variable_lbl = orig_index_tuple[idx]
            if variable_lbl == BLANK:
                variable_order = 0  ## never more than one BLANK below a parent so no sorting occurs - so 0 as good as anything else
            else:
                variable_order = order_rule[idx]
            if debug:
                print(f"{variable_lbl=}; {variable_order=}")
            list_for_sorting.append(variable_order)
        elif is_val_idx:
            """
            Because we want TOTAL to come last we namespace everything else with 0, and TOTAL with 1. Elegant 😙🤌 
            """
            val_lbl = orig_index_tuple[idx]
            if val_lbl == BLANK:
                value_order = (0, "doesn't matter - doesn't splay below this so nothing to sort beyond the order already set so far in the ordering tuple")  ## never more than one BLANK in vals (because all the rest to the right will also be BLANKs and there will be nothing to sort within the parent branch this BLANK was under) so not more than one to sort so sort order doesn't matter
            else:
                variable_lbl = orig_index_tuple[idx - 1]
                variable = var_labels.var_lbl2var.get(variable_lbl, variable_lbl)  ## if unconfigured, left alone - not title-cased or anything
                value_order_rule = order_rule[idx]
                if value_order_rule == SortOrder.LABEL:
                    value_order = (1, val_lbl) if val_lbl == TOTAL else (0, val_lbl)  ## want TOTAL last
                elif value_order_rule == SortOrder.VALUE:
                    if val_lbl != TOTAL:
                        val2lbl = var_labels.var2val2lbl.get(variable)
                        if val2lbl:
                            lbl2val = {v: k for k, v in val2lbl.items()}
                            val = lbl2val.get(val_lbl, val_lbl)  ## on assumption (validated) that a val lbl cannot apply to more than one val for any given variable
                        else:
                            val = val_lbl  ## If unconfigured, left alone. Note - if val was an integer it is on the user to define a val lbl explicitly in the YAML or accept potential sort issues e.g. 1, 11, 12, 2, 3 etc
                        value_order = (0, val)
                    else:  ## want TOTAL last
                        value_order = (1, 'anything - the 1 is enough to ensure sort order')
                elif value_order_rule in (SortOrder.INCREASING, SortOrder.DECREASING):
                    increasing = (value_order_rule == SortOrder.INCREASING)
                    filts = tuple(variable_value_lbl_pairs)
                    value_order = by_freq(variable, val_lbl, df=raw_df, filts=filts, increasing=increasing)  ## can't use df as arg for cached function  ## want TOTAL last
                else:
                    raise ValueError(f"Unexpected value order spec ({value_order_rule})")
                variable_value_lbl_pairs.append((variable, val_lbl))
            list_for_sorting.append(value_order)
        elif has_metrics and is_metric_idx:
            metric = orig_index_tuple[idx]
            metric_order = get_metric2order(metric)
            list_for_sorting.append(metric_order)
        else:
            raise ValueError(f"Unexpected item index ({idx=}) when getting tuple for sorting")
    tuple_for_sorting = tuple(list_for_sorting)
    return tuple_for_sorting

def get_sorted_multi_index_list(unsorted_multi_index_list: list[tuple], *, order_rules_for_multi_index_branches: dict,
        var_labels: VarLabels, raw_df: pd.DataFrame, has_metrics: bool, debug=False) -> list[tuple]:
    """
    1) Convert variable labels to variables. E.g.
    'Web Browser' => 'browser'
    'Car' => 'car'

    so

    ('Web Browser', 'Firefox', 'Car', 'AUDI', Metric.FREQ)
    =>
    ('browser', 'Firefox', 'car', 'AUDI', Metric.FREQ)

    2) Get from the index row tuple to the branch of variable keys e.g.
    ('browser', 'Firefox', 'car', 'AUDI', Metric.FREQ)
    =>
    ('browser', 'car', )

    3) Find the matching sort order rule for that branch of variables key
    (in this case, a branch from browser to car).

    4) Derive a sortable tuple from that original index row according to the sort order rule (see get_tuple_for_sorting)

    5) Sort by the sortable tuple

    :param order_rules_for_multi_index_branches: e.g.
        {
            ('age', ): (0, Sort.VAL),
            ('browser', 'age', ): (1, Sort.LBL, 0, Sort.VAL),
            ('browser', 'car', ): (1, Sort.LBL, 1, Sort.LBL),
        }
    :param raw_df: e.g.
                id  age            browser  car
        0        1    5            Firefox    7
        ...    ...  ...                ...  ...
        1499  1500    4  Internet Explorer    8
    """
    multi_index_sort_fn = partial(get_tuple_for_sorting,
        order_rules_for_multi_index_branches=order_rules_for_multi_index_branches,
        var_labels=var_labels, raw_df=raw_df, has_metrics=has_metrics, debug=debug)
    sorted_multi_index_list = sorted(unsorted_multi_index_list, key=multi_index_sort_fn)
    if debug:
        for row in sorted_multi_index_list:
            print(row)
    return sorted_multi_index_list
