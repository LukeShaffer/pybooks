from datetime import datetime

import pytest

from pybooks.util import parse_date

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
