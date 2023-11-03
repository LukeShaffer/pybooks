'''
'''
from __future__ import annotations

import math
# "Circular" imports only for type annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from pybooks.account import Account

from collections import defaultdict
from datetime import datetime

from pybooks.util import parse_date, normal_round, truncate

class Journal:
    def __init__(self, currency_symbol='$'):
        # A dictionary from dates to a list of entries on that date
        # The combined date+index will mark the journal ID for the transaction
        self._entries:defaultdict[datetime.datetime, list] = defaultdict(list)
        self.num_entries = 0
        self.accounts:set[Account] = set()

        self._currency = currency_symbol
    
    def print_journal(self, use_acc_numbers=False, use_acc_names=True,
            date_format='%B %d, %Y', tab_len=4):
        '''
        Iterate through all stored transactions and print them into a table
        for inspection.

        Can specify either account names, numbers or both in the table.

        If they are both specified the account number will be printed first

        TODO Add support for compound journal entries
        '''
        def get_entry_lengths(entry, use_nums, use_names):
            '''
            Util function that gets the max length of an account for the
            printed journal with the optional specified number or name format
            
            Returns a 2-tuple: debit_len, credit_len
            '''
            if not use_nums and not use_names:
                return (0, 0)

            # In multiplcation bools resolve to 0 or 1
            debit_len = len(entry.acc_debit.number) * use_nums
            debit_len += len(entry.acc_debit.name) * use_names

            credit_len = len(entry.acc_credit.number) * use_nums
            credit_len += len(entry.acc_credit.name) * use_names

            # If name and number are specified put a space between them
            if use_nums and use_names:
                debit_len += 1
                credit_len += 1

            return (debit_len, credit_len)
        
        def get_acc_col_length(entry_list, use_nums, use_names, tab_len):
            '''
            Get the overall length for the Account Column in the printed table.
            '''
            if not use_nums and not use_names:
                return 0

            to_return = 0

            for entry in entry_list:
                debit_len, credit_len = \
                    get_entry_lengths(entry, use_nums, use_names)
                
                to_return = max(to_return, debit_len, credit_len + tab_len)

            return to_return 

        # dictionaries keys are unordered
        dates = sorted(self._entries)

        cols = ('Date', 'Account', 'Debit', 'Credit')
        longest = [0] * len(cols)

        # Get the longest values for each column
        for date, entry_list in self._entries.items():
            longest[0] = max(
                longest[0],
                len(datetime.strftime(date, date_format))
            )
            # max will return the JournalEntry object
            longest[1] = max(
                longest[1],
                get_acc_col_length(entry_list, use_acc_numbers, use_acc_names,
                                   tab_len)
            )
            longest[2] = max(
                longest[2],
                len('{}{:,}'.format(
                    self._currency,
                    max(entry_list, key=lambda x: x.amount).amount)
                )
            )

            longest[3] = longest[2]

        lc = longest
        tab = ' ' * tab_len
        title_row = (
            '{0:<{lc[0]}}{tab}'
            '{1:<{lc[1]}}{tab}'
            '{2:<{lc[2]}}{tab}'
            '{3:<{lc[3]}}'
            .format(*cols, tab=tab,lc=lc)
        ).strip()

        print(title_row)
        print('=' * len(title_row))
        sorted_dates = sorted(self._entries.keys())

        for date in sorted_dates:
            for entry in self._entries[date]:
                debit_name = ''
                credit_name = ''
                if use_acc_numbers:
                    debit_name += entry.acc_debit.number
                    credit_name += entry.acc_credit.number

                    # Add a space only if the name is coming after and
                    # the name is populated
                    if use_acc_names:
                        debit_name += ' '
                        credit_name += ' '
                
                if use_acc_names:
                    debit_name += entry.acc_debit.name
                    credit_name += entry.acc_credit.name

                # Print the debit account, and then the credit account
                print(
                    '{0:<{lc[0]}}{tab}'
                    '{1:<{lc[1]}}{tab}'
                    '{curr}{2:<{lc[2]},}{tab}'
                    '{3:<{lc[3]}}'
                    .format(
                        datetime.strftime(entry.date, date_format),
                        debit_name,
                        entry.amount,
                        '',
                        lc=lc,
                        tab=tab,
                        curr=self._currency
                    )
                    .strip()
                )
                # Indent the credited account
                print(
                    '{0:<{lc[0]}}{tab}'
                    '{1:<{lc[1]}}{tab}'
                    '{2:<{lc[2]}}{tab}'
                    '{curr}{3:<{lc[3]},}'
                    .format(
                        '',
                        tab + credit_name,
                        '',
                        entry.amount,
                        lc=lc,
                        tab=tab,
                        curr=self._currency
                    )
                    .rstrip()  # Indented with spaces on the left
                )
                print('-' * len(title_row))

    def add_account(self, account):
        '''
        Add an account to this journal's collection of accounts
        '''
        self.accounts.add(account)
    
    def add_entry(self, entry):
        if not isinstance(entry, JournalEntry):
            raise TypeError('Entry must be a JournalEntry')
        self._entries[entry.date].append(entry)
        self.num_entries += 1

        # Link all of the entries together
        for account in (entry.acc_credit, entry.acc_debit):
            self.add_account(account)

class JournalEntry:
    '''
    Each individual journal entry in the journal will be its own instance.

    The credit and debit accounts will be account instances that can be queried
    for more information

    Following the layout in a T account, debits are on the left, and credits
    are on the right
    '''
    def __init__(self, date, acc_debit, acc_credit, amount, memo=''):
        if None in (acc_debit, acc_credit):
            raise ValueError('Cannot create JournalEntry with a Null account!')
        if amount == 0:
            raise ValueError('Typo, you are trying to create a journal entry '
                'with no amount')

        self.date = parse_date(date)
        self.acc_debit = acc_debit
        self.acc_credit = acc_credit
        self.amount = amount
        self.memo = memo

        acc_credit.add_journal_entry(self)
        acc_debit.add_journal_entry(self)


    def __repr__(self):
        return f'Journal Entry: {self.acc_debit} <- {self.acc_credit} for {self.amount}'


def split_wages(gross_wages, rules, date=datetime.now()):
    '''
    Given a gross wage amount and a set of rules with which to split them,
    return a series of journal entries that represent all of the splits and
    deductions from your gross wages.

    See examples.py for an example ruleset to feed this function.

    Example.
    
    You have a $100 paycheck.
    You have the following pre-tax deductions:
        $10 medical insurance
        $20 retirement account contribution
    You pay the following taxes:
        10% federal income tax
        3% state income tax
    You have the following post-tax deductions:
        5% 2nd retirement account

    This function will do the operations in order and return a list of
    JournalEntry's that represent the splitting of your paycheck.
    '''
    def parse_split_str(split_str):
        '''
        Parse numbers or percentages and return a decimal variable.

        Returns a 2-tuple (is_percentage, value)
            where is_percentage is a boolean
            and value is the float value of the input
        '''
        try:
            return (False, float(split_str))
        except ValueError as e:
            if split_str.strip()[-1] == '%':
                return (True, float(split_str.strip()[:-1]) / 100)
            else:
                raise ValueError(f'Unparseable split_str "{split_str}"')

    def split_wage(starting_wage, split_str, round_method):
        '''
        Do logic to determine the split of the starting wage with either
        flat amounts or percentages.

        pass round_method = None to skip rounding

        Returns either split_str as a float or if split_str ends with a
        '%', returns that percentage of the starting_wage
        '''
        is_percentage, split_str = parse_split_str(split_str)
        if is_percentage:
            split_str = starting_wage * split_str
        
        if round_method == 'Normal':
            split_str = normal_round(split_str, 2)
        elif round_method == 'Truncate':
            split_str = truncate(split_str, 2)
        elif round_method == 'Banker':
            # The default Python round() function is a banker's round
            # implementation
            split_str = round(split_str, 2)
        elif round_method is None:
            pass
        else:
            raise ValueError('Invalid round_method specified')
        
        return split_str

    to_return = []

    # Set up global rounding constants and behavior
    global_round = rules.get('round', False)
    global_round_method = rules.get('round_method', "Banker")

    to_return.append(JournalEntry(date=date, acc_credit=rules['acc_credit'],
                                  acc_debit=rules['acc_debit'],
                                  amount=gross_wages, memo=rules['memo']))
    
    # These could be flat amounts or percentages in the case of bonuses
    additional_wage_total = 0
    for additional_wage in rules['ADDITIONAL_WAGES']:
        # Check any rounding overrides for this step
        step_round = additional_wage.get('round', global_round)

        if step_round:
            step_round_method = additional_wage.get('round_method',
                                                    global_round_method)
        else:
            step_round_method = None
        step_wage = split_wage(starting_wage=gross_wages,
                               split_str=additional_wage['amount'],
                               round_method=step_round_method)
        additional_wage_total += step_wage
        to_return.append(
            JournalEntry(date=date, acc_credit=additional_wage['acc_credit'],
                         acc_debit=additional_wage['acc_debit'],
                         amount=step_wage, memo=additional_wage['memo']))
        
    # Add vacation and bonus credit to the total wages being calculated
    gross_wages += additional_wage_total

    pre_tax_ded_total = 0
    for deduction in rules['PRE_TAX_DEDUCTIONS']:
        step_round = deduction.get('round', global_round)
        if step_round:
            step_round_method = deduction.get('round_method',
                                              global_round_method)
        else:
            step_round_method = None
        step_wage = split_wage(starting_wage=gross_wages,
                               split_str=deduction['amount'],
                               round_method=step_round_method)

        pre_tax_ded_total += step_wage
        to_return.append(
            JournalEntry(date=date, acc_credit=deduction['acc_credit'],
                         acc_debit=deduction['acc_debit'], amount=step_wage))
        

    if pre_tax_ded_total > gross_wages:
        raise ValueError('Pre Tax Deductions are larger than gross wages')


    tax_total = 0
    for tax in rules['TAXES']:
        step_round = tax.get('round', global_round)
        if step_round:
            step_round_method = tax.get('round_method', global_round_method)
        else:
            step_round_method = None
        
        step_wage = split_wage(starting_wage=gross_wages - pre_tax_ded_total,
                               split_str=tax['amount'],
                               round_method=step_round_method)

        tax_total += step_wage
        to_return.append(
            JournalEntry(date=date, acc_credit=tax['acc_credit'],
                         acc_debit=tax['acc_debit'], amount=step_wage)
        )

    if tax_total > gross_wages or tax_total + pre_tax_ded_total > gross_wages:
        raise ValueError('Taxes have pushed gross wages negative')

    post_tax_ded_total = 0
    for deduction in rules['POST_TAX_DEDUCTIONS']:
        step_round = deduction.get('round', global_round)
        if step_round:
            step_round_method = deduction.get('round_method',
                                              global_round_method)
        else:
            step_round_method = None
        step_wage = \
            split_wage(starting_wage=gross_wages-pre_tax_ded_total-tax_total,
                       split_str=deduction['amount'],
                       round_method=step_round_method)
        post_tax_ded_total += step_wage

        to_return.append(
            JournalEntry(date=date, acc_credit=deduction['acc_credit'],
                         acc_debit=deduction['acc_debit'], amount=step_wage)
        )
    
    
    if post_tax_ded_total > gross_wages \
            or post_tax_ded_total + tax_total + pre_tax_ded_total > gross_wages:
        raise ValueError('Post Tax deductions have pushed gross wages negative')
    
    """
    print('=====================')
    print(gross_wages)
    print(pre_tax_ded_total)
    print(tax_total)
    print(post_tax_ded_total)
    print('=====================')
    """

    return to_return

