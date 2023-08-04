from enum import IntEnum, auto

class AccountingMethods:
    ACCRUAL = 'Accrual Accounting'
    CASH = 'Cash Accounting'

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
