'''
Provides functionality for accounting Accounts
'''

class ChartOfAccounts:
    '''
    A structure that holds a set of related accounts and related formatting
    functions
    '''
    def __init__(self):
        self.accounts = {}
        raise NotImplementedError()
    
    def print_table(self):
        '''
        Prints a visual representation of the accounts contained, listed in
        the following order:

        Balance Sheet Accounts
            - Assets
            - Liabilities
            - Owners' Equity
        
        Income Statement Accoutns
            - Operating Revenues
            - Operating Expenses
            - Non-Operating Revenues and Gains
            - Non-Operating Expenses and Losses
        '''
        raise NotImplementedError()


class Account:
    def __init__(self, name, initial_balance=0):
        self.name = name
        # A set of Journal instances used to populate the Account's balance
        self.journals = set()

    def __str__(self):
        return self.name

    @property
    def net_credit(self):
        total = 0
        for journal in self.journals:
            for entry in journal._entries:
                if entry.acc_credit == self:
                    total += entry.amount
        return total
    
    @property
    def net_debit(self):
        total = 0
        for journal in self.journals:
            for entry in journal._entries:
                if entry.acc_debit == self:
                    total += entry.amount
        return total

    def print_t_account(self):
        '''
        Construct and print the T account for this account as a formatted
        table
        '''
        raise NotImplementedError()
