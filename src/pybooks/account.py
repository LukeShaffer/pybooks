'''
Provides functionality for accounting Accounts
'''
from __future__ import annotations

import re
from datetime import datetime
from collections import OrderedDict


from pybooks.journal import JournalEntry
from pybooks.util import InvalidAccountNumberException, DuplicateException
from pybooks.enums import AccountType

class AccountNumberSegment:
    '''
    A class to wrap account number segment functionality

    These will either be initialized with a dictionary of exactly defined
    key-value pairs, or a regex and a static category value such as "Assets".
    These will function as the allowable / defined values and their meanings.

    '''

    def __init__(self, name:str, meanings:dict[str|re.Pattern, str],
                 is_regex=False, incrementable=False):
        self.name = name
        self.meanings = meanings
        self.is_regex = is_regex
        self.length = None
        # Whether this segment is unimportant / temp enough to warrant
        # strict value mappings
        self._incrementable = incrementable
        # Sanity check - incrementable fields can only be dicts with one regex
        # line to avoid a logic checking explosion
        if incrementable:
            assert is_regex and len(meanings) == 1

        # I am disallowing variable-length regexes to simplify validation
        regex_repetition_chars = '*+?'

        # Determine standard key length for this segment
        
        if is_regex:
            sample_key = next(iter(meanings)).pattern
            length = len(sample_key)

            for _ in re.findall(r'\\[a-zA-Z]', sample_key):
                length -= 1

            # Save for access later
            self.length = length

            # Validate all keys
            for regex in meanings:
                error_msg = ('Cannot have a variable length '
                    r'AccountNumberSegment (inlcudes {\d+}).')
                # re.match() only matches at the beginning
                if re.search(r'{\d+}', regex.pattern):
                    raise InvalidAccountNumberException(error_msg)
                # Search for any comma-separated repetition counts - "{1,2}"
                if re.findall(r'{\d+,\d+}', regex.pattern):
                    raise InvalidAccountNumberException(error_msg)
                for char in regex_repetition_chars:
                    if char in regex.pattern:
                        raise InvalidAccountNumberException(error_msg)
                
                # Check uniform regex length
                regex_length = len(regex.pattern)
                for _ in re.findall(r'\\[a-zA-Z]', regex.pattern):
                    regex_length -= 1
                
                if regex_length != self.length:
                    raise InvalidAccountNumberException(
                        'Variable length regex detected on Segment!')

        
        # Check for uniform meanings lengths
        elif isinstance(meanings, dict):
            first_key = next(iter(meanings))
            first_len = len(first_key)
            self.length = first_len
            if isinstance(first_key, re.Pattern):
                raise TypeError('Regex segment encountered with no is_regex '
                                'flag')
            
            if not all([len(x) == first_len for x in meanings]):
                raise ValueError('AccountNumberSegment input dict has '
                    'variable length keys')


    
    def __contains__(self, item):
        '''
        Used so we can check if a key is 'in' this Segment
        '''
        if isinstance(self.meanings, re.Pattern):
            return self.meanings.fullmatch(item)
        return item in self.meanings

    def __getitem__(self, key):
        '''
        Used to get the meaning of an account number segment.

        Throws a KeyError if the number segment is outside the defined range
        for the current segment.
        '''
        if self.is_regex:
            if len(key) == self.length:
                for regex, value in self.meanings.items():
                    if regex.match(str(key)):
                        return value
        return self.meanings[key]

class AccountNumberTemplate:
    '''
    A collection of AccountNumberSegment instances that AccountNumbers can be
    verified and interpreted against.

    The `segments` argument should be a list of tuples of the following form:

    [
        ('Division Code', AccountNumberSegment(seg1_vals)),
        ('Department Code', AccountNumberSegment(seg2_vals)),
        ('Account Code', 
            AccountNumberSegment(
                [f'{_:03}' for _ in range(100, 200)], flat_value='Assets'),
            AccountNumberSegment(
                [f'{_:03}' for _ in range(200, 300)], flat_value='Liabilities'),
            AccountNumberSegment(
                [f'{_:03}' for _ in range(300, 400)], flat_value='Equity'),
            AccountNumberSegment(
                [f'{_:03}' for _ in range(400, 500)], flat_value='Revenue'),
            AccountNumberSegment(
                [f'{_:03}' for _ in range(500, 600)], flat_value='Expenses'),
        )   
    ]

    Where the first item is the name of the segment, followed by the possible
    / defined values for that segment and the defined names that have been
    given them.

    Of these possible values, the first value will be assumed to be the
    default.

    This would define an account number of the following form:
    XX-XX-XXX

    Where we have a specific enumeration of values for each segment.
    '''
    def __init__(self, *args:AccountNumberSegment, separator='-'):
        self.segments:dict[str, AccountNumberSegment] = OrderedDict()
        self.separator = separator
        # Sentinel value, we must assure that there is only 1 auto-incrementing
        # segment per account number template
        self._increment_segment = None

        for segment in args:
            if not isinstance(segment, AccountNumberSegment):
                raise ValueError('Initializing AccountNumberTemplate with a '
                                 'type besides AccountNumberSegment: '
                                 f'{type(segment)}')
            if segment.name in self.segments:
                raise ValueError('Initializing AccountNumberTemplate with '
                                 f'duplicate segment name: {segment.name}')
            if segment._incrementable:
                if self._increment_segment is not None:
                    error_msg = (f'Error, cannot create {self.__class__.__name__} '
                                 'with more than one incrementing segment')
                    raise ValueError(error_msg)
                self._increment_segment = segment

            self.segments[segment.name] = segment
            

    def _show_form(self, fill_char='X', separator=None):
        '''
        Shows the number format of an account number following this template:
        eg: XX-XXX-XX
        '''
        if separator is None:
            separator = self.separator
        to_return = ''

        for segment in self.segments.values():
            to_return += fill_char * segment.length
            to_return += separator
        
        # Avoid errors if this template has no segments
        if not to_return:
            return ''
        
        # Remove last fill_char, also returns an empty
        return to_return[:-1]

    def __str__(self):
        return self._show_form()

    def validate_account_number(self, number, separator=None):
        '''
        Validate that a given account number matches the template instance.

        Returns True or False
        '''
        if separator is None:
            separator = self.separator

        # Add a convenience here so you can pass in an Account instance or an
        # account number string
        if isinstance(number, Account):
            number = number.number

        # Important that it's zipped so that templates with identical segments
        # in different orders do not match
        for val, seg in zip(number.split(separator), self.segments.values()):
            try:
                # seg.__getitem__ is defined to do all the logic here or spit
                # out a KeyError
                seg[val]
            except KeyError:
                return False
            continue
        return True
    
    def _make_account_number(self, **kwargs) -> _AccountNumber:
        '''
        In order to facilitate larger account numbers, I have seen fit to
        expand the account number template functionality to be able to create
        a corresponding _AccountNumber instance from a named set of inputs.

        This function will serve as an OOP method to create account numbers
        from the named meanings of each of the named segments of the account
        number.

        For example, assume we have an account number template something of the
        form:
        ```
        rules = {
            'Company Code': '01',
            'Department Code': '01',
            'Account Code': '100'
        }
        ```

        If we want to dynamically create an account number using the above
        values, we can have `rules` be the kwargs passed in to the function
        so that the account number creation is self-documenting.
        '''
        number = ''
        # First translate the kwargs into their segments and check if exist
        for arg in kwargs:
            if arg not in self.segments:
                raise ValueError(f'Input segment name "{arg}" DNE in template')
            
        for segment_name in self.segments:
            if segment_name not in kwargs:
                error_msg = (f'Input account details did not include'
                              f'mandatory segment "{segment_name}"')
                raise ValueError(error_msg)
            number += kwargs[segment_name]
            number += self.separator

        if number.endswith(self.separator):
            number = number.rstrip(self.separator)

        return _AccountNumber(number, self)
    
    def make_account(self, name:str, account_type:AccountType,
                     initial_balance:int = 0, **kwargs) -> Account:
        '''
        Creates an account using a dictionary set of segment names and values
        '''
        acc_num = self._make_account_number(**kwargs)
        return Account(name=name, number=acc_num, account_type=account_type,
                       initial_balance=initial_balance)

    def show_template(self):
        '''
        Prints the details and possible values of the segments of this account
        number template
        TODO
        '''
        raise NotImplementedError()

class _AccountNumber:
    '''
    A class wrapping account numbers.  More than just a unique identifier,
    there are typically partitions and special meanings for specific digits
    in the account number that can quickly be used to locate and describe
    the type of account without having to parse the name.

    Here is a typical layout.

    2-digit Division code
    2-digit Department code
    3-digit account code, using the following subdivisions.
        
        Account code    Meaning
        100-199         Assets
        200-299         Liabilities
        300-399         Equity Accounts
        400-499         Revenues
        500-599         Expenses
    '''

    def __init__(self, number: str, template: AccountNumberTemplate):
        if number is None:
            raise TypeError('Error Initializing - account number is None')

        if template.validate_account_number(number) is False:
            raise InvalidAccountNumberException(
                f'{number} does not match the given template')
        
        self.template = template
        self._dict = OrderedDict()

        values = number.split(template.separator)
        for seg_name, value in zip(template.segments, values):
            self._dict[seg_name] = value

            # Add property access for all segments
            attr_name = seg_name.lower().replace(' ', '_')
            setattr(self, attr_name, value)
    
    @property
    def number(self):
        '''
        Recreate the account number in visual form
        '''
        to_return = ''
        for item in self._dict.values():
            to_return += item
            to_return += self.template.separator
        
        return to_return[:-len(self.template.separator)]
    
    def __getitem__(self, key):
        return self._dict[key]

    def __hash__(self):
        return hash(''.join([item for item in self._dict.values()]))
    
    # Define sorting methods
    def __eq__(self, other):
        return self.number == other
    
    def __ne__(self, other):
        return self.number != other
    
    def __lt__(self, other):
        if not isinstance(other, _AccountNumber):
            raise NotImplemented
        if self.template != other.template:
            raise InvalidAccountNumberException(
                'Cannot compare two accounts with different templates.')
        
        left_tokens = self.number.split(self.template.separator)
        right_tokens = other.number.split(other.template.separator)
        for left, right in zip(left_tokens, right_tokens):
            # Compare as strings
            if left < right:
                return True
        
        return False

class Account:
    def __init__(self, name:str, number:_AccountNumber|str,
                 account_type:AccountType, initial_balance=0,
                 template:AccountNumberTemplate=None):
        # The name is just a text description of the account with no strict
        # rules or guidelines
        if not name:
            raise ValueError('Trying to initialize account with an empty name')
        self.name = name

        # The number is a strictly templated value that must conform to an
        # AccountNumberTemplate.
        if not isinstance(number, _AccountNumber):
            if template is None:
                raise TypeError('String AccountNumber given with no Template')
            self._account_number = _AccountNumber(number, template)
        else:
            self._account_number = number

        # Easy access to a raw string version of the account number
        # formatted with the template's default separator
        self.number = self._account_number.number

        # Either a credit or a debit
        if account_type is None or not isinstance(account_type, AccountType):
            raise ValueError('Trying to create a new account with an invalid '
                             'Account type (must be Credit or Debit)')
        self.account_type = account_type

        # A set of JournalEntry instances added to whenever this account is
        # involved in a Journal addition
        self.journal_entries:set[JournalEntry] = set()

        # TODO no logic around initial balanaces yet
        self.initial_balance = initial_balance

        # These are accessed by each JournalEntry every time a new one
        # regarding this account is posted to a Journal
        self.gross_debit = 0
        self.gross_credit = 0
    
    @classmethod
    def from_template(cls, template:AccountNumberTemplate,
                      account_type:AccountType, details:dict[str, str]):
        '''
        Create an account from a template
        '''
        raise NotImplementedError()

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name

    def __eq__(self, other):
        if not isinstance(other, Account):
            return NotImplemented
        
        return (self.name == other.name and self.number == other.number
                and self.account_type == other.account_type)

    def __getitem__(self, key):
        return self._account_number[key]

    def __hash__(self):
        '''
        I want to be able to have a set() of Accounts
        '''
        return hash((self.name, self.number, self.account_type))

    @property
    def display_name(self):
        '''
        Return a nice and easy to read formatted view of the account
        TODO
        '''
        raise NotImplementedError()


    def add_journal_entry(self, journal_entry):
        self.journal_entries.add(journal_entry)
        if self == journal_entry.acc_debit:
            self.gross_debit += journal_entry.amount
        elif self == journal_entry.acc_credit:
            self.gross_credit += journal_entry.amount

    @property
    def net_balance(self):
        '''
        Return the net balance of the account, depending on whether it is a
        credit or a debit
        '''
        to_return = self.initial_balance

        if self.account_type == AccountType.CREDIT:
            to_return += self.gross_credit
            to_return -= self.gross_debit
        elif self.account_type == AccountType.DEBIT:
            to_return += self.gross_debit
            to_return -= self.gross_credit
        
        return to_return

    @staticmethod
    def net_balance_agg(accounts, report_format):
        '''
        Given an iterable of accounts, go through them and report the net
        sum of their balances.

        `report_format` controls whether the end result is reported as a
        credit or debit (ie, should debts be positive or negative)
        '''
        debits = 0
        credits = 0

        for account in accounts:
            debits += account.gross_debit
            credits += account.gross_credit
        
        if report_format == AccountType.CREDIT:
            return credits - debits
        elif report_format == AccountType.DEBIT:
            return debits - credits
        else:
            raise TypeError('Invalid reporting format specified')
        
    @staticmethod
    def get_net_transfer(debit_accounts:list[Account],
                         credit_accounts:list[Account],
                         start_date=datetime.min, end_date=datetime.max,
                         memo:re.Pattern=re.compile('.*')):
        '''
        Get the net flow of capital from the debit_accounts group to the
        credit_accounts group, reporting in terms of net credit or debit flow.

        Now with an option to match transactions whose memos match a certain
        pattern.
        '''

        net_transfer = 0

        for account in credit_accounts:
            for entry in account.journal_entries:
                if start_date <= entry.date <= end_date:
                    # search vs match - want a match anywhere in the string
                    if not memo.search(entry.memo):
                        continue
                    if entry.acc_debit in debit_accounts:
                        net_transfer += entry.amount
                    elif entry.acc_credit in debit_accounts:
                        net_transfer -= entry.amount

        return net_transfer



    def print_t_account(self):
        '''
        Construct and print the T account for this account as a formatted
        table
        TODO
        '''
        raise NotImplementedError()

class ChartOfAccounts(dict):
    '''
    A structure that holds a set of related accounts and related formatting
    functions

    Much TODO here
    '''
    def __init__(self, template:AccountNumberTemplate=None, mapping={}):
        super().__init__(mapping)

        if template is None:
            template = AccountNumberTemplate(
                AccountNumberSegment('DUMMY', {'1': 'no_meaning'}))

        if not isinstance(template, AccountNumberTemplate):
            raise TypeError('template must be of class '
                            'pybooks.account.AccountNumberTemplate.')
        self.template = template

    # Copy dict() builtins
    @classmethod
    def _wrap_methods(cls, names):
        def wrap_method_closure(name):
            def inner(self, *args):
                result = getattr(super(cls, self), name)(*args)
                if isinstance(result, set) and not hasattr(result, 'foo'):
                    result = cls(result, foo=self.foo)
                return result
            inner.fn_name = name
            setattr(cls, name, inner)
        for name in names:
            wrap_method_closure(name)
    
    def add_account(self, account:Account|str, number:str=None,
                    account_type:AccountType=None):
        '''
        Add a new account to this ledger, either as a pre-existing Account
        instance or creating a new one from the raw details and the account
        number template associated with this ledger.
        '''
        if not isinstance(account, Account):
            if not isinstance(number, str) and \
                    isinstance(account_type, AccountType):
                raise TypeError('Invalid account initialization values.')
            
            if not self.template.validate_account_number(number):
                raise InvalidAccountNumberException(f'{number} does not match '
                                                    'the given template')
            account = Account(account, number, account_type,
                              template=self.template)

        # Safety Check: The account must have the same template as this chart
        if account._account_number.template != self.template:
            raise ValueError('Trying to add an Account with a different '
                             'AccountNumberTemplate')

        # This test must come first as it is more permissive
        if account.number in self:
            raise DuplicateException('Trying to add a new account with a '
                                        f'duplicate number: {account.number}')
    
        self[account.number] = account
        # Return the account to add to a ledger's personal collection of
        # accounts
        return account

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

# Make sure the set wrapper class has all of the builtin set methods
ChartOfAccounts._wrap_methods([
    '__class_getitem__', '__contains__', '__delattr__', '__delitem__',
    '__eq__', '__format__', '__ge__', '__getattribute__', '__getitem__',
    '__gt__', '__hash__', '__ior__', '__iter__', '__le__', '__len__', '__lt__',
    '__ne__', '__or__', '__reduce__', '__reduce_ex__', '__repr__',
    '__reversed__', '__ror__', '__setattr__', '__setitem__', '__sizeof__',
    'clear', 'copy', 'fromkeys', 'get', 'items', 'keys', 'pop', 'popitem',
    'setdefault', 'update', 'values'
])
