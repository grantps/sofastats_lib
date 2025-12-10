from collections.abc import Sequence
from dataclasses import asdict, dataclass, fields
from pathlib import Path
import re
from typing import Literal

import pandas as pd

from sofastats import SQLITE_DB

pd.set_option('display.max_rows', 200)
pd.set_option('display.min_rows', 30)
pd.set_option('display.max_columns', 25)
pd.set_option('display.width', 500)

def get_pandas_friendly_name(orig_name: str, suffix: Literal['_var', '_val'] | None = None) -> str:
    """
    E.g. 'Age Group', '_val' ==> age_group_val

    Not cleaning everything but making most common cases pleasant to work with
    """
    new_name = (orig_name
        .lower()
        .replace(' ', '_')
        .replace('-', '_')
        .replace('(', '_')
        .replace(')', '_')
        .replace('/', '_')
        .replace('\\', '_')
        .replace('|', '_')
        .replace('__', '_')  ## clean up some repeat __'s
        .replace('__', '_')
        .replace('__', '_')
    )
    pandas_friendly_name = f"{new_name}{suffix}" if suffix else new_name
    return pandas_friendly_name

def pluralise_with_s(*, singular_word: str, n_items: int) -> str:
    return singular_word if n_items == 1 else f'{singular_word}s'

def todict(dc: dataclass, *, shallow=True) -> dict:
    """
    dataclasses.asdict is recursive i.e. if you have an internal sequence of dataclasses
    then they will be transformed into dicts as well.
    todict is shallow by default in which case it only turns the top level into a dict.
    This might be useful if wanting to feed the contents of the dataclass into another dataclass
    e.g. anova_results_extended = AnovaResultsExtended(**todict(anova_results), ...)
    where the goal is to make a new dataclass that has everything in the parent class
    plus new items in the child class.
    """
    if shallow:
        dict2use = dict((field.name, getattr(dc, field.name)) for field in fields(dc))
    else:
        dict2use = asdict(dc)
    return dict2use

def close_internal_db():
    """
    For tidy programmers :-)
    """
    if SQLITE_DB.get('sqlite_default_cur'):
        SQLITE_DB.get['sqlite_default_cur'].close()
        SQLITE_DB.get['sqlite_default_con'].close()

def get_safer_name(raw_name):
    return re.sub('[^A-Za-z0-9]+', '_', raw_name)

def lengthen(*, wide_csv_fpath: Path, cols2stack: Sequence[str] | None = None,
        name_for_stacked_col: str = 'Group', name_for_value_col: str = 'Value', debug=False):
    """
    If only supplied with a CSV, tries to treat the first column as the only id column
    and all the other columns as the columns to stack. Also produces a long format CSV with the following columns:
    <original_first_column_name>, Group, Value
    Can override these defaults by supplying any of the following: cols2stack, name_for_stacked_col, name_for_value_col
    Easy to add a GUI in front which explains all this to users.
    """
    df_wide = pd.read_csv(wide_csv_fpath)
    if debug: print(df_wide)
    cols = df_wide.columns
    if cols2stack is None:
        cols2stack = cols[1:]
    id_cols = list(set(cols) - set(cols2stack))
    df_long = df_wide.melt(id_vars=id_cols, value_vars=cols2stack,  ## https://pandas.pydata.org/docs/reference/api/pandas.melt.html
        var_name=name_for_stacked_col, value_name=name_for_value_col)
    if debug: print(df_long)
    long_csv_fpath = wide_csv_fpath.with_name(f"{wide_csv_fpath.stem}_IN_LONG_FORMAT.csv")
    df_long.to_csv(long_csv_fpath, index=False)
    print(f"Made {long_csv_fpath}")

if __name__ == '__main__':
    csv_fpath = Path("/home/g/projects/sofastats/store/food_data.csv")
    lengthen(wide_csv_fpath=csv_fpath, debug=True)
