'''
The ledger is where everything starts.  A general container class used
to encapsulate the various accounts tied together in the overall ledger.

Also contains helper methods to print and export the ledger as well.
'''
from pybooks.util import DuplicateException 
from pybooks.enums import AccountingMethods

class _Ledger:
    '''
    A base parent class detailing common ledger methods for General and Sub
    Ledgers
    '''
    def __init__(self, name, accounting_method=AccountingMethods.CASH):
        self.name = name

        # These are for information and do not currently control behavior

        # Cash or Accrual
        self.accounting_method = accounting_method

    def view(self):
        '''
        Print a visual representation of the ledger
        '''
        raise NotImplementedError()

    
class GeneralLedger(_Ledger):
    '''
    The top-level master ledger for an entity, composed of other subledgers
    or accounts
    '''
    def __init__(self, name):
        super().__init__(name)
        self.subledgers = set()
        self.accounts = set()

    def add_account(self, account):
        if account in self.accounts:
            raise DuplicateException(f'Account {account} already exists')
        self.accounts.add(account)
    
    def add_subledger(self, subledger):
        if subledger in self.subledgers:
            raise DuplicateException(f'Subledger {subledger} already exists')
        self.subledgers.add(subledger)

class SubLedger(_Ledger):
    '''
    A sub ledger with a 
    '''
    def __init__(self, name, general_ledger):
        super().__init__(name)
        self.accounts = self._contents