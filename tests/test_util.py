from datetime import datetime

import pytest

from pybooks.util import parse_date, truncate, normal_round

# Taking this out for now, good attempt, but I don't know if this belongs here

def test_parse_date():
    test_date = datetime(2023, 7, 23, 0, 0, 0)

    assert parse_date('2023$07$23', '%Y$%m$%d') == test_date

    invalid_dates = (
        'x',
        '2023/05',
        '5/23/23'
    )

    for date in invalid_dates:
        assert parse_date(date) is None

    valid_dates = (
        'Sun July 23, 2023',
        'SUNDAY-JULY-23, 2023',
        'SUN/JUL/23/2023',
        '00:00:00 Sunday-Jul,23 2023',
    )
    for date in valid_dates:
        assert parse_date(date) == test_date

def test_truncate():
    assert truncate(23.9, 0) == 23
    assert truncate(23.5, 0) == 23
    assert truncate(23.2, 0) == 23

    assert truncate(23.564, 2) == 23.56

def test_normal_round():
    assert normal_round(23.6, 0) == 24
    assert normal_round(23.5, 0) == 24
    assert normal_round(23.4, 0) == 23

    assert normal_round(23.48, 1) == 23.5
    assert normal_round(23.45, 1) == 23.5
    assert normal_round(23.43, 1) == 23.4

    assert normal_round(23.457, 2) == 23.46
    assert normal_round(23.455, 2) == 23.46
    assert normal_round(23.451, 2) == 23.45