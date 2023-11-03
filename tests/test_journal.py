from datetime import datetime
from textwrap import dedent
import re
from copy import deepcopy

import pytest

from pybooks.journal import Journal, JournalEntry, split_wages
from pybooks.account import Account
from pybooks.enums import AccountType
from pybooks.util import normal_round, truncate

from util import init_template


def test_init():
    j = Journal()
    init_template()

def test_add_entries():
    j = Journal()
    template = init_template()

    acc_credit = Account('Creditor', '01-00-100', AccountType.CREDIT,
                         template=template)
    acc_debit = Account('Debtor', '01-00-300', AccountType.DEBIT,
                        template=template)

    now = datetime(2023, 7, 23)
    for _ in range(3):
        je = JournalEntry(now, acc_debit, acc_credit, 500)
        j.add_entry(je)
    
    assert j._entries[now][0].amount == 500
    assert j._entries[now][2].date == now
    assert j._entries[now][1].acc_credit == acc_credit

    # There is only one date
    assert len(j._entries) == 1
    assert j.num_entries == 3

    next_day = datetime(2023, 7, 24)
    for _ in range(3):
        je = JournalEntry(next_day, acc_debit, acc_credit, 200)
        j.add_entry(je)
    
    assert len(j._entries) == 2
    assert j.num_entries == 6

    # A journal entry that doesn't get posted to a journal will still affect
    # account totals
    assert acc_credit.gross_credit == 2100
    assert acc_debit.gross_debit == 2100
    je = JournalEntry(next_day, acc_debit, acc_credit, 200)
    assert acc_credit.gross_credit == 2300
    assert acc_debit.gross_debit == 2300

def test_print_journal(capsys):
    j = Journal()
    template = init_template()

    acc_credit = Account('Creditor', '01-00-100', AccountType.CREDIT,
                         template=template)
    acc_debit = Account('Debtor', '01-00-200', AccountType.DEBIT,
                        template=template)

    now = datetime(2023, 7, 23)
    for _ in range(3):
        je = JournalEntry(now, acc_debit, acc_credit, 5000)
        j.add_entry(je)
    
    j.print_journal()
    out, err = capsys.readouterr()

    assert out == dedent('''\
        Date             Account         Debit     Credit
        =================================================
        July 23, 2023    Debtor          $5,000
                             Creditor              $5,000
        -------------------------------------------------
        July 23, 2023    Debtor          $5,000
                             Creditor              $5,000
        -------------------------------------------------
        July 23, 2023    Debtor          $5,000
                             Creditor              $5,000
        -------------------------------------------------
        ''')
    
    # Out of order journal entries will show chronologically
    j.add_entry(JournalEntry(datetime(2023, 1, 23), acc_debit, acc_credit, 10))
    j.add_entry(JournalEntry(datetime(2023, 12, 23), acc_debit, acc_credit, 1))
    j.print_journal()
    
    out, err = capsys.readouterr()

    assert out == dedent('''\
        Date                 Account         Debit     Credit
        =====================================================
        January 23, 2023     Debtor          $10
                                 Creditor              $10
        -----------------------------------------------------
        July 23, 2023        Debtor          $5,000
                                 Creditor              $5,000
        -----------------------------------------------------
        July 23, 2023        Debtor          $5,000
                                 Creditor              $5,000
        -----------------------------------------------------
        July 23, 2023        Debtor          $5,000
                                 Creditor              $5,000
        -----------------------------------------------------
        December 23, 2023    Debtor          $1
                                 Creditor              $1
        -----------------------------------------------------
        ''')

    # New addition, test printing with account numbers
    j.print_journal(use_acc_numbers=True, use_acc_names=False)
    out, err = capsys.readouterr()
    assert out == dedent('''\
    Date                 Account          Debit     Credit
    ======================================================
    January 23, 2023     01-00-200        $10
                             01-00-100              $10
    ------------------------------------------------------
    July 23, 2023        01-00-200        $5,000
                             01-00-100              $5,000
    ------------------------------------------------------
    July 23, 2023        01-00-200        $5,000
                             01-00-100              $5,000
    ------------------------------------------------------
    July 23, 2023        01-00-200        $5,000
                             01-00-100              $5,000
    ------------------------------------------------------
    December 23, 2023    01-00-200        $1
                             01-00-100              $1
    ------------------------------------------------------
    ''')


    j.print_journal(use_acc_numbers=True, use_acc_names=True)
    out, err = capsys.readouterr()
    assert out == dedent('''\
    Date                 Account                   Debit     Credit
    ===============================================================
    January 23, 2023     01-00-200 Debtor          $10
                             01-00-100 Creditor              $10
    ---------------------------------------------------------------
    July 23, 2023        01-00-200 Debtor          $5,000
                             01-00-100 Creditor              $5,000
    ---------------------------------------------------------------
    July 23, 2023        01-00-200 Debtor          $5,000
                             01-00-100 Creditor              $5,000
    ---------------------------------------------------------------
    July 23, 2023        01-00-200 Debtor          $5,000
                             01-00-100 Creditor              $5,000
    ---------------------------------------------------------------
    December 23, 2023    01-00-200 Debtor          $1
                             01-00-100 Creditor              $1
    ---------------------------------------------------------------
    ''')
    

def test_print_journal_with_memo(capsys):
    # TODO
    pass

def test_wage_split():
    '''
    Test that I am able to faithfully split wages from a preset rule book
    '''
    template = init_template()

    job_acc = Account('Company Pay', number='01-00-100',
                      account_type=AccountType.CREDIT, template=template)
    
    gross_wages = Account('Gross Wages', number='10-00-100',
                          account_type=AccountType.DEBIT, template=template)
    ret_acc = Account('401k', number='10-00-101',
                      account_type=AccountType.DEBIT, template=template)
    fed_acc = Account('FICA', number='02-00-100', account_type=AccountType.DEBIT,
                     template=template)

    roth_acc = Account('Roth 401k', number='10-00-102',
                       account_type=AccountType.DEBIT, template=template)

    wages = 100

    # Test initializing with an empty ruleset
    wage_rules = {}
    with pytest.raises(KeyError):
        result = split_wages(wages, wage_rules)

    # Rounding is disabled
    # Basic rules start with no deferrals and no taxes
    wage_rules = {
        'acc_credit': job_acc,
        'acc_debit': gross_wages,
        'memo': 'Gross Wages from Company',
        
        'ADDITIONAL_WAGES': [],
        'PRE_TAX_DEDUCTIONS': [],
        'TAXES': [],
        'POST_TAX_DEDUCTIONS': []
    }

    result = split_wages(wages, wage_rules)


    assert len(result) == 1
    assert result[0].acc_credit == job_acc
    assert result[0].acc_debit == gross_wages
    assert result[0].amount == wages

    # Add a bonus / vacation
    wage_rules['ADDITIONAL_WAGES'] = [
        {
            'acc_credit': job_acc,
            'acc_debit': gross_wages,
            'amount': '10%',
            'memo': 'bonus'
        },
        {
            'acc_credit': job_acc,
            'acc_debit': gross_wages,
            'amount': 100,
            'memo': 'Vacation Pay'
        }
    ]
    # 100 + 10% + 100

    result = split_wages(wages, wage_rules)
    assert len(result) == 3
    assert result[0].amount == 100
    assert result[1].amount == 10
    assert result[2].amount == 100

    # Total wages at this point = 210

    # Add pre-tax deductions
    wage_rules['PRE_TAX_DEDUCTIONS'] = [
        {
            'acc_credit': gross_wages,
            'acc_debit': fed_acc,
            'amount': 25,
            'memo': 'Insurance'
        },
        {
            'acc_credit': gross_wages,
            'acc_debit': ret_acc,
            'amount': '7.5%',
            'memo': 'Retirement Contribution'
        }
    ]
    result = split_wages(wages, wage_rules)
    assert len(result) == 5
    assert result[3].amount == 25
    assert result[4].amount == 210 * 0.075

    # Test that pre-tax deductions totalling more than the original wages
    # throws error
    error_wage_rules = deepcopy(wage_rules)
    error_wage_rules['PRE_TAX_DEDUCTIONS'].append(
        {
            'acc_credit': job_acc,
            'acc_debit': ret_acc,
            'amount': wages + 500,
            'memo': 'Too much deduction'
        }
    )
    with pytest.raises(ValueError):
        split_wages(wages,error_wage_rules)
    
    # Add tax section
    # Current balance: 169.25
    wage_rules['TAXES'] = [
        {
            'acc_credit': gross_wages,
            'acc_debit': fed_acc,
            'amount': '15%',
            'memo': 'Federal Income Tax',
            'round_up': False
        },
        {
            'acc_credit': gross_wages,
            'acc_debit': fed_acc,
            'amount': '3%',
            'memo': 'State Income Tax'
        }
    ]
    result = split_wages(wages, wage_rules)
    assert len(result) == 7
    assert result[5].amount == 169.25 * 0.15
    assert result[6].amount == 169.25 * 0.03

    # Check that taxes exceeding the initial wages throws an error
    error_wage_rules['TAXES'].append(
        {
            'acc_credit': gross_wages,
            'acc_debit': fed_acc,
            'amount': wages + 500,
            'memo': 'Bad Taxes'
        }
    )
    with pytest.raises(ValueError):
        split_wages(wages, error_wage_rules)

    # Post-tax deductions
    # Current amount == 138.785
    wage_rules['POST_TAX_DEDUCTIONS'] = [
        {
            'acc_credit': gross_wages,
            'acc_debit': roth_acc,
            'amount': '5%',
            'memo': 'Roth Contributions'
        },
        {
            'acc_credit': gross_wages,
            'acc_debit': roth_acc,
            'amount': '15%',
            'memo': '2nd Roth Contribution',
            'round_up': False
        }
    ]

    result = split_wages(wages, wage_rules)
    assert len(result) == 9
    assert result[7].amount == 138.785 * 0.05
    assert result[8].amount == 138.785 * 0.15

    error_wage_rules = deepcopy(wage_rules)
    error_wage_rules['POST_TAX_DEDUCTIONS'] = [
        {
            'acc_credit': gross_wages,
            'acc_debit': roth_acc,
            'amount': wages + 100,
            'memo': 'Too Large'
        }
    ]

    with pytest.raises(ValueError):
        split_wages(wages, error_wage_rules)
    

    # Now test that rounding is implemented properly
    wage_rules['round'] = True

    result = split_wages(wages, wage_rules)
    assert result[7].amount == round(138.79 * 0.05, 2)
    assert result[8].amount == round(138.79 * 0.15, 2)

    wage_rules['round_method'] = 'Truncate'
    result = split_wages(wages, wage_rules)
    # 138.8 * 0.05 results in 6.940000000000001
    assert result[7].amount == truncate(138.8 * 0.05, 2)
    assert result[8].amount == 138.8 * 0.15