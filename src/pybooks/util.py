from datetime import datetime
import math
from typing import Union

class DuplicateException(Exception):
    pass

class InvalidAccountNumberException(Exception):
    # TODO maybe through a logging statement in here saying which part of the
    # account number doesn't line up.
    '''
    Raised when an account is trying to be parsed that does not match the
    given account number template
    '''
    pass

class NullAccountTemplateError(Exception):
    '''
    To be raised when a _Ledger or subclass is interacted with in a way that
    involves child accounts before the Ledger has initialized its account
    number template.
    '''
    pass

def truncate(num:Union[int, float], decimals:int):
    '''
    Truncates a decimal number to a certain length of decimal places
    '''
    # Short-circuit check
    if decimals == 0:
        return int(num)
    
    dec_place = str(num).find('.')

    # No decimals, nothing to round
    if dec_place == -1:
        return num
    
    # Python lets you over-extend slicing ranges on strings
    # Need to add the extra 1 since the end index is non-inclusive
    return float(str(num)[0:dec_place+decimals+1])    

def normal_round(num:Union[int,float], decimals:int):
    '''
    Perform a normal schoolyard rounding operation, rounding up to the next
    place on 5's
    '''
    whole_num = ''
    dec = ''

    seen_dec = False
    dec_place = 0

    for char in str(num):
        if char == '.':
            seen_dec = True
            continue
        if not seen_dec:
            whole_num += char
            continue
        dec += char
        dec_place += 1

        if dec_place == decimals + 1:
            break
    
    # Round up
    if int(dec[-1]) >= 5:
        # Need special logic here in case of whole number rounding
        if decimals == 0:
            return math.ceil(num)
        dec = f'{dec[0:-2]}{int(dec[-2]) + 1}0'
    # Round down
    else:
        if decimals == 0:
            return math.floor(num)
        dec = dec[:-1]


    return float(f'{whole_num}.{dec}')

def calculate_progressive_tax(taxable_income:Union[int, float], tax_brackets:list):
    '''
    Method to dynamically calculate the amount of money that a certain income
    would owe in taxes using the given (progressive) tax brackets.

    tax_bracket format is the following:

    ```
    * a list of 2-tuples: the tax rate and the maximum income of the row /
    bracket.
    * Must be specified in ascending order.
    * Use 'inf' for the top un-capped tax bracket:
    [
        (0.05, 999),
        (0.15, 1500),
        (0.30, 'inf')
    ]
    ```
    '''
    to_return = 0
    prev_max = 0
    for bracket in tax_brackets:
        rate, max_income = bracket
        max_income = float(max_income)
        if max_income <= prev_max:
            raise SyntaxError('There is an error with the supplied tax brackets')

        if taxable_income > max_income:
            to_return += rate * (max_income - prev_max)
            prev_max = max_income
            continue
        elif taxable_income <= max_income:
            to_return += rate * (taxable_income - prev_max)
            return to_return
        
    
    raise ValueError('Income beyond last defined tax bracket detected')

        

    
    


def parse_date(date, user_format=None):
    '''
    Parse a date according to some predefined rules.

    If it is already a datetime just return it.
    '''
    if isinstance(date, datetime):
        return date

    if user_format is not None:
        return datetime.strptime(date, user_format)

    DATE_SEPARATORS = ('/', '-', ',', ', ', ' ')
    DATE_FORMATS = [
        ('%Y', '%m', '%d'),         # 2001/05/25, with any variation of separator
        ('%a', '%b', '%d', '%Y'),   # Sun Jan 22, 2023
        ('%A', '%b', '%d', '%Y'),   # Sunday Jan 22, 2023
        ('%a', '%B', '%d', '%Y'),   # Sun January 22, 2023
        ('%A', '%B', '%d', '%Y'),   # Sunday January 22, 2023
    ]
    TIME_FORMATS = [
        '%H',           # 13
        '%I %p',        # 1 PM
        '%H:%M',        # 13:25
        '%I:%M %p',     # 1:25 PM
        '%H:%M:%S',     # 13:25:01
        '%I:%M:%S %p',  # 1:25:01 PM
    ]
    TIME_SUFFIXES = (
        '%Z',       # Timezones like GMT, PST 
    )

    def date_builder(queue, result='', total=[]):
        if not queue:
            return result

        result += queue[0]
        if len(queue) == 1:
            return result

        for sep in DATE_SEPARATORS:
            total.append(date_builder(queue[1:], result+sep, total))
        
        return total


    has_time = ':' in date
    # print(date)
    for form in DATE_FORMATS:
        if not has_time:
            for built_form in date_builder(form):
                try:
                    return datetime.strptime(date, built_form)
                except:
                    continue
        else:
            # All dates at this point will have a time component
            time_first_half = date.find(':') / len(date) < 0.5

            for bf in date_builder(form):
                for time in TIME_FORMATS:
                    if time_first_half:
                        try:
                            return datetime.strptime(date, f'{time} {bf}')
                        except:
                            pass
                    else:
                        try:
                            return datetime.strptime(date, f'{bf} {time}')
                        except:
                            pass
                    for suffix in TIME_SUFFIXES:
                        if time_first_half:
                            try:
                                return datetime.strptime(f'{time} {suffix} {bf}')
                            except:
                                pass
                        else:
                            try:
                                return datetime.strptime(f'{bf} {time} {suffix}')
                            except:
                                pass
    
    return None
            

