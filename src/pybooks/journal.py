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
    
    def print_journal(self, use_acc_numbers=False, use_acc_names=True,
            date_format='%B %d, %Y', tab_len=4):
        '''
        Iterate through all stored transactions and print them into a table
        for inspection.

        Can specify either account names, numbers or both in the table.

        If they are both specified the account number will be printed first

        TODO Add support for compound journal entries
        '''
        def get_entry_lengths(entry, use_nums, use_names):
            '''
            Util function that gets the max length of an account for the
            printed journal with the optional specified number or name format
            
            Returns a 2-tuple: debit_len, credit_len
            '''
            if not use_nums and not use_names:
                return (0, 0)

            # In multiplcation bools resolve to 0 or 1
            debit_len = len(entry.acc_debit.number) * use_nums
            debit_len += len(entry.acc_debit.name) * use_names

            credit_len = len(entry.acc_credit.number) * use_nums
            credit_len += len(entry.acc_credit.name) * use_names

            # If name and number are specified put a space between them
            if use_nums and use_names:
                debit_len += 1
                credit_len += 1

            return (debit_len, credit_len)
        
        def get_acc_col_length(entry_list, use_nums, use_names, tab_len):
            '''
            Get the overall length for the Account Column in the printed table.
            '''
            if not use_nums and not use_names:
                return 0

            to_return = 0

            for entry in entry_list:
                debit_len, credit_len = \
                    get_entry_lengths(entry, use_nums, use_names)
                
                to_return = max(to_return, debit_len, credit_len + tab_len)

            return to_return 

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
                get_acc_col_length(entry_list, use_acc_numbers, use_acc_names,
                                   tab_len)
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
                debit_name = ''
                credit_name = ''
                if use_acc_numbers:
                    debit_name += entry.acc_debit.number
                    credit_name += entry.acc_credit.number

                    # Add a space only if the name is coming after and
                    # the name is populated
                    if use_acc_names:
                        debit_name += ' '
                        credit_name += ' '
                
                if use_acc_names:
                    debit_name += entry.acc_debit.name
                    credit_name += entry.acc_credit.name

                # Print the debit account, and then the credit account
                print(
                    '{0:<{lc[0]}}{tab}'
                    '{1:<{lc[1]}}{tab}'
                    '{curr}{2:<{lc[2]},}{tab}'
                    '{3:<{lc[3]}}'
                    .format(
                        datetime.strftime(entry.date, date_format),
                        debit_name,
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
                        tab + credit_name,
                        '',
                        entry.amount,
                        lc=lc,
                        tab=tab,
                        curr=self._currency
                    )
                    .rstrip()  # Indented with spaces on the left
                )
                print('-' * len(title_row))

    def add_account(self, account):
        '''
        Add an account to this journal's collection of accounts
        '''
        self.accounts.add(account)
    
    def add_entry(self, entry):
        if not isinstance(entry, JournalEntry):
            raise TypeError('Entry must be a JournalEntry')
        self._entries[entry.date].append(entry)
        self.num_entries += 1

        # Link all of the entries together
        for account in (entry.acc_credit, entry.acc_debit):
            self.add_account(account)
            account.add_journal_entry(entry)



class JournalEntry:
    '''
    Each individual journal entry in the journal will be its own instance.

    The credit and debit accounts will be account instances that can be queried
    for more information

    Following the layout in a T account, debits are on the left, and credits
    are on the right
    '''
    def __init__(self, date, acc_debit, acc_credit, amount, memo=''):
        if None in (acc_debit, acc_credit):
            raise ValueError('Cannot create JournalEntry with a Null account!')
        if amount == 0:
            raise ValueError('Typo, you are trying to create a journal entry '
                'with no amount')

        self.date = parse_date(date)
        self.acc_debit = acc_debit
        self.acc_credit = acc_credit
        self.amount = amount
        self.memo = memo
