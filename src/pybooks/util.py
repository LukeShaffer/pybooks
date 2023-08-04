from datetime import datetime

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
    print(date)
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
            

