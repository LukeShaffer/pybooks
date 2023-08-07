from enum import IntEnum, Enum, auto

class AccountingMethods:
    ACCRUAL = 'Accrual Accounting'
    CASH = 'Cash Accounting'

class AccountType(str, Enum):
    '''
    Best name I could think of for the Debit / Credit divide
    '''
    DEBIT = 'Debit'
    CREDIT = 'Credit'

class CoreSubledgers(IntEnum):
    '''
    A Collection of standard subledgers to organize a ledger's accounts.
    Like categories for the General Ledger.  
    '''

    ASSETS = 0
    LIABILITIES = auto()
    EQUITY = auto()
    REVENUE = auto()
    COST_OF_SALES = auto()  # Includes Taxes
    EXPENSES = auto()
