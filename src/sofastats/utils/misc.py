from collections.abc import Sequence
from dataclasses import asdict, dataclass, fields
from pathlib import Path
import re
from typing import Any, Literal

import pandas as pd

from sofastats import SQLITE_DB
from sofastats.conf.main import SortOrderSpecs

pd.set_option('display.max_rows', 200)
pd.set_option('display.min_rows', 30)
pd.set_option('display.max_columns', 25)
pd.set_option('display.width', 500)

def get_width_after_left_margin(*,
        n_x_items: int, n_items_horizontally_per_x_item: int, min_pixels_per_sub_item: int,
        x_item_padding_pixels: int, sub_item_padding_pixels: int,
        x_axis_title: str, widest_x_label_n_characters: int, avg_pixels_per_character: float,
        min_chart_width_one_item: int, min_chart_width_multi_item: int,
        is_multi_chart: bool, multi_chart_size_scalar: float = 0.9,
        is_time_series=False, show_major_ticks_only=False) -> float:
    """
    Usually only need to be wide enough to contain chart content.
    If the x-axis title is wider than that we need to increase the overall width to be wide enough for the title.
    If the minimum chart width is bigger, then we set the width to that.

    So how do we set the minimum chart content width?
    We set enough space for each x-item (one per label on the x-axis) including some padding between them.

    So how do we set the x-item width?
    In general, we set enough space for each sub-item, if there are any
    (e.g. each bar in a cluster, or each box in a cluster) including some padding between them.
    If the widest x-axis label is wider than that we must increase the x-item width
    so it is wide enough for even the widest label.
    If the more specific case of dealing with a time series line or area chart,
    we simply set the width per item quite narrow.

    We have to work outwards from the smallest parts e.g. from sub-items to items.

    Args:
        n_x_items: how many labelled items on the x-axis e.g. categories
        n_items_horizontally_per_x_item: one for line and area charts,
          the number of series in the case of bar charts and box plots
        min_pixels_per_sub_item: for bar charts, the minimum sane bar width; for box plots;
          the minimum sane box width; for line and area enough width to include the marker
        x_item_padding_pixels: space between each x-item. For a simple bar chart, the space between bars;
          for a clustered bar chart, the space between clusters; for a simple box plot, the space between boxes;
          for a clustered box plot, the space between series of boxes;
          for line and area charts, some extra horizontal space between markers
        sub_item_padding_pixels: only applies when there are multiple sub-items.
          Extra horizontal spacing between bars within a cluster for clustered bar charts;
          and between boxes within a box cluster defined by series
        x_axis_title: obviously can't be narrower than this
          (usually not a factor because much narrower than what is needed by the chart content)
        widest_x_label_n_characters: this sets the minimum for labels generally.
          Note - not just the number of characters - there are line breaks so we only care about the widest part.
          E.g. label for x-axis is "This is a really long label, and we need a wide enough chart"
        avg_pixels_per_character: we use this to work out how many pixels titles and labels require
        min_chart_width_one_item: Feels OK to shrink a bit when just one item
        min_chart_width_multi_item: Feels necessary to be a little wider
        is_multi_chart: one chart or many - shrink charts slightly when multi-chart
        multi_chart_size_scalar: e.g. 0.5 halves width, 2.0 doubles it
        is_time_series: can narrow a lot because standard-sized labels and usually not many.
        show_major_ticks_only: we want to only see the main labels and won't need it to be so wide
          (only applicable to line and area charts)
    """
    debug = False
    item_min_width_from_sub_item_contents = (
        (min_pixels_per_sub_item * n_items_horizontally_per_x_item)  ## sub-items
        + ((n_items_horizontally_per_x_item- 1) * sub_item_padding_pixels)  ## in-between padding
    )
    widest_x_label_width = (widest_x_label_n_characters * avg_pixels_per_character)
    if is_time_series:
        item_min_width = max(10, widest_x_label_width)
    else:
        item_min_width = max(item_min_width_from_sub_item_contents, widest_x_label_width)
    min_width_from_item_content = (
        (n_x_items * item_min_width)  ## items
        + ((n_x_items - 1) * x_item_padding_pixels)  ## padding
    )
    x_axis_title_width = len(x_axis_title) * avg_pixels_per_character
    raw_width_from_content = max(min_width_from_item_content, x_axis_title_width)
    if is_multi_chart:
        width_from_content = raw_width_from_content * multi_chart_size_scalar
    else:
        width_from_content = raw_width_from_content
    min_chart_width = min_chart_width_one_item if n_x_items == 1 else min_chart_width_multi_item
    if show_major_ticks_only:
        min_chart_width = 0.4 * min_chart_width
    width = max(width_from_content, min_chart_width)
    if debug:
        print(f"""
        ********************************************************************************************************
        width: {width}
        min_chart_width: {min_chart_width}
        width_from_content: {width_from_content}
        raw_width_from_content: {raw_width_from_content}
        x_axis_title_width: {x_axis_title_width} (x_axis_title = "{x_axis_title}")
        min_width_from_item_content: {min_width_from_item_content}
        (
            ({n_x_items=} * {item_min_width=})  ## items
            + (({n_x_items=} - 1) * {x_item_padding_pixels=})  ## padding
        )
        item_min_width: {item_min_width}
        widest_x_label_width: {widest_x_label_width}
        ({widest_x_label_n_characters=} * {avg_pixels_per_character=})
        item_min_width_from_sub_item_contents: {item_min_width_from_sub_item_contents}
        (
            ({min_pixels_per_sub_item=} * {n_items_horizontally_per_x_item=})  ## sub-items
            + (({n_items_horizontally_per_x_item=}- 1) * {sub_item_padding_pixels=})  ## in-between padding
        )
        ********************************************************************************************************""")
    return width

def apply_custom_sorting_to_values(*, variable_name: str, values: list[Any], sort_orders: SortOrderSpecs) -> list[Any]:
    orig_values = values.copy()
    try:
        specified_custom_values_in_order = sort_orders[variable_name]
    except KeyError:
        sorted_values = sorted(orig_values)
    else:
        value2order = {val: order for order, val in enumerate(specified_custom_values_in_order)}
        try:
            sorted_values = sorted(orig_values, key=lambda val: value2order[val])
        except KeyError:
            raise Exception(f"The custom sort order you supplied for values in variable '{variable_name}' "
                "didn't include all the values in your analysis so please fix that and try again.")
    return sorted_values

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
