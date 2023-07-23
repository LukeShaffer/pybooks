'''
'''

class Journal:
    def __init__(self):
        # The index will mark the journal ID for the transaction
        self.entries = []
    
    def print_table(self, make_compound=False):
        '''
        Iterate through all stored transactions and print them into a table
        for inspection.

        Optionally condense same-day transactions to common accounts to make
        the table smaller.
        '''
        pass
    



class JournalEntry:
    '''
    Each individual journal entry in the journal will be its own instance.

    The credit and debit accounts will be account instances that can be queried
    for more information
    '''
    def __init__(self, date, acc_credit, acc_debit, amount, memo=''):
        self.date = date
        self.acc_credit = acc_credit
        self.acc_debit = acc_debit
        self.amount = amount
        self.memo = memo