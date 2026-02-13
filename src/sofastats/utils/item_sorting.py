"""
Chart output by Charts and by Series should only be sorted by the value label itself (e.g. '<20' is before '20 to <30'),
not by data associated with the label such as chart n_records.
So only by SortOrder's: VALUE, CUSTOM but not INCREASING, or DECREASING.

sort_orders: SortOrderSpecs = a dict for each variable with values in expected order
sort_order: SortOrder = how an individual variable is to be sorted e.g. CUSTOM
"""
from typing import Any

from sofastats.conf.main import SortOrderSpecs, SortOrder

def sort_by_text(*, variable_name: str, values: list[Any],
        sort_orders: SortOrderSpecs, sort_order: SortOrder) -> list[Any]:
    """
    Sort values by the content of the values themselves (if possible)
    i.e. not with reference to frequencies associated with those values.

    Not always possible because the setting might be CUSTOM yet no custom sort order supplied
    (in which case no change is made to the order)

    Charting with categories which display amounts are sorted by to_sorted_category_amount_specs()
    in data_extraction.charts.amounts

    Table variable values are sorted by get_sorted_multi_index_list() in output.tables.utils.multi_index_sort
    """
    if sort_order == SortOrder.VALUE:
        sorted_values = sorted(values)
    elif sort_order == SortOrder.CUSTOM:
        orig_values = values.copy()
        try:
            specified_custom_values_in_order = sort_orders[variable_name]
        except KeyError:
            sorted_values = orig_values  ## leave as the order they were supplied - don't sort
        else:
            value2order = {val: order for order, val in enumerate(specified_custom_values_in_order)}
            try:
                sorted_values = sorted(orig_values, key=lambda val: value2order[val])
            except KeyError:
                raise Exception(f"The custom sort order you supplied for values in variable '{variable_name}' "
                    "didn't include all the values in your analysis so please fix that and try again.")
    else:
        raise Exception(f"Unexpected sort_order ({sort_order})"
            "\nINCREASING and DECREASING not allowed using sort_values_by_value_or_custom_if_possible().")
    return sorted_values
