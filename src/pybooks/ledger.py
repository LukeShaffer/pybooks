'''
The ledger is where everything starts.  A general container class used
to encapsulate the various accounts tied together in the overall ledger.

Also contains helper methods to print and export the ledger as well.
'''
import re

from pybooks.util import DuplicateException, NullAccountTemplateError, \
    InvalidAccountNumberException
from pybooks.enums import AccountingMethods
from pybooks.account import ChartOfAccounts, Account


class _Ledger:
    '''
    A base parent class detailing common ledger methods for General and Sub
    Ledgers
    '''
    def __init__(self, name:str, accounting_method=AccountingMethods.CASH):
        # The human readable name of the General Ledger
        self.name = name

        # A general purpose dict that contains all accounts contained in
        # this ledger as well as any and all subledgers
        self.chart_of_accounts = ChartOfAccounts()
        
        # The accounts that comprise this ledger that are not part of any
        # identified subledger, not a complete list
        self.accounts = {}

        # These are for information and do not currently control behavior
        # Cash or Accrual
        self.accounting_method = accounting_method

    def view(self) -> None:
        '''
        Print a visual representation of the ledger
        TODO
        '''
        raise NotImplementedError()


    def add_account(self, account):
        if not isinstance(account, Account):
            raise TypeError('Account must be of type pybooks.account.Account')

        # This test must come first as it is more permissive
        if account in self.chart_of_accounts:
            if account != self.chart_of_accounts[account.number]:
                raise DuplicateException('Trying to add a new account with a '
                                         f'duplicate number: {account.number}')
        
        if account.number in self.accounts:
            raise DuplicateException(
                f'Account {account.number} already exists in this ledger.')
        
        self.accounts[account.number] = account
        self.chart_of_accounts[account.number] = account

    def filter_accounts(self, match_all=True, fuzzy_match=True, **kwargs) \
            -> [Account]:
        '''
        An attempt to make a django-like account search and filter system for
        Ledgers to filter their respective accounts based on account codes.

        The accounts are filtered via the named segments based in to the
        AccountNumberTemplate used to initialize the Account.

        `match_all`: toggles AND or OR behavior for the given filters
        `fuzzy_match`: toggles "fuzzy matching" of the given filters where
            most values will be converted to strings and case will be ignored

        Ie. for account numbers XX-XX-XXX where the last 3 digits were given
        the name 'Account Code' in the AccountNumberTemplate constructor, call
        this function as such:

        ledger.filter_accounts(account_code='121')
        '''
        to_return = []
        if not kwargs:
            return to_return

        for account in self.chart_of_accounts.values():
            matches_all = True
            for arg, value in kwargs.items():
                # All possible values we want to allow the user to filter on
                search_dict = {
                    # All the named section from this account's number
                    **account._account_number._dict,
                    'name': account.name
                }
                
                for term in search_dict:
                    flag = re.IGNORECASE
                    # Iterate over every user given filter
                    if re.match(f'^{arg}$', term.replace(' ', '_'), flag):
                        term_matches_filter = False
                        # fuzzy_match means ignore case and type differences
                        if fuzzy_match:
                            if re.match(f'^{value}$', search_dict[term], flag):
                                term_matches_filter = True
                        elif search_dict[term] == value:
                            term_matches_filter = True
                        
                        if term_matches_filter:
                            # If OR behavior is specified, add the account to
                            # the output
                            if not match_all:
                                to_return.append(account)
                        else:
                            matches_all = False

                # If it doesn't match here skip rest of args to save time
                if match_all and not matches_all:
                    break

            if matches_all:
                to_return.append(account)

        return to_return

    def get_account(self, **kwargs) -> Account|None:
        '''
        Single result extension of filter_accounts() that will throw an error
        if more than one item matches
        '''
        result = self.filter_accounts(**kwargs)
        if len(result) > 1:
            raise ValueError('More than 1 Account returned for get_account()')
        
        if not result:
            return None
        return result[0]

class GeneralLedger(_Ledger):
    '''
    The top-level master ledger for an entity, composed of other subledgers
    or accounts
    '''
    def __init__(self, name, account_number_template=None, **kwargs):
        super().__init__(name, *kwargs)
        self.subledgers = set()
        # The AccountNumberTemplate that all child accounts must follow
        self.account_number_template = account_number_template 
    
    def _make_subledger_name(self, name):
        return f'{self.name}__{name}'
    
    def add_subledger(self, name=None, subledger=None):
        if subledger is None and name is None:
            raise TypeError('Subledger must be added via object or name!')
        
        if subledger is None:
            subledger = SubLedger(
                self._make_subledger_name(name),
                general_ledger=self
            )
        else:
            if subledger in self.subledgers:
                raise DuplicateException(f'Subledger {subledger} already exists')
        
        # Make sure links are correct
        subledger.general_ledger = self
        self.subledgers.add(subledger)
        self.chart_of_accounts.update(subledger.chart_of_accounts)

class SubLedger(_Ledger):
    '''
    A sub ledger with a collection of accounts.
    Must have a general ledger to which it is attached.
    '''
    def __init__(self, name, general_ledger=None, **kwargs):
        self.general_ledger = general_ledger
        # Account number templates can only live on GeneralLedger instances
        if 'account_number_template' in kwargs:
            raise ValueError('account_number_template can only be defined on '
                'GeneralLedger instances')

        super().__init__(name, *kwargs)

    @property
    def account_number_template(self):
        if self.general_ledger is None:
            return None
        return self.general_ledger.account_number_template


    

