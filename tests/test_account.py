from datetime import datetime
import re

import pytest

from pybooks.account import Account, _AccountNumber, AccountNumberSegment,\
    AccountNumberTemplate, ChartOfAccounts
from pybooks.journal import Journal, JournalEntry
from pybooks.enums import AccountType
from pybooks.util import InvalidAccountNumberException, DuplicateException

from util import init_template


def test_init():
    seg = AccountNumberSegment('test seg', {'1': 'test'})
    template = AccountNumberTemplate(seg)
    acc_num = _AccountNumber('1', template)
    Account('Cash - BMO', '1', AccountType.DEBIT, template=template)

    ChartOfAccounts(template)
    # Test that the template I use for all my other tests inits
    template = init_template()

def test_account_number_segments():
    '''
    I have created new classes for more exact control of account numbers
    '''
    seg1_vals = {
        f'{num:02}': f'cmpny{num}'
        for num in range(1, 4)
    }
    seg1_vals.update({
        f'{num:02}': f'cmpny{num}'
        for num in range(10, 15)
    })

    seg1 = AccountNumberSegment('Comany Name', seg1_vals)
    seg2 = AccountNumberSegment('Department Name', {
        f'{num:02}': f'dpt{num}'
        for num in range(3)
    })

    assert seg1['01'] == 'cmpny1'
    assert seg1['11'] == 'cmpny11'
    assert seg2['02'] == 'dpt2'

    seg3 = AccountNumberSegment('Account Type', {
        re.compile(r'1\d\d'): 'Assets',
        re.compile(r'2\d\d'): 'Liabilities',
        re.compile(r'3\d\d'): 'Equity',
        re.compile(r'4\d\d'): 'Revenue',
        re.compile(r'5\d\d'): 'Expenses',
    }, is_regex=True)

    # Test regex __getitem__ behavior
    assert seg3['100'] == 'Assets'
    assert seg3['300'] == 'Equity'

    # Partial matches must not succeed
    with pytest.raises(KeyError):
        seg3['3000']
    
    with pytest.raises(KeyError):
        seg3['0300']

    # Variable length regex's are not allowed
    var_len_regex = (
        re.compile(r'\d{1}'),
        re.compile(r'\d{1,2}'),
        re.compile(r'\d+')
    )

    for reg in var_len_regex:
        with pytest.raises(InvalidAccountNumberException):
            AccountNumberSegment('test', {reg: 'value'}, is_regex=True)

    # Forgetting to designate a regex segment as a regex raises an error
    with pytest.raises(TypeError):
        AccountNumberSegment('test', {re.compile(r'\d'): 'a'})

    # Creating a regex segment with different length regexs raises an error
    regex = {
        re.compile(r'\d'): '1',
        re.compile(r'\d\d'): '2',
    }
    with pytest.raises(InvalidAccountNumberException):
        AccountNumberSegment('test', regex, is_regex=True)

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
        '10-02-001',
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

def test_account_number_from_template():
    '''
    8/20/23 I am shelving the idea of default segments
    In order to facilitate creating larger account numbers with default
    sections, I have added an API to create an account number from named
    values for each of the segments of an account number, additionally
    including default
    
    template = init_template()

    acc = Account.from_template(template, AccountType.CREDIT, {
        'Company Code': '01',
        'Department Code': '01',
        'Account Code': '100'
    })

    Account.from_template(template, AccountType.DEBIT, {
        'DNE': 'sdfdsfsf',
        'Account Code': '100'
    })
    '''

    rules = {
        'Company Code': '01',
        'Department Code': '01',
        'Account Code': '100'
    }
    template = init_template()
    acc_num = template.make_account_number(**rules)

    # assert acc_num.company_code == '01'
    # assert acc_num.department_code == '01'

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
    assert (number1 == number2) is False

    assert number1 == _AccountNumber('10-02-200', template)

    assert number2 < number1
    assert number1 > number2
    assert all([number3 < num for num in [number1, number2, number4]])
    assert all([number4 > num for num in [number1, number2, number3]])

    assert number1['Company Code'] == '10'
    assert number1['Department Code'] == '02'
    assert number2['Department Code'] == '00'
    assert number4['Account Code'] == '500'

    assert number1.number == '10-02-200'

def test_add_journal():
    template = init_template()

    j = Journal()

    acc_credit = Account('Creditor', '01-01-100', AccountType.CREDIT,
                         template=template)
    acc_debit = Account('Debtor', '01-01-101', AccountType.DEBIT,
                        template=template)

    now = datetime(2023, 7, 23)
    for _ in range(3):
        je = JournalEntry(now, acc_debit, acc_credit, 100)
        j.add_entry(je)
    
    assert len(acc_credit.journal_entries) == 3
    assert len(acc_debit.journal_entries) == 3

def test_gross_balance():
    template = init_template()
    j = Journal()

    acc_credit = Account('Creditor', '01-01-100', AccountType.CREDIT,
                         template=template)
    acc_debit = Account('Debtor', '01-01-101', AccountType.DEBIT,
                        template=template)

    now = datetime(2023, 7, 23)
    for _ in range(3):
        je = JournalEntry(now, acc_debit, acc_credit, 100)
        j.add_entry(je)
    
    assert acc_credit.gross_credit == 300
    assert acc_debit.gross_debit == 300

# ChartOfAccounts tests
def test_chart_of_accounts_add_account():
    seg = AccountNumberSegment('test seg', {'1': 'test', '2': 'test'})
    template = AccountNumberTemplate(seg)
    account = Account('Cash - BMO', '1', AccountType.DEBIT, template=template)
    chart = ChartOfAccounts(template)

    chart.add_account(account)

    with pytest.raises(DuplicateException):
        chart.add_account(account)
    
    chart.add_account('new account', '2', AccountType.CREDIT)

    # Adding an account with a different template raises an error
    seg2 = AccountNumberSegment('seg', {'100': 'test'})
    template2 = AccountNumberTemplate(seg2)
    with pytest.raises(ValueError):
        chart.add_account(Account('test', '100', AccountType.CREDIT,
                                template=template2))

def test_account():
    template = init_template()
    acc_num = _AccountNumber('01-01-100', template)

    # Test equality
    acc1 = Account('Cash - JPM', acc_num, AccountType.CREDIT)
    acc2 = Account('Cash - JPM', '01-01-100', AccountType.CREDIT,
                   template=template)
    
    assert acc1 == acc2

    # Name, number, and accountType must all match
    assert acc1 != Account('Cash - BMO', acc_num, AccountType.CREDIT)
    assert acc1 != Account('Cash - JPM', '02-01-100', AccountType.CREDIT,
                           template=template)
    assert acc1 != Account('Cash - JPM', acc_num, AccountType.DEBIT)

    # Accounts must have a name
    with pytest.raises(ValueError):
        Account('', '01-01-100', AccountType.CREDIT, template=template)

    # String account numbers must be initialized with a template
    with pytest.raises(TypeError):
        Account('test', '123', AccountType.CREDIT)

    # Create an account with an invalid accountType
    with pytest.raises(ValueError):
        Account('test', '01-01-100', 'invalid', template=template)

    # Getitem should automatically return the account number's value
    assert acc1['Company Code'] == '01' 

    
def test_account_aggregation():
    '''
    I am going to need a way to roll up multiple accounts and just get the
    end net debit or credit balance
    '''
    template = init_template()
    accounts = []

    for x in range(3):
        accounts.append(Account('acc', f'01-{x:02}-100', AccountType.CREDIT,
                                template=template))
    
    # No transactions have been posted
    assert Account.net_balance_agg(accounts, AccountType.CREDIT) == 0
    assert Account.net_balance_agg(accounts, AccountType.DEBIT) == 0

    # Don't need to post it anywhere, just the creation will register the 
    # balance
    # Debit acc0 and credit acc1
    JournalEntry(datetime.now(), accounts[0], accounts[1], 100)

    assert Account.net_balance_agg(accounts, AccountType.CREDIT) == 0
    assert Account.net_balance_agg(accounts, AccountType.DEBIT) == 0

    assert Account.net_balance_agg(accounts[1:], AccountType.CREDIT) == 100
    assert Account.net_balance_agg(accounts[1:], AccountType.DEBIT) == -100

    JournalEntry(datetime.now(), accounts[0], accounts[2], 500)
    assert Account.net_balance_agg(accounts[1:], AccountType.CREDIT) == 600
    assert Account.net_balance_agg([accounts[0]], AccountType.DEBIT) == 600

def test_get_net_transfer():
    '''
    Check the transfers from one group of accounts to another
    '''
    debit_accounts = []
    credit_accounts = []

    template = init_template()
    for x in range(1, 4):
        debit_accounts.append(Account(f'acc{x}', f'{x:02}-01-100',
                                      AccountType.CREDIT, template=template))
    for x in range(10, 15):
        credit_accounts.append(Account(f'acc{x}', f'{x:02}-01-100',
                                       AccountType.DEBIT, template=template))
    
    for _ in range(3):
        acc_debit = debit_accounts[_]
        acc_credit = credit_accounts[_]
        JournalEntry(datetime.now(), acc_debit, acc_credit, 100)
    
    assert Account.get_net_transfer(debit_accounts, credit_accounts) == 300

    # One transaction going the other way should reduce total
    JournalEntry(datetime.now(), credit_accounts[0], debit_accounts[0], 100)
    assert Account.get_net_transfer(debit_accounts, credit_accounts) == 200

    # Transactions made to outside accounts should have no effect
    new_acc = Account('t', '01-02-100', AccountType.CREDIT, template=template)

    for x in range(100):  
        JournalEntry(datetime.now(), debit_accounts[x%len(debit_accounts)],
                     new_acc, 100)
        JournalEntry(datetime.now(), credit_accounts[x%len(credit_accounts)],
                     new_acc, 100)
        JournalEntry(datetime.now(), new_acc,
                     debit_accounts[x%len(debit_accounts)], 100)
        JournalEntry(datetime.now(), new_acc,
                     credit_accounts[x%len(credit_accounts)], 100)
    assert Account.get_net_transfer(debit_accounts, credit_accounts) == 200


    # Test that adding start and end dates functions properly.
    acc1 = Account('a', '01-02-100', AccountType.CREDIT, template=template)
    acc2 = Account('b', '01-02-101', AccountType.DEBIT, template=template)

    # Add one transaction a year ago and one from 10 years ago
    now = datetime.now()
    one_year_ago = datetime(now.year-1 , now.month, now.day)
    ten_years_ago = datetime(now.year-10 , now.month, now.day)
    JournalEntry(date=one_year_ago, acc_credit=acc1, acc_debit=acc2,
                 amount=1000)
    JournalEntry(date=ten_years_ago, acc_credit=acc1, acc_debit=acc2,
                 amount=2000)
    
    assert Account.get_net_transfer(debit_accounts=[acc2],
                                    credit_accounts=[acc1]) == 3000
    
    assert Account.get_net_transfer(debit_accounts=[acc2],
                                    credit_accounts=[acc1],
                                    start_date=one_year_ago) == 1000
    
    assert Account.get_net_transfer(debit_accounts=[acc2],
                                    credit_accounts=[acc1],
                                    start_date=datetime(now.year-3, now.month, now.day)) == 1000
    
    assert Account.get_net_transfer(debit_accounts=[acc2],
                                    credit_accounts=[acc1],
                                    start_date=datetime(now.year-11, now.month, now.day),
                                    end_date=datetime(now.year-5, now.month, now.day)) == 2000
    
    assert Account.get_net_transfer(debit_accounts=[acc2],
                                    credit_accounts=[acc1],
                                    end_date=datetime(now.year-5, now.month, now.day)) == 2000
    
    assert Account.get_net_transfer(debit_accounts=[acc2],
                                    credit_accounts=[acc1],
                                    start_date=now) == 0
    
    # Test that we are able to filter based on memos
    JournalEntry(datetime.now(), acc_debit=acc1, acc_credit=acc2, amount=100,
                 memo='Interest payment')

    assert Account.get_net_transfer(debit_accounts=[acc1],
                                    credit_accounts=[acc2],
                                    memo=re.compile('')) == -2900
    
    assert Account.get_net_transfer(debit_accounts=[acc1],
                                    credit_accounts=[acc2],
                                    memo=re.compile('Interest')) == 100

