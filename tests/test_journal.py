from datetime import datetime
from textwrap import dedent

from pybooks.journal import Journal, JournalEntry
from pybooks.account import Account

def test_init():
    j = Journal()

def test_add_entries():
    j = Journal()

    acc_credit = Account('Creditor')
    acc_debit = Account('Debtor')

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

    acc_credit = Account('Creditor')
    acc_debit = Account('Debtor')

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

    