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
from pybooks.account import ChartOfAccounts, Account, AccountNumberTemplate,\
    _AccountNumber

# Control vars for the filter_accounts() method
FILTER_TOKEN = '__'
DEFINED_FILTERS = (
    'eq',
    'in',
    'lt', 'lte',
    'gt', 'gte',
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

    @property
    def template() -> AccountNumberTemplate:
        raise NotImplementedError('Base class should not be called like this')

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

        The `account` parameter is either an Account instance or the name of
        a new account to be created.
        '''
        # If there is a name conflict, this will error out
        account = self.chart_of_accounts.add_account(account, number,
                                                     account_type)
        if account.number in self.accounts:
            raise DuplicateException('Account already exists in this ledger.')
        self.accounts[account.number] = account

    def get_new_account(self, name:str, account_type:AccountType,
                        initial_balance:float=0, **kwargs) -> Account:
        '''
        A handy utility function that allows the creation of dynamic account
        numbers through the use of templates with incrementable fields.

        Creates a new account

        The kwargs to pass to this function are the same as to
        AccountNumberTemplate._make_account_number() (the names of the segments
        as well as the values for them) and will vary per template.
        '''
        # Find if the ledger's template supports incrementing
        if self.template._increment_segment is None:
            raise ValueError("This ledger's template does not support "
                             "incrementing account numbers")
        
        # Find the first open index in the incrementable segment
        inc_seg = self.template._increment_segment
        max_val = int(list(inc_seg.meanings.keys())[0].pattern.replace('\\d', '9'))
        existing_accounts = self.filter_accounts(**kwargs)

        # This assumes that every auto increment account will contain a '\d'
        if len(existing_accounts) > max_val:
            raise OverflowError('Cannot increment AccountSegment any further') 

        # Set this up for the loop
        existing_accounts = iter(existing_accounts)
        current_index = 0
        while current_index <= max_val:
            try:
                next_account = next(existing_accounts)
            except StopIteration:
                # 0 existing accounts, or we have reached the end of the
                # existing accounts
                break
            
            current_try = f'{current_index:0{inc_seg.length}}'
            if next_account._account_number[inc_seg.name] == current_try:
                current_index += 1
                continue
            break

        kwargs[inc_seg.name] = f'{current_index:0{inc_seg.length}}'
        acc_num = self.template._make_account_number(**kwargs)

        # print(f'Success, found empty account number: {acc_num.number}')
        # Create the new account, add it and return it
        new_acc = Account(name=name, number=acc_num, account_type=account_type,
                          initial_balance=initial_balance,
                          template=self.template)
        
        self.add_account(new_acc)
        return new_acc


    def _keys_match(self, acc_key, user_key):
        '''
        Need to separate the comparing of keys (eg, "name") from their values
        for the filter function.

        This function will match exact keys as well as Django-ified
        under_replacements.

        Eg, for the key "Company Code", either "Company Code" or "company_code"
        will return True.
        '''
        if FILTER_TOKEN in user_key:
            # Not even worrying about multiple
            user_key = user_key.split(FILTER_TOKEN)[0]

        flag = re.IGNORECASE
        # Convert to Boolean for debug statements
        keys_match = bool(re.match(f"^{acc_key.replace(' ', '_')}$", user_key,
                                   flag))
        
        # Need to expand this to include a direct non-transformed matching input
        keys_match_exact = bool(re.match(f'^{acc_key}$', user_key, flag))

        # print(f'Comparing acc_key {acc_key} and user_key {user_key}...{keys_match}')
        return keys_match or keys_match_exact

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
        
        # Begin specifying any of the __dunder filters I will handle
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
        elif user_filter == 'lt':
            return int(account_val) < int(user_val)
        elif user_filter == 'lte':
            return int(account_val) <= int(user_val)
        elif user_filter == 'gt':
            return int(account_val) > int(user_val)
        elif user_filter == 'gte':
            return int(account_val) >= int(user_val)
        
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

        DEBUG = False

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

            DEBUG and print('search_dict: ', search_dict)

            # Keep track of AND or OR behavior
            num_user_keys_matched = 0

            DEBUG and print('\nsearching new account...')
            for user_key, user_value in kwargs.items():
                DEBUG and print(f'\tcomparing user key: {user_key} ({user_value})')
                for acc_key, acc_value in search_dict.items():
                    DEBUG and print('acc_key, acc_value: ', acc_key, acc_value)
                    # Go ahead to compare key values
                    if self._keys_match(acc_key, user_key):
                        # Not just a simple equality check, also does filters
                        term_matches_filter = self._term_matches_filter(
                            acc_value, user_key, user_value, fuzzy_match
                        )
                        DEBUG and print(f'\t\t...to acc key {acc_key} ({acc_value})...', end='')
                        DEBUG and print(term_matches_filter)
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

        DEBUG and print('filter_accounts return...', to_return)
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

    def get_net_balance(self, reporting_format, accounts=[], match_all=True,
                        fuzzy_match=True, **kwargs) -> float:
        '''
        A function to aggregate the net balances for any subset of the
        accounts contained by this ledger or its subledgers.

        For any specific subset of the accounts under this ledger, aggregate
        their credits and debits and report the final amount in terms of
        net credits or debits

        The reporting_format controls which side of the balance sheet will be
        considered the positive one in terms of the net balance.

        For example, if someone owes $100,000 and owns $100, the net balance
        is a $99,900 credit (liability).
            If we report as a CREDIT, we will return positive $99,900
            If we report as a DEBIT, we will return negative ($99,900)

        reporting_format is either one of "AccountType.CREDIT" or
            "AccountType.DEBIT"
        '''
        if not accounts:
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


    

