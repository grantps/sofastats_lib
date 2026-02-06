from tests.utils import contains_subsequence, found_amount_sequence_in_html_table

def test_contains_subsequence():
    found_tests = [
        ([1, ], [1, ]),
        ((1, ), [1, ]),
        ((1, ), (1, )),
        ([0, 1, 2, 3], [0, 1]),
        ([0, 1, 2, 3], [0, 1, 2, 3]),
        ([0, 1, 2, 3, 4, 5], [0, 1, 2, 3]),
        (['0', '1', '2', '3', '4', '5'], ['0', '1', '2', '3']),
        ([str, int, float, dict, tuple, set], [set, ]),
        ([0, 6, 2, 4], [0, 6, 2, 4]),
        ([0, 'sausage', 2.0, {4}], [0, 'sausage', 2.0, {4}]),
        ([0, 1.0, 2, 3], [0, 1]),
        ([0, 1, 2, 3], [0, 1.0]),
        ([1.234, 5.678], [1.234, ]),
    ]
    not_found_tests = [
        ([0, 1, 2, 3], [0, 1, 2, 3, 4]),
        (['0', '1', '2', '3', '4', '5'], [0, 1, 2, 3]),  ## would succeed if same type
        ([0, 1, 2, 3, 4, 5], ['0', '1', '2', '3']),  ## ditto
    ]
    for sequence, subsequence in found_tests:
        assert contains_subsequence(sequence=sequence, subsequence=subsequence, debug=True)
    for sequence, subsequence in not_found_tests:
        assert not contains_subsequence(sequence=sequence, subsequence=subsequence, debug=True)

has_subsequence_0 = """\
## just what we're looking for (the subsequence _is_ the sequence)
<td class="data row0 col0" id="T_c59ee_row0_col0">97</td>
<td class="data row0 col1" id="T_c59ee_row0_col1">171.123</td>  ## has to be able to extract entire number with digits after decimal point 
<td class="data row0 col2" id="T_c59ee_row0_col2">50</td>
<td class="data row0 col3" id="T_c59ee_row0_col3">318</td>
"""
has_subsequence_1 = """\
## as above but put an extra item before and after
<td class="data row0 col0" id="fake">666</td>
<td class="data row0 col0" id="T_c59ee_row0_col0">97</td>
<td class="data row0 col1" id="T_c59ee_row0_col1">171.123</td>
<td class="data row0 col2" id="T_c59ee_row0_col2">50</td>
<td class="data row0 col3" id="T_c59ee_row0_col3">318</td>
<td class="data row0 col3" id="fake">666</td>
"""
has_subsequence_2 = """\
## as above but put some of the same numbers earlier (albeit separated bu other numbers)
<td class="data row0 col0" id="fake">666</td>
<td class="data row0 col0" id="fake">97</td>
<td class="data row0 col0" id="fake">666</td>
<td class="data row0 col0" id="fake">171.123</td>
<td class="data row0 col0" id="fake">666</td>
<td class="data row0 col0" id="fake">50</td>
<td class="data row0 col0" id="fake">666</td>
<td class="data row0 col0" id="fake">318</td>
<td class="data row0 col0" id="fake">666</td>
<td class="data row0 col0" id="T_c59ee_row0_col0">97</td>
<td class="data row0 col1" id="T_c59ee_row0_col1">171.123</td>
<td class="data row0 col2" id="T_c59ee_row0_col2">50</td>
<td class="data row0 col3" id="T_c59ee_row0_col3">318</td>
<td class="data row0 col3" id="fake">666</td>
"""
lacks_subsequence_0 = """\
## missing 318 at end
<td class="data row0 col0" id="fake">97</td>
<td class="data row0 col0" id="fake">171.123</td>
<td class="data row0 col0" id="fake">50</td>
"""
lacks_subsequence_1 = """\
## separated by other numbers
<td class="data row0 col0" id="fake">97</td>
<td class="data row0 col0" id="fake">666</td>
<td class="data row0 col0" id="fake">171.123</td>
<td class="data row0 col0" id="fake">666</td>
<td class="data row0 col0" id="fake">50</td>
<td class="data row0 col0" id="fake">666</td>
<td class="data row0 col0" id="fake">318</td>
"""
lacks_subsequence_2 = """\
## Has different numbers when digits after the decimal point are taken into account.
## Looking for 97, ... should fail because it _should_ be looking in 97.1, ...
<td class="data row0 col0" id="T_c59ee_row0_col0">97.1</td>
<td class="data row0 col1" id="T_c59ee_row0_col1">171.1</td>
<td class="data row0 col2" id="T_c59ee_row0_col2">50.1</td>
<td class="data row0 col3" id="T_c59ee_row0_col3">318.1</td>
"""

def test_found_number_sequence_in_html_table():
    debug = True
    vals_sequences = [
        (97, 171.123, 50, 318),
        ('97', '171.123', '50', '318'),
    ]
    for vals2find in vals_sequences:
        assert found_amount_sequence_in_html_table(text=has_subsequence_0, vals2find=vals2find, debug=debug)
        assert found_amount_sequence_in_html_table(text=has_subsequence_1, vals2find=vals2find, debug=debug)
        assert found_amount_sequence_in_html_table(text=has_subsequence_2, vals2find=vals2find, debug=debug)
        assert not found_amount_sequence_in_html_table(text=lacks_subsequence_0, vals2find=vals2find, debug=debug)
        assert not found_amount_sequence_in_html_table(text=lacks_subsequence_1, vals2find=vals2find, debug=debug)
        assert not found_amount_sequence_in_html_table(text=lacks_subsequence_2, vals2find=vals2find, debug=debug)

if __name__ == '__main__':
    pass
    # test_contains_subsequence()
    test_found_number_sequence_in_html_table()
