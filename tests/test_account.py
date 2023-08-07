from datetime import datetime
import re

import pytest

from pybooks.account import Account, _AccountNumber, AccountNumberSegment,\
    AccountNumberTemplate
from pybooks.journal import Journal, JournalEntry
from pybooks.enums import AccountType
from pybooks.util import InvalidAccountNumberException

def init_template():
    '''
    Reusable test code
    '''
    seg1_vals = {
        f'{key:02}': val
        for key, val in [(_, f'cmpny{_}') for _ in range(1, 4)]
    }
    seg1_vals.update({
        f'{key:02}': val
        for key, val in [(_, f'cmpny{_}') for _ in range(10, 15)]
    })

    seg2_vals = {
        f'{key:02}': val
        for key, val in [(_, f'dpt{_}') for _ in range(3)]
    }

    seg1 = AccountNumberSegment(seg1_vals)
    seg2 = AccountNumberSegment(seg2_vals)

    seg3 = [
        AccountNumberSegment(
            re.compile(r'1\d\d'), length=3, flat_value='Assets'),
        AccountNumberSegment(
            [f'{_:03}' for _ in range(200, 300)], flat_value='Liabilities'),
        AccountNumberSegment(
            re.compile(r'3\d\d'), length=3, flat_value='Equity'),
        AccountNumberSegment(
            [f'{_:03}' for _ in range(400, 500)], flat_value='Revenue'),
        AccountNumberSegment(
            re.compile(r'5\d\d'), length=3, flat_value='Expenses'),
    ]

    template = AccountNumberTemplate((
        ('Division Code', seg1),
        ('Department Code', seg2),
        ('Account Code', *seg3)
    ))
    return template

def test_init():
    seg = AccountNumberSegment({'1': 'test'})
    template = AccountNumberTemplate([
        ('acc_num', seg)
    ])
    _AccountNumber('1', template)
    Account('Cash - BMO', '1', template, AccountType.DEBIT)
    template = init_template()


def test_account_number_segments():
    '''
    I have created new classes for more exact control of account numbers
    '''
    seg1_vals = {
        f'{key:02}': val
        for key, val in zip(range(1, 4), ['cmpny1', 'cmpny2', 'cmpny3'])
    }
    seg1_vals.update({
        f'{key:02}': val
        for key, val in zip(range(10, 15), ['cmpny10', 'cmpny11', ...])
    })

    seg2_vals = {
        f'{key:02}': val
        for key, val in zip(range(3), ['dpt0', 'dpt1', 'dpt2'])
    }

    seg1 = AccountNumberSegment(seg1_vals)
    seg2 = AccountNumberSegment(seg2_vals)

    assert seg1['01'] == 'cmpny1'
    assert seg1['11'] == 'cmpny11'
    assert seg2['02'] == 'dpt2'

    seg3 = [
        AccountNumberSegment(
            [f'{_:03}' for _ in range(100, 200)], flat_value='Assets'),
        AccountNumberSegment(
            [f'{_:03}' for _ in range(200, 300)], flat_value='Liabilities'),
        AccountNumberSegment(
            [f'{_:03}' for _ in range(300, 400)], flat_value='Equity'),
        AccountNumberSegment(
            [f'{_:03}' for _ in range(400, 500)], flat_value='Revenue'),
        AccountNumberSegment(
            re.compile(r'5\d{2}'), flat_value='Expenses', length=3),
    ]

    # Test the raw flat_value behavior
    assert seg3[0]['100'] == 'Assets'
    assert seg3[2]['300'] == 'Equity'

    with pytest.raises(KeyError):
        assert seg3[0]['300'] == 'Invalid'

    # Test regex behavior
    assert seg3[4].get_key_length() == 3
    with pytest.raises(TypeError):
        AccountNumberSegment(re.compile(r'test\d'), flat_value='no length')

    with pytest.raises(InvalidAccountNumberException):
        AccountNumberSegment(re.compile(r'\d{1,2}'))
    
    with pytest.raises(InvalidAccountNumberException):
        AccountNumberSegment(re.compile(r'\d+'))

def test_account_number_template():
    template = init_template()

    assert template._show_form() == 'XX-XX-XXX'

    valid_numbers = (
        '01-02-100',
        '01-02-350',
        '10-00-450',
        '10-00-599',
    )

    for number in valid_numbers:
        assert template.validate_account_number(number)

    invalid_numbers = (
        '00-02-100',
        '10--02-100',
        ' 10-02-100',
        '10-99-100',
        '10-02-99',
        '10_00_599',
        '10-00-700'
    )

    for number in invalid_numbers:
        assert template.validate_account_number(number) is False
    
    assert template.validate_account_number('10_00_450', separator='_')

def test_show_account_template():
    # TODO write a test to verify the show_template() function shows the
    # possible values for each segment.
    template = init_template()

    assert template._show_form() == 'XX-XX-XXX'


def test_account_number():
    '''
    Test various functionality of the _AccountNumber class
    '''
    template = init_template()

    number1 = _AccountNumber('10-02-200', template)
    number2 = _AccountNumber('10-00-300', template)
    number3 = _AccountNumber('01-00-300', template)
    number4 = _AccountNumber('11-01-500', template)

    with pytest.raises(InvalidAccountNumberException):
        _AccountNumber('99-00-200', template)
    
    assert number1 != number2
    assert not number1 == number2

    assert number1 == _AccountNumber('10-02-200', template)

    assert number2 < number1
    assert number1 > number2
    assert all([number3 < num for num in [number1, number2, number4]])
    assert all([number4 > num for num in [number1, number2, number3]])

    assert number1['Division Code'] == '10'
    assert number1['Department Code'] == '02'
    assert number2['Department Code'] == '00'
    assert number4['Account Code'] == '500'


def test_add_journal():
    template = init_template()

    j = Journal()

    acc_credit = Account('Creditor', '01-01-100', template, AccountType.CREDIT)
    acc_debit = Account('Debtor', '01-01-101', template, AccountType.DEBIT)

    now = datetime(2023, 7, 23)
    for _ in range(3):
        je = JournalEntry(now, acc_debit, acc_credit, 100)
        j.add_entry(je)
    
    assert len(acc_credit.journal_entries) == 3
    assert len(acc_debit.journal_entries) == 3

def test_gross_balance():
    template = init_template()
    j = Journal()

    acc_credit = Account('Creditor', '01-01-100', template, AccountType.CREDIT)
    acc_debit = Account('Debtor', '01-01-101', template, AccountType.DEBIT)

    now = datetime(2023, 7, 23)
    for _ in range(3):
        je = JournalEntry(now, acc_debit, acc_credit, 100)
        j.add_entry(je)
    
    assert acc_credit.gross_credit == 300
    assert acc_debit.gross_debit == 300