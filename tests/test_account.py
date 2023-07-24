from datetime import datetime


from pybooks.account import Account
from pybooks.journal import Journal, JournalEntry

def test_init():
    acc = Account('Cash - BMO')


def test_add_journal():
    j = Journal()

    acc_credit = Account('Creditor')
    acc_debit = Account('Debtor')

    now = datetime(2023, 7, 23)
    for _ in range(3):
        je = JournalEntry(now, acc_debit, acc_credit, 100)
        j.add_entry(je)
    
    assert acc_credit.journals == set([j])
    assert acc_debit.journals == set([j])