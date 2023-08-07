'''
Provides functionality for accounting Accounts
'''
import re
from collections import OrderedDict

from pybooks.util import InvalidAccountNumberException
from pybooks.enums import AccountType


class ChartOfAccounts(dict):
    '''
    A structure that holds a set of related accounts and related formatting
    functions

    Much TODO here
    '''
    def __init__(self, mapping={}):
        super().__init__(mapping)

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

class AccountNumberSegment:
    '''
    A class to wrap account number segment functionality

    These will either be initialized with a dictionary of exactly defined
    key-value pairs, or a range / list / regex and a static category value such
    as "Assets".  These will function as the allowable / defined values and
    their meanings.

    TODO perhaps change this class to be initialized with a regex instead of a
    range() or a dictionary
    '''
    def __init__(self, meanings, flat_value=None, length=None):
        self.meanings = meanings
        self.flat_value = flat_value
        self.length = length

        regex_repetition_chars = '*+?'

    
        # Regex sanitation, make sure that there aren't any variable length
        # regexes
        
        if isinstance(meanings, re.Pattern):
            error_msg = 'Cannot have a variable length AccountNumberSegment.'
            if re.findall(r'{\d+,\d+}', meanings.pattern):
                raise InvalidAccountNumberException(error_msg)
            for char in regex_repetition_chars:
                if char in meanings.pattern:
                    raise InvalidAccountNumberException(error_msg)

            # Make sure that a length has been reported
            if length is None:
                raise TypeError(
                    '"length" keyword not specified when initializing from '
                    'regex')
        
        # Check for uniform meanings lengths
        elif isinstance(meanings, dict):
            first_len = 0
            for key in meanings:
                first_len = len(key)
                self.length = first_len
                break
            
            if not all([len(x) == first_len for x in meanings]):
                raise ValueError('AccountNumberSegment input dict has '
                    'variable length keys')

        # General iterable case
        else:
            first_len = len(meanings[0])
            self.length = first_len
            if not all([len(x) == first_len for x in meanings]):
                raise ValueError('AccountNumberSegment has variable length '
                    'meanings')

    
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
        if self.flat_value is not None:
            if key in self:
                return self.flat_value
            raise KeyError(
                f'Key {key} does not exist in current account segment')
        return self.meanings[key]
    
    def get_key_length(self):
        if self.length is not None:
            return self.length

        if isinstance(self.meanings, re.Pattern):
            # A self-reported length field that must be included when
            # initializing off of a regex
            return self.length

        # self.meanings will be a flat list
        if self.flat_value is not None:
            for meaning in self.meanings:
                self.length = len(meaning)
                return len(meaning)
        
        # self.meanings is a dict
        for meaning in self.meanings.keys():
            self.length = len(meaning)
            return len(meaning)



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
                [f'{_:03}' for _ in range(200, 300)],flat_value='Liabilities'),
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

    This would define an account number of the following form:
    XX-XX-XXX

    Where we have a specific enumeration of values for each segment.
    '''
    def __init__(self, segments, separator='-'):
        self.segments = segments
        self.separator = separator
    
    def _show_form(self, fill_char='X'):
        '''
        Shows the number format of an account number following this template:
        eg: XX-XXX-XX
        '''
        to_return = ''
        for segment in self.segments:
            to_return += fill_char * segment[1].get_key_length()
            to_return += self.separator
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

        for current, rules in zip(number.split(separator), self.segments):
            # Each segment can have multiple possible definitions
            meaning, seg_defs = rules[0], rules[1:]

            # Need to find each segment for the whole number to be valid
            found = False
            
            for segment in seg_defs:                
                if current in segment:
                    found = True
                    break
            if not found:
                return False

        return True  

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
        if template.validate_account_number(number) is False:
            raise InvalidAccountNumberException(
                f'{number} does not match the given template')
        
        self.template = template
        self._dict = OrderedDict()

        values = number.split(template.separator)
        for segment, value in zip(template.segments, values):
            self._dict[segment[0]] = value
    
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
    def __init__(self, name:str, number:str, template:AccountNumberTemplate,
                 account_type:AccountType, initial_balance=0):
        # The name is just a text description of the account with no strict
        # rules or guidelines
        self.name = name

        # The number is a strictly templated value that must conform to an
        # AccountNumberTemplate.
        self._account_number = _AccountNumber(number, template)

        # Easy access to a raw string version of the account number
        # formatted with the template's default separator
        self.number = self._account_number.number

        # Either a credit or a debit
        self.account_type = account_type

        # A set of JournalEntry instances added to whenever this account is
        # involved in a Journal addition
        self.journal_entries = set()

        # TODO no logic around initial balanaces yet
        self.initial_balance = initial_balance

        # These are accessed by each JournalEntry every time a new one
        # regarding this account is posted to a Journal
        self.gross_debit = 0
        self.gross_credit = 0

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name

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


    def print_t_account(self):
        '''
        Construct and print the T account for this account as a formatted
        table
        TODO
        '''
        raise NotImplementedError()
