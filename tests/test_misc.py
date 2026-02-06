from sofastats.utils.misc import correct_str_dps


def test_correct_str_dps():
    """
    Apply decimal points to floats only - leave Freq integers alone.
    Assumes already rounded to correct dp's.
    3dp
    '0.0' => '0.000'
    '12' => '12'
    """
    tests = [
        ('0.0', '0.000', 3),
        ('12', '12', 3),
        ('0.00', '0.000', 3),
        ('-0.00', '-0.000', 3),
        ('1,234,567', '1,234,567', 3),
        ('1,234,567.12', '1,234,567.120', 3),
    ]
    for val, expected, decimal_points in tests:
        actual = correct_str_dps(val, decimal_points=decimal_points)
        assert actual == expected

if __name__ == "__main__":
    pass
    test_correct_str_dps()
