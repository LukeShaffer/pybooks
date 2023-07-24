# Purpose
This is meant to be a simple programatic ledger for use in basic bookkeeping
/ accounting applications.

There will be some basic accounting knowledge needed to understand the
terminology here, but I will try and provide a primer in the README.

# Project Layout
TBD

# Accounting Concepts

## Credits and Debits
In order for accounting to categorize transactions, it gives them a "direction"
either called a credit or a debit.

Roughly speaking, for any account, a credit is an incoming value and a debit
is an outgoing value.  Whether this is a "good" or "bad" thing depends on the
type of account. 

- Credit: Source / Value Inflow
    - Abbreviation Cr
- Debit: Destination / Value Outflow
    - Abbreviation Dr

Without getting too deep (the next section is Accounts),
there can be all sorts of accounts, but let's take two simple ones for an
example: Cash and Loan (Debt).

A credit to your Cash Account would mean that you got money somewhere else and
deposited it in your bank account.

A debit to your Cash Account would mean that you took money from your bank
account and moved it somewhere else.

A credit to your Loan Account would mean that your debt has increased, and you
now have more liabilities (debt) than before.

A debit to your Loan Account would mean that you have taken money from
somewhere else and used it to resolve an existing debt.


## Account
`A place where we can record, sort, and store all transactions that affect a related group of items.`

Forget everything you know about the word "Account" becuase in the context of
accounting it takes on a slightly different meaning.  An account transcends
the normal connotation of a bank or brokerage account which is basically a
location for money to travel to or from, to a non-physical label that we apply
to a group of related transactions simply for organizational purposes.

An "Account" here could transcend several "normal" accounts; what constitutes
an account in accounting is that money is flowing in or out for some related
purpose.

Accounts are generally conceptualized as either an Asset or a Liability for
planning purposes.  The core "type" of account helps to determine whether line
items are placed into the debit or credit sides of an account.


Further, Accounts are usually grouped into the same common categories for most
businesses in order to standardize things from one accountant to the next.
You can see a list of common account names from quickbooks [here](https://qbkaccounting.com/chart-accounts-complete-list-descriptions/)

For example, here are some sample accounts you might find in the wild:

- Cash Account
    - The total net sum of cash at a person or business's disposal.  You can see
    that if the entity had multiple cash bank accounts how these all fall under
    the same accounting "Account" umbrella while being separate accounts
    legally.

- Revenue
    - Every time a business makes a sale, it is accounted for as stemming from
    the Revenue Account.  Otherwise it could have been a donation, found $10
    on the ground, whatever.  Closly linked to the Cash Account.

- Loans Payable
    - If a business takes out a loan from a bank, this is the account that would
    receive the loan as a credit on their balance sheet.  This account contains
    every entity that has loaned the POV money.

- Equipment
    - This one takes some getting used to, but it refers to the intrinsic dollar
    amount that any equipment you own possesses.  For example, if you use
    $10,000 to buy a truck for work, that $10,000 doesn't just disappear off
    the books and go to money heaven, it gets credited from your cash account
    and debited as a line item into your equipment account.

- Supplies
    - Related to Equipment but more of a temporary / consumable category.
    Things like cleaning supplies and paper towels would go in here as a debit.

- Cost of Sales
    - Most easily conceptualized in the form of an example.  Say you own a
    cleaning company and cleaning things uses cleaning supplies like spray
    and towels.  You will credit your Supplies Account for any used supplies,
    and the corresponding amount will be debited here in the Cost of Sales
    Account.

- Accounts Payable
    - Related to Loans Payable, but applies in the situation where you have
    received some good or service instead of raw money. This helps accountants
    to know to look for the corresponding entry in the Equipment Account
    instead of the Cash Account.


Now that we are at the end, I should mention that Accounts can be split into
multiple accounts for a single purpose.  For example, the above "Cash" Account
could be split into a separate account for each individual bank account
controlled.

## Journal
At the most basic level of accounting is the journal.  The "Book of Original
Entry" as it is also known is simply a line by line log of transactions as they
take place (organized chronologically).  Each of these journal entries contains
the date, the parties or accounts involved, and the amount of money or value
that exchanged hands.

Here is an example journal entry for the sale of a $100 product:
```
Date        Account                         Debit   Credit     
============================================================
2020/01/25  Cash                            $100
                Revenue                              $100
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

## Ledger
Finally, we tie it all together with the one book to rule them all, the ledger.
A ledger is a master copy of all transactions that occur across all accounts.

Essentially, this is structured like a journal, with a list of line items and
whether they are net credits or debits, but instead of being listed by date,
they are consolidated per account and show the net flow over the period of
time being accounted for.

The General Ledger is the name for the one top-level master ledger that contains
the total net inflows and outflows for the entity. It is either composed of
line items listing individual account debits / credits, or of consolidated
subledgers that wrap up a set of related transactions.

### Ledgers vs SubLedgers
You can have numerous levels of accounting separation.  If one of the areas of
account have very many Accounts and makes too much noise in the General Ledger,
you can bundle a group of accounts into a subledger that will contain all of
the individual transactions and can then be included in the General Ledger as
a single line item. 

# Building for Local Development
make sure you source your venv

install the dev_requirements.txt file and then run
`$ python -m build`

This will create the dist/ directory which you can then install with pip
`$ pip install -e .`