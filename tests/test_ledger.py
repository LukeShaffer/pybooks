'''
Basic fundamental functional tests of the ledger system
'''
import re

import pytest

from pybooks.ledger import GeneralLedger, SubLedger
from pybooks.account import Account, AccountNumberSegment, \
    AccountNumberTemplate
from pybooks.enums import CoreSubledgers
from pybooks.util import DuplicateException, NullAccountTemplateError, \
    InvalidAccountNumberException

def init_template():
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
            re.compile(r'0\d\d'), length=3, flat_value='Assets'),
        AccountNumberSegment(
            [f'{_:03}' for _ in range(100, 300)], flat_value='Liabilities'),
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
    template = init_template()
    gen = GeneralLedger('general ledger')
    gen2 = GeneralLedger('gen2', accounting_method=None)
    sub = SubLedger('Cash', general_ledger=gen)
    sub2 = SubLedger('Cash2', general_ledger=gen, accounting_method=None)

    with pytest.raises(ValueError):
        sub3 = SubLedger('Cash3', account_number_template='some value')

    seg1 = AccountNumberSegment(re.compile(r'\d'), flat_value='test', length=1)
    template = AccountNumberTemplate([
        ('ID', seg1)
    ])

    gen = GeneralLedger('general')
    sub = SubLedger('Cash', general_ledger=gen)

def test_add_accounts():
    template = init_template()

    gen = GeneralLedger('general')
    sub = SubLedger('Cash', general_ledger=gen)

    account1 = Account('acc1', '01-01-001', template)
    account2 = Account('acc2', '01-01-002', template)
    account3 = Account('acc3', '01-01-003', template)
    account_dup = Account('newacc', '01-01-001', template)
    account_dup2 = Account('newacc', '01-01-004', template)

    sub.add_account(account1)
    sub.add_account(account2)
    sub.add_account(account3)

    with pytest.raises(DuplicateException):
        sub.add_account(account1)
    
    # No error is added
    gen.add_account(account1)

    # Now is a duplicate
    with pytest.raises(DuplicateException):
        gen.add_account(account1)
    
    # Trying to add a new account with a pre-existing number raises an error
    with pytest.raises(DuplicateException):
        gen.add_account(account_dup)
    
    # Adding an account with a duplicate name but a unique number is allowed
    gen.add_account(account_dup2)
    

def test_filter_accounts():
    template = init_template()

    gen = GeneralLedger('general ledger')

    acc1 = Account('account 1', '10-02-200', template)
    acc2 = Account('account 2', '10-00-300', template)
    acc3 = Account('account 3', '01-00-300', template)
    acc4 = Account('account 4', '11-01-500', template)

    for acc in (acc1, acc2, acc3, acc4):
        gen.add_account(acc)

    # Test no arguments
    assert gen.filter_accounts() == []

    assert gen.filter_accounts(account_code='500') == [acc4]
    assert gen.filter_accounts(department_code='02') == [acc1]
    assert gen.filter_accounts(department_code='00') == [acc2, acc3]
    assert gen.filter_accounts(division_code='10') == [acc1, acc2]

    assert gen.filter_accounts(division_code='05') == []

    # Test that we are able to get accounts from their names
    assert gen.filter_accounts(name='account 1') == [acc1]
    assert gen.filter_accounts(name='account') == []

    # Test multiple filters provide AND functionality
    assert gen.filter_accounts(name='account 1', division_code=10) == [acc1]

    # Test non-default OR behavior
    results = gen.filter_accounts(match_all=False, name='account 1',
                               division_code='01')
    assert results == [acc1, acc3]

def test_get_account():
    '''
    Make sure the API to get only a single account throws an error if more
    than 1 account is returned
    '''
    template = init_template()

    gen = GeneralLedger('general ledger')

    acc1 = Account('account 1', '10-02-200', template)
    acc2 = Account('account 2', '10-00-300', template)
    acc3 = Account('account 3', '01-00-300', template)
    acc4 = Account('account 4', '11-01-500', template)

    for acc in (acc1, acc2, acc3, acc4):
        gen.add_account(acc)
    
    assert gen.filter_accounts(account_code=500) == [acc4]
    assert gen.get_account(account_code='500') == acc4
    assert gen.get_account(account_code=500) == acc4

    assert gen.get_account(account_code=123213) is None


def test_compare_chart_of_accounts():
    '''
    I am running into an issue where two charts of accounts from two separate
    general ledgers with identical accounts are failing the equality check
    '''
    template = init_template()

    gen = GeneralLedger('general ledger')
    gen2 = GeneralLedger('gen ledger 2')

    acc1 = Account('account 1', '10-02-200', template)
    acc2 = Account('account 2', '10-00-300', template)
    acc3 = Account('account 3', '01-00-300', template)
    acc4 = Account('account 4', '11-01-500', template)

    for acc in (acc1, acc2, acc3, acc4):
        gen.add_account(acc)
        gen2.add_account(acc)

    assert gen.chart_of_accounts == gen2.chart_of_accounts

    # Now adding an "identical" but separate account to each ledger should
    # make their charts of accounts different

    gen.add_account(Account("new account", '12-01-000', template))
    gen2.add_account(Account('new account', '12-01-000', template))

    assert gen.chart_of_accounts != gen2.chart_of_accounts

def test_view():
    pass

# TODO add other tests for other views and ratios of a ledger