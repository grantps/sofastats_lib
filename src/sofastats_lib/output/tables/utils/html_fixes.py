from itertools import count

from bs4 import BeautifulSoup
import pandas as pd

from sofastats_lib.output.styles.interfaces import StyleSpec
from sofastats_lib.output.tables.interfaces import BLANK

def is_empty_th(th) -> bool:
    return th.string in (None, ' ', '\xa0')

def fix_top_left_box(raw_tbl_html: str, style_spec: StyleSpec, *, debug=False, verbose=False) -> str:
    """
    Merge top-left cells.

    We start with a grid in the top-left corner - it has some labels we don't need and even an extra row
    depending on how pandas chooses, to display itself, possibly in a quirky way.

                              measure    Freq ...
    country_var    country     <====== pandas creates an extra row, including col labels, if, and only if, the entire column is the same

    To merge the top-left corner we need several things:
    1) the two numbers for n_rows and n_cols to span
    2) how to identify the ths to delete
    3) whether there is a row to delete (remove this first before working out total rows to span, or deleting ths)

    https://www.crummy.com/software/BeautifulSoup/bs4/doc/

    https://www.crummy.com/software/BeautifulSoup/bs4/doc/#changing-tag-names-and-attributes

    Step 1 - look at the final tr and see if the last th is empty. If so, remove that tr.
    Step 2 - use n_header_rows and n_header_cols to do spanning
    Step 3 - remove all other ths in top-left corner (not all of which are empty)
    """
    soup = BeautifulSoup(raw_tbl_html, 'html.parser')
    trs = soup.table.thead.find_all('tr')
    n_header_rows = len(trs)
    ## Step 1 Remove extraneous row (if present)
    last_tr = trs[-1]
    last_tr_ths = last_tr.find_all('th')
    last_th_in_last_tr = last_tr_ths[-1]
    last_th_in_last_tr_is_empty = is_empty_th(last_th_in_last_tr)
    if last_th_in_last_tr_is_empty:
        last_tr.decompose()  ## bye bye! Step 1 happens
        n_header_rows -= 1
        trs = soup.table.thead.find_all('tr')
    ## Step 2 Make spanned / merged cell
    first_tr = trs[0]
    first_tr_ths = first_tr.find_all('th')
    n_header_cols = 0
    for first_tr_th in first_tr_ths:
        if is_empty_th(first_tr_th):
            n_header_cols += 1
        else:
            break
    if debug:
        print(f"{n_header_rows=}; {n_header_cols=}")
    tl_box_th = soup.new_tag('th')
    tl_box_th['rowspan'] = str(n_header_rows)
    tl_box_th['colspan'] = str(n_header_cols)
    tl_box_th['class'] = f"spaceholder-{style_spec.name.replace('_', '-')}"
    first_tr_first_th = first_tr_ths[0]
    first_tr_first_th.replace_with(tl_box_th)  ## Step 2 happens
    ## Step 3 Remove redundant ths
    ## for each header row, remove the first n_header_cols ths (except for first one in which case keep the first - the new spanned / merged th)
    for i, tr in enumerate(trs):
        first_header_row = (i == 0)
        start_idx = 1 if first_header_row else 0
        ths_in_header_row = tr.find_all('th')
        ths2kill = ths_in_header_row[start_idx: n_header_cols]
        for th2kill in ths2kill:
            th2kill.decompose()  ## bye bye! Step 3 happens
    if debug and verbose:
        print(soup)
    tbl_html = str(soup)
    return tbl_html

def merge_cols_of_blanks(raw_tbl_html: str, *, debug=False) -> str:
    """
    Male 	__blank__ 	__blank__ ==> Male colspan=3

    We want to get from:

    <th class="row_heading level1 row6" id="T_d3b21_level1_row6">Male</th>
    <th class="row_heading level2 row6" id="T_d3b21_level2_row6">__blank__</th>
    <th class="row_heading level3 row6" id="T_d3b21_level3_row6">__blank__</th>

    -->

    <th class="row_heading level1 row6" colspan=3 id="T_d3b21_level1_row6">Male</th>

    Get th's in order which have class = 'row_heading'
    Get positional idxs of non-__blank__ th's
    Pair idx and next_idx (None for the last one, and None for the first if only one)
    Gap = colspan. Set colspan if more than the default of 1.
    If next_idx is None, just use length of total list to work out any col-spanning.
    """
    soup = BeautifulSoup(raw_tbl_html, 'html.parser')
    ths = soup.table.find_all('th', class_='row_heading')
    df_ths = pd.DataFrame.from_dict({'th': ths})
    df_ths.reset_index(inplace=True)
    df_ths.rename(columns={'index': 'label_idx'}, inplace=True)
    max_idx = len(df_ths)  ## index of item after end
    df_labelled_ths = df_ths[df_ths.apply(lambda row: row['th'].string != BLANK, axis=1)].copy()
    ## remove all blanks now from actual soup
    for blank_th in df_ths[df_ths.apply(lambda row: row['th'].string == BLANK, axis=1)]['th']:
        blank_th.decompose()
    ## set up idxs ready for working out row spans
    next_labelled_ths = list(df_labelled_ths['label_idx'])[1:] + [max_idx]
    df_labelled_ths['next_label_idx'] = next_labelled_ths
    df_labelled_ths['span'] = df_labelled_ths['next_label_idx'] - df_labelled_ths['label_idx']
    if debug:
        print(df_labelled_ths)
    ## Add rowspan to each th where > 1
    for _i, row in df_labelled_ths[df_labelled_ths['span'] > 1].iterrows():
        row['th']['colspan'] = str(row['span'])
    if debug:
        print(soup)
    tbl_html = str(soup)
    return tbl_html

def _get_upwards_row_to_col_idxs(trs_row_above_measures_first) -> dict[int: {int: str}]:
    """
    For example, we want to get from the HTML on the left to the dict on the right:

                              Browser                                                       Age Group                            row_idx: {col_idx: th, ...}
                Chrome                          Firefox                   <20        20-29       30-39      40-64        65+        2: {0: th(Chrome), 5: th(Firefox), 10: th(<20), 11: th(20-29), ...}
               Age Group                       Age Group                __blank__   __blank__   __blank__   __blank__   __blank__   1: {0: th(Age Group), 5: th(Age Group), 10: th(__blank__), 11: th(__blank__), ...}
    <20   20-29  30-39  40-64  65+    <20  20-29  30-39  40-64  65+ 	__blank__   __blank__   __blank__   __blank__   __blank__   0: {0: th(<20), 1: th(20-29), 2: th(30-39), ... 5: th(<20), ... 10: th(__blank__), 11: th(__blank__), ...}
    Freq  Freq   Freq   Freq  Freq   Freq  Freq   Freq   Freq   Freq      Freq        Freq        Freq        Freq        Freq      Ignored
    """
    upwards_row_to_col_idxs = {}
    for row_idx, tr in enumerate(trs_row_above_measures_first):
        col_idx_to_th = {}
        ths = tr.find_all('th')
        spans_to_add = 0
        for raw_col_idx, th in enumerate(ths):
            col_idx = raw_col_idx + spans_to_add
            col_idx_to_th[col_idx] = th
            extra_spans = int(th['colspan']) - 1 if th.get('colspan') is not None else 0  ## if a col spans 3 cols we only need to increment subsequent col_idxs by 2  TODO: check the attribute exists if 1 span
            if extra_spans:
                spans_to_add += extra_spans
        upwards_row_to_col_idxs[row_idx] = col_idx_to_th
    return upwards_row_to_col_idxs

def _get_blank_ths(trs) -> list:
    """
    Get list of table header (th) elements that are blank. At the end these will all be removed.
    """
    blank_ths = []
    for tr in trs:
        ths = tr.find_all('th')
        blank_ths_in_tr = [th for th in ths if th.string == BLANK]
        blank_ths.extend(blank_ths_in_tr)
    return blank_ths

def merge_rows_of_blanks(raw_tbl_html: str, *, debug=False, verbose=True) -> str:
    """
      20-29
    __blank__
    __blank__

    becomes

      20-29 rowspan=3

    etc

    We want to get from:
                              Browser                                                       Age Group
                Chrome                          Firefox                   <20        20-29       30-39      40-64        65+
               Age Group                       Age Group                __blank__   __blank__   __blank__   __blank__   __blank__
    <20   20-29  30-39  40-64  65+    <20  20-29  30-39  40-64  65+ 	__blank__ 	__blank__ 	__blank__ 	__blank__ 	__blank__    <========= row_above_measures (row index 0 counting upwards from bottom)
    Freq  Freq   Freq   Freq  Freq   Freq  Freq   Freq   Freq   Freq      Freq        Freq        Freq        Freq        Freq       <========= measures row

    -->
                              Browser                                                       Age Group
                Chrome                          Firefox                   <20        20-29       30-39      40-64        65+
               Age Group                       Age Group                    |          |           |          |           |   <=== pipes represent row spanning
    <20   20-29  30-39  40-64  65+    <20  20-29  30-39  40-64  65+ 	    |          |           |          |           |
    Freq  Freq   Freq   Freq  Freq   Freq  Freq   Freq   Freq   Freq      Freq        Freq        Freq        Freq        Freq

    We do this working upwards from the row_above_measures.
    We make that row 0 and the rows above it are 1, 2, .... etc.
    The outer process is to work across row_above_measures looking for BLANK (__blank__) th's.
    For each of these we then want to work upwards through the same horizontal position
    until we stop finding BLANKs in the th's and find an actual value in the th i.e. a label.
    We then row-span that valued (non-BLANK) th so it covers all the BLANK th's in the rows below it
    (we have kept track of the hops upwards).
    Because of col-spanning to our left, staying in the same position as we move upwards
    is not a simple matter of using the same th index position as in row_above_measures in the rows of th's above.
    More details on how that can be achieved in next paragraph.
    At end, .decompose() all BLANK th's in thead.

    Make a dict with row idx 0 being row_above_measures, 1 being the row above, and so on.
    Make the value a mapping from col_idx to th element. Because of col-spanning, some th col_idxs will not exist.
    For example:

                              Browser                                                       Age Group                            row_idx: {col_idx: th, ...}
                Chrome                          Firefox                   <20        20-29       30-39      40-64        65+        2: {0: th(Chrome), 5: th(Firefox), 10: th(<20), 11: th(20-29), ...}
               Age Group                       Age Group                __blank__   __blank__   __blank__   __blank__   __blank__   1: {0: th(Age Group), 5: th(Age Group), 10: th(__blank__), 11: th(__blank__), ...}
    <20   20-29  30-39  40-64  65+    <20  20-29  30-39  40-64  65+ 	__blank__   __blank__   __blank__   __blank__   __blank__   0: {0: th(<20), 1: th(20-29), 2: th(30-39), ... 5: th(<20), ... 10: th(__blank__), 11: th(__blank__), ...}
    Freq  Freq   Freq   Freq  Freq   Freq  Freq   Freq   Freq   Freq      Freq        Freq        Freq        Freq        Freq      Ignored

    Using the example above, we work across row_above_measures until we eventually encounter a BLANK at col_idx 10.
    In row_idx 1, col_idx 10 is still BLANK so we have 1 hop so far.
    In row_idx 2, col_idx 10 is not BLANK so we have 2 hops total and we can set the rowspan for that label th
    to the number of hops (2 in this case).
    Then move onto next col in row_above_measures.
    """
    soup = BeautifulSoup(raw_tbl_html, 'html.parser')
    trs = soup.table.find('thead').find_all('tr')
    trs_row_above_measures_first = reversed(trs)
    upwards_row_to_col_idxs = _get_upwards_row_to_col_idxs(trs_row_above_measures_first)
    row_above_measures = upwards_row_to_col_idxs[1]
    ## move rightwards across row_above_measures
    for col_idx, th in row_above_measures.items():
        if th.string == BLANK:
            ## iterate upwards
            for hop_n in count(1):
                aligned_th = upwards_row_to_col_idxs[1 + hop_n][col_idx]
                if aligned_th.string == BLANK:
                    continue
                else:
                    span = hop_n + 1
                    aligned_th['rowspan'] = str(span)
                    if debug and verbose:
                        print(f"{hop_n} {aligned_th}")
                    break
    blank_ths = _get_blank_ths(trs)
    ## remove all blanks now from actual soup
    for blank_th in blank_ths:
        blank_th.decompose()
    if debug:
        print(soup)
    tbl_html = str(soup)
    return tbl_html
