from datetime import datetime

import pytest

from pybooks.util import parse_date, truncate, normal_round,\
    calculate_progressive_tax

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
    assert truncate(23.549, 2) == 23.54

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


def test_calculate_income_tax():
    tax_brackets = [
        (0.01, 100),
        (0.02, 200),
    ]

    assert calculate_progressive_tax(50, tax_brackets) == 0.50
    assert calculate_progressive_tax(150, tax_brackets) == 1 + 0.02 * 50
    assert calculate_progressive_tax(200, tax_brackets) == 3

    # Fraction test
    assert calculate_progressive_tax(100.50, tax_brackets) == 1 + 0.01

    with pytest.raises(ValueError):
        calculate_progressive_tax(1000000, tax_brackets)
    
    tax_brackets.append((0.5, 'inf'))

    assert calculate_progressive_tax(1000, tax_brackets) == \
        3 + 0.5 * 800
    
    assert calculate_progressive_tax(1_000_000, tax_brackets) == \
        3 + 0.5 * (1_000_000 - 200)

    # Now testing with real us tax brackets ('23)
    tax_brackets = [
        (0.1, 11_000),
        (0.12, 44_725),
        (0.22, 95_375),
        (0.24, 182_100),
        (0.32, 231_250),
        (0.35, 578_125),
        (0.37, 'inf')
    ]

    assert calculate_progressive_tax(15_000, tax_brackets) == 1100 + 0.12 * 4_000
    assert calculate_progressive_tax(50_000, tax_brackets) == \
        1100 + 4047 + 0.22 * (50_000 - 44_725)
    
    assert calculate_progressive_tax(1_000_000, tax_brackets) == \
        174_238.25 + 0.37 * (1_000_000 - 578_125)


