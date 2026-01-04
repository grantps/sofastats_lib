from collections.abc import Sequence
from typing import Any

from sofastats import logger
from sofastats.conf.main import (AVG_CHAR_WIDTH_PIXELS, AVG_LINE_HEIGHT_PIXELS, DOJO_Y_AXIS_TITLE_OFFSET_PIXELS,
    GAP_BEFORE_FIRST_X_LABEL_TICK_PIXELS, PADDING_TO_RIGHT_OF_Y_AXIS_VALUES_PIXELS)
from sofastats.output.charts.interfaces import LeftMarginOffsetSpec

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
    if show_major_ticks_only:
        widest_x_label_width = 0.6 * widest_x_label_width  ## wide labels still won't bang into each other because they are separated by unlabelled minor ticks
    if is_time_series:
        item_min_width = max(5, widest_x_label_width)
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
        min_chart_width = 1.5 * min_chart_width
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

def get_y_axis_title_offset(*, widest_y_axis_label_n_characters: int, widest_x_axis_label_n_characters: int,
        avg_pixels_per_character: float) -> int:
    """
    Need to shift y-axis title left by y_axis_title_offset
    if first x-axis label is wide or the highest y-axis label is wide.
    Note - must convert characters to pixels as all offsets and other chart dimensions are in pixels.

       |   |<------------- offset required for widest y-axis label (width = 1000 and another 20 pixels for the padding)

            ^
       1000 |
    F       |
    r       |
    e   500 |
    q       |
            |
          0 |
            ------------------------------------------------->
               `          '         '      ...
          New Zealand   Canada  Colombia
          |    |<------ half of width of first x-label           This
            |  |<---- GAP_BEFORE_FIRST_X_LABEL_TICK_PIXELS       minus
         |  |<----- offset required for first x-axis label       this
                                                                 is the offset required for the first x-axis label
    """
    offset_required_for_widest_y_axis_label = (
            (widest_y_axis_label_n_characters * avg_pixels_per_character) + PADDING_TO_RIGHT_OF_Y_AXIS_VALUES_PIXELS)
    half_of_width_of_first_x_label = (widest_x_axis_label_n_characters / 2) * avg_pixels_per_character
    offset_required_for_first_x_axis_label = half_of_width_of_first_x_label - GAP_BEFORE_FIRST_X_LABEL_TICK_PIXELS  ## half of label goes to the right
    y_axis_title_offset_required = max(offset_required_for_widest_y_axis_label, offset_required_for_first_x_axis_label)
    return y_axis_title_offset_required

def get_left_margin_offset(*, width_after_left_margin: float, offsets: LeftMarginOffsetSpec,
        is_multi_chart: bool, y_axis_title_offset: float, rotated_x_labels: bool) -> float:
    wide = width_after_left_margin > 1_200
    initial_offset = offsets.wide_offset if wide else offsets.initial_offset  ## otherwise gets squeezed out e.g. in pct
    offset = initial_offset + y_axis_title_offset - DOJO_Y_AXIS_TITLE_OFFSET_PIXELS
    offset = offset + offsets.rotate_offset if rotated_x_labels else offset
    offset = offset + offsets.multi_chart_offset if is_multi_chart else offset
    return offset

def get_x_axis_font_size(*, n_x_items: int, is_multi_chart: bool) -> float:
    if n_x_items <= 5:
        x_axis_font_size = 10
    elif n_x_items > 10:
        x_axis_font_size = 8
    else:
        x_axis_font_size = 9
    x_axis_font_size = x_axis_font_size * 0.75 if is_multi_chart else x_axis_font_size
    return x_axis_font_size

def get_height(*, axis_label_drop: float, rotated_x_labels=False, max_x_axis_label_len: float) -> float:
    height = 310
    if rotated_x_labels:
        height += AVG_CHAR_WIDTH_PIXELS * max_x_axis_label_len
    height += axis_label_drop  ## compensate for loss of bar display height
    return height

def get_axis_label_drop(*, is_multi_chart: bool, rotated_x_labels: bool, max_x_axis_label_lines: int) -> int:
    axis_label_drop = 10 if is_multi_chart else 15
    if not rotated_x_labels:
        extra_lines = max_x_axis_label_lines - 1
        axis_label_drop += AVG_LINE_HEIGHT_PIXELS * extra_lines
    logger.debug(axis_label_drop)
    return axis_label_drop

def get_dojo_format_x_axis_numbers_and_labels(x_axis_categories: Sequence[Any]) -> str:
    """
    Dojo charts need string [{value: 1, text: "NZ"}, ...] as input to addAxis

    Args:
        x_axis_categories: e.g. ['NZ', 'Denmark', ...]
    """
    number_and_labels = []
    for n, category in enumerate(x_axis_categories, 1):
        number_and_labels.append(f'{{value: {n}, text: "{category}"}}')
    dojo_format_x_axis_numbers_and_labels = '[' + ',\n            '.join(number_and_labels) + ']'
    return dojo_format_x_axis_numbers_and_labels
