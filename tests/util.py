'''
Common patterns needed in many separate tests
'''


import re

from pybooks.account import AccountNumberSegment, AccountNumberTemplate

def init_template():
    '''
    Reusable test code, template format

    01-02-100
    '''
    seg1_vals = {
        f'{num:02}': f'cmpny{num}'
        for num in range(1, 4)
    }
    seg1_vals.update({
        f'{num:02}': f'cmpny{num}'
        for num in range(10, 15)
    })

    seg1 = AccountNumberSegment('Company Code', seg1_vals)
    seg2 = AccountNumberSegment('Department Code', {
        f'{num:02}': f'dpt{num}'
        for num in range(3)
    })

    seg3 = AccountNumberSegment('Account Code', {
        re.compile(r'1\d\d'): 'Assets',
        re.compile(r'2\d\d'): 'Liabilities',
        re.compile(r'3\d\d'): 'Equity',
        re.compile(r'4\d\d'): 'Revenue',
        re.compile(r'5\d\d'): 'Expenses',
    }, is_regex=True)

    template = AccountNumberTemplate(seg1, seg2, seg3)

    return template