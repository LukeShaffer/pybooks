
_AMOUNT_SYNTAX = r'\d*(\.\d*)%?'

EXAMPLE_WAGE_SPLIT_RULES = {
    # Top-level wage details
    'acc_credit': 'Account()',
    'acc_debit': 'Account()',
    'memo': 'Gross Wage Memo',
    'round': 'Optional. True or False - Defaults to False',
    'round_method': 'Optional. "Banker", "Normal", or "Truncate" - \
        Defaults to "Banker"',

    # Put things like bonuses and vacation time billed separately here
    # if you only want one split for taxes and insurance to match your paystub
    'ADDITIONAL_WAGES': [
        {
            'acc_credit': 'Account()',
            'acc_debit': 'Account()',
            'amount': '500',
            'memo': 'Memo'
        },
        # ... Etc for each additional item
    ],

    'PRE_TAX_DEDUCTIONS': [
        {
            'acc_credit': 'Account()',
            'acc_debit': 'Account()',
            'amount': '55.3',
            'memo': 'Flat Deduction',
        },
        {
            'acc_credit': 'Account()',
            'acc_debit': 'Account()',
            'amount': '15%',
            'memo': r'15% of gross wages'
        }, # ... Etc for each additional item
    ],

    'TAXES': [
        'Same syntax as above'
    ],

    'POST_TAX_DEDUCTIONS': [
        'Same syntax as above'
    ]
}