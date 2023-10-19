'''
The ledger is where everything starts.  A general container class used
to encapsulate the various accounts tied together in the overall ledger.

Also contains helper methods to print and export the ledger as well.
'''
from __future__ import annotations # list type annotations

import re
from typing import Union  # Multiple type annotation

from pybooks.util import DuplicateException
from pybooks.enums import AccountingMethods, AccountType
from pybooks.account import ChartOfAccounts, Account, AccountNumberTemplate

# Control vars for the filter_accounts() method
FILTER_TOKEN = '__'
DEFINED_FILTERS = (
    'eq',
    'in'
)


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


    def add_account(self, account:Union[Account,str], number:str=None,
                    account_type:AccountType=None):
        '''
        Add a new account to this ledger, either as a pre-existing Account
        instance or creating a new one from the raw details and the account
        number template associated with this ledger.
        '''
        # If there is a name conflict, this will error out
        account = self.chart_of_accounts.add_account(account, number,
                                                     account_type)
        if account.number in self.accounts:
            raise DuplicateException('Account already exists in this ledger.')
        self.accounts[account.number] = account


    def _keys_match(self, acc_key, user_key):
        '''
        Need to separate the comparing of keys (eg, "name") from their values
        for the filter function
        '''
        if FILTER_TOKEN in user_key:
            # Not even worrying about multiple
            user_key = user_key.split(FILTER_TOKEN)[0]

        flag = re.IGNORECASE
        # Convert to Boolean for debug statements
        keys_match = bool(re.match(f"^{acc_key.replace(' ', '_')}$", user_key,
                                   flag))
        # print(f'Comparing acc_key {acc_key} and user_key {user_key}...{keys_match}')
        return keys_match

    def _term_matches_filter(self, account_val, user_key, user_val,
                             fuzzy_match=True):
        '''
        Implement the logic of the kw__contains filters for the filter_accounts
        method for the various filters I choose to implement.
        '''

        # Default to equality if none specified
        user_filter = 'eq'

        if FILTER_TOKEN in user_key:
            user_key, user_filter = user_key.split(FILTER_TOKEN)

        if user_filter not in DEFINED_FILTERS:
            raise ValueError('User specified a nonexistant filter '
                                f'operation: {user_filter}')
        
        # print(type(user_key), user_val)
        # print(type(account_val), account_val)
        # print(user_val == account_val)
        
        # Save space
        re_flag = re.IGNORECASE
        if user_filter == 'eq':
            # fuzzy_match means ignore case and type differences
            if fuzzy_match:
                if re.match(f'^{user_val}$', str(account_val), re_flag):
                    return True
            elif account_val == user_val:
                return True
        # The value must be an iterable
        elif user_filter == 'in':
            for val in user_val:
                if fuzzy_match and re.match(f'^{val}$', str(account_val), re_flag):
                    return True
                elif val == account_val:
                    return True
        
        # Default return False
        return False

    def filter_accounts(self, match_all=True, fuzzy_match=True, **kwargs) \
            -> list[Account]:
        '''
        An attempt to make a django-like account search and filter system for
        Ledgers to filter their respective accounts based on account codes.

        The accounts are filtered via the named segments based in to the
        AccountNumberTemplate used to initialize the Account.

        New addition, adding __in designations like Django queryset filters

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
            return []

        for account in self.chart_of_accounts.values():
            # All possible values we want to allow the user to filter on
            search_dict = {
                # All the named sections from this account's number
                **account._account_number._dict,
                'name': account.name
            }

            # Keep track of AND or OR behavior
            num_user_keys_matched = 0

            print('searching new account...')
            for user_key, user_value in kwargs.items():
                print(f'\tcomparing user key: {user_key} ({user_value})')
                for acc_key, acc_value in search_dict.items():
                    # Goahead to compare key values
                    if self._keys_match(acc_key, user_key):
                        # Not just a simple equality check, also does filters
                        term_matches_filter = self._term_matches_filter(
                            acc_value, user_key, user_value, fuzzy_match
                        )
                        print(f'\t\t...to acc key {acc_key} ({acc_value})...', end='')
                        print(term_matches_filter)
                        if term_matches_filter:
                            num_user_keys_matched += 1
                            # OR short-circuit
                            if not match_all:
                                to_return.append(account)

                        # No point in hitting the other keys, we found the
                        # match for this user input
                        break

            # Only add the AND if OR behavior not specified - will already be
            # added
            if match_all and num_user_keys_matched == len(kwargs.items()):
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

    def get_net_balance(self, reporting_format, match_all=True,
                        fuzzy_match=True, **kwargs)->int:
        '''
        A function to aggregate the net balances for any subset of the
        accounts contained by this ledger or its subledgers.

        For any specific subset of the accounts under this ledger, aggregate
        their credits and debits and report the final amount in terms of
        net credits or debits

        The reporting format controls which side of the balance sheet will be
        considered the positive one in terms of the net balance.

        For example, if someone owes $100,000 and owns $100, the net balance
        is a $99,900 credit (liability).
            If we report as a CREDIT, we will return positive $99,900
            If we report as a DEBIT, we will return negative ($99,900)

        reporting_format is either one of "AccountType.CREDIT" or
            "AccountType.DEBIT"
        '''
        accounts = self.filter_accounts(match_all, fuzzy_match, **kwargs)
        
        # This could either be 0 or raise an error.  I'll just return 0 for now
        if not accounts:
            return 0

        net_balance = 0


        # The net_balance property does the logic of parsing whether
        for account in accounts:
            if account.account_type == reporting_format:
                net_balance += account.net_balance
            else:
                net_balance -= account.net_balance

        return net_balance
            

class GeneralLedger(_Ledger):
    '''
    The top-level master ledger for an entity, composed of other subledgers
    or accounts
    '''
    def __init__(self, name:str, account_number_template:AccountNumberTemplate,
                 **kwargs):
        super().__init__(name, *kwargs)
        self.subledgers = set()

        # The AccountNumberTemplate that all child accounts must follow
        self.chart_of_accounts.template = account_number_template 
    
    @property
    def template(self):
        return self.chart_of_accounts.template
    def _make_subledger_name(self, name:str):
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
    def __init__(self, name, general_ledger:GeneralLedger=None, **kwargs):
        # Account number templates can only live on GeneralLedger instances
        if 'account_number_template' in kwargs:
            raise ValueError('account_number_template can only be defined on '
                'GeneralLedger instances')

        super().__init__(name, *kwargs)
        general_ledger.add_subledger(subledger=self)
        self.general_ledger = general_ledger
        

    @property
    def template(self):
        if self.general_ledger is None:
            return None
        return self.general_ledger.account_number_template


    

