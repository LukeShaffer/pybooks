'''
'''
from collections import defaultdict
from datetime import datetime

from pybooks.util import parse_date

class Journal:
    def __init__(self, currency_symbol='$'):
        # A dictionary from dates to a list of entries on that date
        # The combined date+index will mark the journal ID for the transaction
        self._entries = defaultdict(list)
        self.num_entries = 0
        self.accounts = set()

        self._currency = currency_symbol
    
    def print_journal(self, date_format='%B %d, %Y',tab_len=4):
        '''
        Iterate through all stored transactions and print them into a table
        for inspection.

        TODO Add support for compound journal entries
        '''

        # dictionaries keys are unordered
        dates = sorted(self._entries)

        cols = ('Date', 'Account', 'Debit', 'Credit')
        longest = [0] * len(cols)

        # Get the longest values for each column
        for date, entry_list in self._entries.items():
            longest[0] = max(
                longest[0],
                len(datetime.strftime(date, date_format))
            )
            # max will return the JournalEntry object
            longest[1] = max(
                longest[1],
                len(
                    max(entry_list, key=lambda x: x.acc_debit.name)
                    .acc_debit.name
                ),
                    # Credits are indented
                    tab_len + len(
                        max(entry_list, key=lambda x: x.acc_credit.name)
                        .acc_credit.name
                    )
                )
            longest[2] = max(
                longest[2],
                len('{}{:,}'.format(
                    self._currency,
                    max(entry_list, key=lambda x: x.amount).amount)
                )
            )

            longest[3] = longest[2]

        lc = longest
        tab = ' ' * tab_len
        title_row = (
            '{0:<{lc[0]}}{tab}'
            '{1:<{lc[1]}}{tab}'
            '{2:<{lc[2]}}{tab}'
            '{3:<{lc[3]}}'
            .format(*cols, tab=tab,lc=lc)
        ).strip()

        print(title_row)
        print('=' * len(title_row))
        sorted_dates = sorted(self._entries.keys())

        for date in sorted_dates:
            for entry in self._entries[date]:
                # Print the debit account, and then the credit account
                print(
                    '{0:<{lc[0]}}{tab}'
                    '{1:<{lc[1]}}{tab}'
                    '{curr}{2:<{lc[2]},}{tab}'
                    '{3:<{lc[3]}}'
                    .format(
                        datetime.strftime(entry.date, date_format),
                        entry.acc_debit.name,
                        entry.amount,
                        '',
                        lc=lc,
                        tab=tab,
                        curr=self._currency
                    )
                    .strip()
                )
                # Indent the credited account
                print(
                    '{0:<{lc[0]}}{tab}'
                    '{1:<{lc[1]}}{tab}'
                    '{2:<{lc[2]}}{tab}'
                    '{curr}{3:<{lc[3]},}'
                    .format(
                        '',
                        tab + entry.acc_credit.name,
                        '',
                        entry.amount,
                        lc=lc,
                        tab=tab,
                        curr=self._currency
                    )
                    .rstrip()  # Indented with spaces on the left
                )
                print('-' * len(title_row))

    
    def add_entry(self, entry):
        if not isinstance(entry, JournalEntry):
            raise TypeError('Entry must be a JournalEntry')
        self._entries[entry.date].append(entry)
        self.num_entries += 1

        # Link all of the entries together
        for account in (entry.acc_credit, entry.acc_debit):
            self.accounts.add(account)
            account.journals.add(self)



class JournalEntry:
    '''
    Each individual journal entry in the journal will be its own instance.

    The credit and debit accounts will be account instances that can be queried
    for more information

    Following the layout in a T account, debits are on the left, and credits
    are on the right
    '''
    def __init__(self, date, acc_debit, acc_credit, amount, memo=''):
        self.date = parse_date(date)
        self.acc_debit = acc_debit
        self.acc_credit = acc_credit
        self.amount = amount
        self.memo = memo
