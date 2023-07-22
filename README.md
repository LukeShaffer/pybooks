# Purpose
This is meant to be a simple programatic ledger for use in basic bookkeeping
/ accounting applications.

There will be some basic accounting knowledge needed to understand the
terminology here, but I will try and provide a primer in the README.

# Project Layout


# Accounting Concepts

## Account
`A place where we can record, sort, and store all transactions that affect a related group of items.`
Forget everything you know about the word "Account" becuase in the context of
accounting it takes on a slightly different meaning.  An account transcends
the normal connotation of a bank or brokerage account which is basically a
location for money to travel to or from, to a non-physical label that we apply
to a group of related transactions simply for organizational purposes.

An "Account" here could transcend several bank accounts, what constitutes an
account is that money is flowing in or out for some related purpose.

Accounts are generally conceptualized as either an Asset or a Liability for
planning purposes

For example, here are some sample accounts you might find

- Cash Account
    The total net sum of cash at a person or business's disposal.  You can see
    that if the entity had multiple cash bank accounts how these all fall under
    the same accounting "Account" umbrella while being separate accounts
    legally.

- Loans Payable
    If a business takes out a loan from a bank, this is the account that would
    receive the loan as a credit on their balance sheet.  This account contains
    every entity that has loaned the POV money.

- Equipment
    This one takes some getting used to, but it refers to the intrinsic dollar
    amount that any equipment you own possesses.  For example, if you use
    $10,000 to buy a truck for work, that $10,000 doesn't just disappear off
    the books and go to money heaven, it gets credited from your cash account
    and debited as a line item into your equipment account.

## Journal
[Here](https://www.accountingtools.com/articles/what-is-a-journal-entry.html)
is a link to the guides I will be using to put this project together.

At the most basic level of accounting is the journal.  The "Book of Original
Entry" as it is also known is simply a line by line log of transactions as they
take place.  Each of these journal entries contains the date, the parties or
accounts involved, and the amount of money that exchanged hands.

Here is an example journal entry for the sale of a $100 product:
```
Date        Account                         Debit   Credit     
============================================================
2020/01/25  Cash                            $100
                Product Revenue                     $100
            (Optional memo can go here)
```

As a general practice, the account(s) being credited are visually indented.

There are also compound journal entries where there may be multiple accounts
on one side of a transaction.  In this case instead of making a whole other
line with another journal entry, we can combine the two entries together into a
`compound` journal entry, saving space and being much less wordy.

At this level you don't need to worry about accruals or adjustments or anything
fancy, you are just monitoring the transactions as they happen and keeping note
of where and how much money is changing hands.  All of those complications
happen later on in the process and are not necessary for the initial trial
balance.

For most common non-professional scenarios like keeping a monthly personal
budget, this is more than sufficient.

# Building for Local Development
make sure you source your venv

install the dev_requirements.txt file and then run
`$ python -m build`

This will create the dist/ directory which you can then install with pip
`$ pip install -e .`