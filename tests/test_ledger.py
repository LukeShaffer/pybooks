'''
Basic fundamental functional tests of the ledger system
'''
import re
from datetime import datetime

import pytest

from pybooks.ledger import GeneralLedger, SubLedger
from pybooks.account import Account, AccountNumberSegment, \
    AccountNumberTemplate
from pybooks.journal import Journal, JournalEntry
from pybooks.enums import AccountType
from pybooks.util import DuplicateException, InvalidAccountNumberException

from util import init_template

def test_init():
    template = init_template()
    gen = GeneralLedger('general ledger', account_number_template=template)
    GeneralLedger('gen2', account_number_template=template,
                  accounting_method=None)
    SubLedger('Cash', general_ledger=gen)
    SubLedger('Cash2', general_ledger=gen, accounting_method=None)

    with pytest.raises(ValueError):
        SubLedger('Cash3', account_number_template='some value')

    seg1 = AccountNumberSegment('test', {re.compile(r'\d'): 'test'},
                                is_regex=True)
    template = AccountNumberTemplate(seg1)

    gen = GeneralLedger('general', account_number_template=template)
    sub = SubLedger('Cash', general_ledger=gen)
    sub.add_account('test_account', '1', AccountType.CREDIT)

def test_add_accounts():
    template = init_template()

    gen = GeneralLedger('general', template)

    account1 = Account('acc1', '01-01-101', AccountType.CREDIT,
                       template=template)
    account2 = Account('acc2', '01-01-202', AccountType.DEBIT,
                       template=template)
    account3 = Account('acc3', '01-01-303', AccountType.CREDIT,
                       template=template)
    account_dup = Account('newacc', '01-01-101', AccountType.DEBIT,
                          template=template)
    account_dup2 = Account('newacc', '01-01-404', AccountType.DEBIT,
                           template=template)

    # Adding an account with a different template will raise an error
    with pytest.raises(ValueError):
        seg = AccountNumberSegment('test', {'1': 'no_meaning'})
        gen.add_account(Account('asd', '1', AccountType.CREDIT,
                                template=AccountNumberTemplate(seg)))
    
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

    # Add a new account from just the details
    gen.add_account('raw acc', '01-02-101', AccountType.CREDIT)
    assert gen.accounts.get('01-02-101') is not None

    '''
    # Subledger section
    sub = SubLedger('Cash', general_ledger=gen)
    sub.add_account(account1)
    sub.add_account(account2)
    sub.add_account(account3)

    with pytest.raises(DuplicateException):
        sub.add_account(account1)
    '''
    

def test_filter_accounts():
    template = init_template()

    gen = GeneralLedger('general ledger', template)

    acc1 = Account('account 1', '10-02-200', AccountType.DEBIT,
                   template=template)
    acc2 = Account('account 2', '10-00-300', AccountType.CREDIT,
                   template=template)
    acc3 = Account('account 3', '01-00-300', AccountType.DEBIT,
                   template=template)
    acc4 = Account('account 4', '11-01-500', AccountType.CREDIT,
                   template=template)

    for acc in (acc1, acc2, acc3, acc4):
        gen.add_account(acc)

    # Test no arguments
    assert gen.filter_accounts() == []

    # Try each segment of the template
    assert gen.filter_accounts(company_code='10') == [acc1, acc2]
    assert gen.filter_accounts(department_code='00') == [acc2, acc3]
    assert gen.filter_accounts(account_code='500') == [acc4]

    # ints will be casted to strings
    assert gen.filter_accounts(account_code=500) == [acc4] 
    # Will not 0-fill
    assert gen.filter_accounts(company_code=1) == []

    # Valid filter key but invalid value
    assert gen.filter_accounts(company_code='99') == []

    # Non-existant key
    assert gen.filter_accounts(division_code_DNE='DNE') == []

    # Test that we are able to get accounts from their names
    assert gen.filter_accounts(name='account 1') == [acc1]
    assert gen.filter_accounts(name='account') == []

    # Test multiple filters provide AND functionality
    assert gen.filter_accounts(name='account 1', company_code=10) == [acc1]

    # Test non-default OR behavior
    results = gen.filter_accounts(match_all=False, name='account 1',
                               company_code='01')
    assert results == [acc1, acc3]

def test_filter_account__in():
    '''
    Test the kw__in filter arg to filter_accounts
    '''
    template = init_template()

    gen = GeneralLedger('general ledger', template)

    acc1 = Account('account 1', '10-02-200',  AccountType.DEBIT,
                   template=template)
    acc2 = Account('account 2', '10-00-300', AccountType.CREDIT,
                   template=template)
    acc3 = Account('account 3', '01-00-300', AccountType.DEBIT,
                   template=template)
    acc4 = Account('account 4', '11-01-500', AccountType.CREDIT,
                   template=template)

    for acc in (acc1, acc2, acc3, acc4):
        gen.add_account(acc)
    
    results = gen.filter_accounts(name__in=['account 1', 'account 2'])
    assert results == [acc1, acc2]

    results = gen.filter_accounts(department_code__in=['01', '00'])
    assert results == [acc2, acc3, acc4]

def test_get_account():
    '''
    Make sure the API to get only a single account throws an error if more
    than 1 account is returned
    '''
    template = init_template()

    gen = GeneralLedger('general ledger', template)

    acc1 = Account('account 1', '10-02-200', AccountType.DEBIT,
                   template=template)
    acc2 = Account('account 2', '10-00-300', AccountType.CREDIT,
                   template=template)
    acc3 = Account('account 3', '01-00-300', AccountType.DEBIT,
                   template=template)
    acc4 = Account('account 4', '11-01-500', AccountType.CREDIT,
                   template=template)

    for acc in (acc1, acc2, acc3, acc4):
        gen.add_account(acc)
    
    assert gen.filter_accounts(account_code=500) == [acc4]
    # The returned value must be a single account, not an iterable
    assert gen.get_account(account_code='500') == acc4
    assert gen.get_account(account_code=500) == acc4

    assert gen.get_account(account_code=123213) is None

    # Throw an error is multiple accounts are returned
    with pytest.raises(ValueError):
        gen.get_account(company_code='10')

    # Searching for a non-existant filter returns None
    assert gen.get_account(account_filter=500) is None

def test_get_net_balance():
    '''
    define and test the API for aggregating balances for a subset of the
    ledger's accounts
    '''
    template = init_template()

    gen = GeneralLedger('general ledger', template)

    acc1 = Account('account 1', '10-02-200', AccountType.DEBIT,
                   template=template)
    acc2 = Account('account 2', '10-00-300', AccountType.CREDIT,
                   template=template)
    acc3 = Account('account 3', '01-00-300', AccountType.DEBIT,
                   template=template)
    acc4 = Account('account 4', '11-01-500', AccountType.CREDIT,
                   template=template)

    for acc in (acc1, acc2, acc3, acc4):
        gen.add_account(acc)
    
    j = Journal()

    # Debit acc1 $5000 from acc2
    # Debit acc3 $10000 from acc4
    for _ in range(10):
        je = JournalEntry(datetime.now(), acc1, acc2, 500)
        j.add_entry(je)
        je = JournalEntry(datetime.now(), acc3, acc4, 1000)
        j.add_entry(je)

    # When netting credits and debits, the balance should cancel
    result = gen.get_net_balance(name__in=['account 1', 'account 2'],
                                 match_all=False, 
                                 reporting_format=AccountType.DEBIT)
    assert result == 0

    result = gen.get_net_balance(name__in=['account 1', 'account 2'],
                                 match_all=False,
                                 reporting_format=AccountType.CREDIT)
    assert result == 0

    result = gen.get_net_balance(name__in=['account 1', 'account 4'],
                                 match_all=False,
                                 reporting_format=AccountType.DEBIT)
    assert result == -5000


    result = gen.get_net_balance(name__in=['account 1', 'account 4'],
                                 match_all=False,
                                 reporting_format=AccountType.CREDIT)
    assert result == 5000

    # When netting only credits or debits, the amounts should combine

    result = gen.get_net_balance(name__in=['account 1', 'account 3'],
                                 match_all=False,
                                 reporting_format=AccountType.DEBIT)
    assert result == 15000

    result = gen.get_net_balance(name__in=['account 1', 'account 3'],
                                 match_all=False,
                                 reporting_format=AccountType.CREDIT)
    assert result == -15000

    result = gen.get_net_balance(name__in=['account 2', 'account 4'],
                                 match_all=False,
                                 reporting_format=AccountType.DEBIT)
    assert result == -15000

    result = gen.get_net_balance(name__in=['account 2', 'account 4'],
                                 match_all=False,
                                 reporting_format=AccountType.CREDIT)
    assert result == 15000
    
    # Directly supplying the accounts should function the same
    result = gen.get_net_balance(accounts=[acc2, acc4],
                                 reporting_format=AccountType.DEBIT)
    assert result == -15000


def test_compare_chart_of_accounts():
    '''
    I am running into an issue where two charts of accounts from two separate
    general ledgers with identical accounts are failing the equality check
    '''
    template = init_template()

    gen = GeneralLedger('general ledger', account_number_template=template)
    gen2 = GeneralLedger('gen ledger 2', account_number_template=template)

    acc1 = Account('acc1', '10-02-200', AccountType.DEBIT, template=template)
    acc2 = Account('acc2', '10-00-300', AccountType.CREDIT, template=template)
    acc3 = Account('acc3', '01-00-300', AccountType.DEBIT, template=template)
    acc4 = Account('acc4', '11-01-500', AccountType.CREDIT, template=template)

    for acc in (acc1, acc2, acc3, acc4):
        gen.add_account(acc)
        gen2.add_account(acc)

    assert gen.chart_of_accounts == gen2.chart_of_accounts

    # Now adding an "identical" but separate account to each ledger should
    # make their charts of accounts different

    gen.add_account('new account', '12-01-300', AccountType.CREDIT)
    gen2.add_account('new account', '12-01-300', AccountType.DEBIT)

    assert gen.chart_of_accounts != gen2.chart_of_accounts

def test_view():
    pass

# TODO add other tests for other views and ratios of a ledger