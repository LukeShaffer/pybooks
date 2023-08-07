from datetime import datetime
from textwrap import dedent
import re

from pybooks.journal import Journal, JournalEntry
from pybooks.account import Account, AccountNumberTemplate, AccountNumberSegment
from pybooks.enums import AccountType


def init_template():
    seg1_vals = {
        f'{key:02}': val
        for key, val in [(_, f'cmpny{_}') for _ in range(1, 4)]
    }

    seg2_vals = {
        f'{key:02}': val
        for key, val in [(_, f'dpt{_}') for _ in range(3)]
    }

    seg1 = AccountNumberSegment(seg1_vals)
    seg2 = AccountNumberSegment(seg2_vals)

    seg3 = [
        AccountNumberSegment(
            re.compile(r'\d{4}'), length=3, flat_value='Account Name'),
    ]

    template = AccountNumberTemplate((
        ('Division Code', seg1),
        ('Department Code', seg2),
        ('Account Code', *seg3)
    ))
    return template

def test_init():
    j = Journal()
    init_template()

def test_add_entries():
    j = Journal()
    template = init_template()

    acc_credit = Account('Creditor', '01-00-0000', template, AccountType.CREDIT)
    acc_debit = Account('Debtor', '01-00-0001', template, AccountType.DEBIT)

    now = datetime(2023, 7, 23)
    for _ in range(3):
        je = JournalEntry(now, acc_debit, acc_credit, 500)
        j.add_entry(je)
    
    assert j._entries[now][0].amount == 500
    assert j._entries[now][2].date == now
    assert j._entries[now][1].acc_credit == acc_credit

    assert len(j._entries) == 1
    assert j.num_entries == 3

    next_day = datetime(2023, 7, 24)
    for _ in range(3):
        je = JournalEntry(next_day, acc_debit, acc_credit, 200)
        j.add_entry(je)
    
    assert len(j._entries) == 2
    assert j.num_entries == 6

def test_print_journal(capsys):
    j = Journal()
    template = init_template()

    acc_credit = Account('Creditor', '01-00-0001', template, AccountType.CREDIT)
    acc_debit = Account('Debtor', '01-00-0002', template, AccountType.DEBIT)

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
    Date                 Account           Debit     Credit
    =======================================================
    January 23, 2023     01-00-0002        $10
                             01-00-0001              $10
    -------------------------------------------------------
    July 23, 2023        01-00-0002        $5,000
                             01-00-0001              $5,000
    -------------------------------------------------------
    July 23, 2023        01-00-0002        $5,000
                             01-00-0001              $5,000
    -------------------------------------------------------
    July 23, 2023        01-00-0002        $5,000
                             01-00-0001              $5,000
    -------------------------------------------------------
    December 23, 2023    01-00-0002        $1
                             01-00-0001              $1
    -------------------------------------------------------
    ''')


    j.print_journal(use_acc_numbers=True, use_acc_names=True)
    out, err = capsys.readouterr()
    assert out == dedent('''\
    Date                 Account                    Debit     Credit
    ================================================================
    January 23, 2023     01-00-0002 Debtor          $10
                             01-00-0001 Creditor              $10
    ----------------------------------------------------------------
    July 23, 2023        01-00-0002 Debtor          $5,000
                             01-00-0001 Creditor              $5,000
    ----------------------------------------------------------------
    July 23, 2023        01-00-0002 Debtor          $5,000
                             01-00-0001 Creditor              $5,000
    ----------------------------------------------------------------
    July 23, 2023        01-00-0002 Debtor          $5,000
                             01-00-0001 Creditor              $5,000
    ----------------------------------------------------------------
    December 23, 2023    01-00-0002 Debtor          $1
                             01-00-0001 Creditor              $1
    ----------------------------------------------------------------
    ''')
    

def test_print_journal_with_memo(capsys):
    # TODO
    pass