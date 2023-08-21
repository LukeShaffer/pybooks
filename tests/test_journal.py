from datetime import datetime
from textwrap import dedent
import re

from pybooks.journal import Journal, JournalEntry
from pybooks.account import Account, AccountNumberTemplate, AccountNumberSegment
from pybooks.enums import AccountType

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