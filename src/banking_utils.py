from sqlalchemy import create_engine, ForeignKey, Column, String, Integer, CHAR
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.mysql import TINYINT, DECIMAL, TIMESTAMP
from uuid import uuid4
from hashlib import sha256
import json
from datetime import datetime
from dotenv import load_dotenv, dotenv_values
import os

Base = declarative_base()


class Individual(Base):
    """Declarative base class describing unique individuals in the banking system. This will correspond to
    and `individuals` table in the banking database.

    Parameters
    ----------

    indvdl_id : str
        Unique identifier for an individual. If not specified, will create a unique UUID. This is the primary key
        for the `individuals` table.

    user_name : str
        Login name for the individual.

    password : str
        Password for the user. Input will be encrypted via SHA-256.

    first_name : str
        Individual's first name

    last_name : str
        Individual's last name

    age_num : int
        Individual's age

    address : str
        Individual's address

    Methods
    -------

    make_basic_accounts(self):
        Generates three default Account objects. For the scope of this project, this will return a checking, savings, and credit card
        account respectively, starting at a balance of 0.

    """

    __tablename__ = 'individuals'

    _indvdl_id = Column('indvdl_id', String(36), primary_key=True)
    user_name = Column('user_name', String(255), unique=True)
    _password = Column('password', String(64))
    first_name = Column('first_name', String(255))
    last_name = Column('last_name', String(255))
    _age_num = Column('age_num', Integer)
    address = Column('address', String(255))

    def __init__(self, user_name, password, first_name, last_name, age_num, address, indvdl_id=None):
        self._indvdl_id = str(uuid4()) if indvdl_id is None else indvdl_id
        self.user_name = user_name
        self.password = password
        self.first_name = first_name
        self.last_name = last_name
        self.age_num = age_num
        self.address = address

    @property
    def indvdl_id(self):
        return self._indvdl_id

    @property
    def password(self):
        return self._password

    @password.setter
    def password(self, pwd):
        self._password = sha256(pwd.encode('utf-8')).hexdigest()

    @property
    def age_num(self):
        return self._age_num

    @age_num.setter
    def age_num(self, new_age):
        if new_age < 18:
            raise ValueError('Must be 18 or older to have an account')
        self._age_num = new_age

    def make_basic_accounts(self):
        checking = Account.make_checking_account(self.indvdl_id, 0)
        savings = Account.make_savings_account(self.indvdl_id, 0)
        credit_card = Account.make_credit_card_account(self.indvdl_id, 0)
        return (checking, savings, credit_card)


class Account(Base):
    """Declarative base class describing unique accounts in the banking system. This will correspond to
    and `accounts` table in the banking database.

    Parameters
    ----------

    account_id : str
        Unique identifier for an account. If not specified, will create a unique UUID. This is the primary key
        for the `accounts` table.

    indvdl_id : str
        This corresponds to the `individuals.indvdl_id` that is the owner of the account. This will be a foreign
        key in the `accounts` table.

    account_type : str
        Account type for the individual ('Checking', 'Savings', 'Credit Card')

    balance : int
        Balance on the account, must be >= 0.

    liability_fg : int
        Must be 0 or 1. 0=non-liability, 1=liability
        A liability account will have its balance increased in credit transactions and decreased in debit transactions.
        A non-liability account will have its balance decreased in credit transactions and increased in debit transactions.

    interest_rate : float
        Interest rate on the account if applicable.

    Methods
    -------

    debit(amt : int):
        Returns a Transaction object for the given cash flow on the account.
        amt must be an integer >=0. The associated account will be debited for this amount.

    credit(amt : int):
        Returns a Transaction object for the given cash flow on the account.
        amt must be an integer >=0. The associated account will be credited for this amount.

    """

    __tablename__ = 'accounts'

    _account_id = Column('account_id', String(36), primary_key=True)
    indvdl_id = Column('indvdl_id', String(
        36), ForeignKey('individuals.indvdl_id'))
    _account_type = Column('account_type', String(255))
    _balance = Column('balance', Integer)
    _liability_fg = Column('liability_fg', TINYINT)
    _interest_rate = Column('interest_rate', DECIMAL(10, 2))

    def __init__(self, indvdl_id, account_type, balance, liability_fg, interest_rate, account_id=None):
        self._account_id = str(uuid4()) if account_id is None else account_id
        self.indvdl_id = indvdl_id
        self.account_type = account_type
        self.balance = balance
        self.liability_fg = liability_fg
        self.interest_rate = interest_rate

    @property
    def account_id(self):
        return self._account_id

    @property
    def account_type(self):
        return self._account_type

    @account_type.setter
    def account_type(self, new_type):
        if new_type not in ['Checking', 'Savings', 'Credit Card']:
            raise ValueError(
                'Accounts can only be `Checking`, `Savings`, or `Credit Card`')
        self._account_type = new_type

    @property
    def balance(self):
        return self._balance

    @balance.setter
    def balance(self, new_balance):
        if new_balance < 0:
            raise ValueError('Negative balance')
        self._balance = new_balance

    @property
    def liability_fg(self):
        return self._liability_fg

    @liability_fg.setter
    def liability_fg(self, fg):
        if fg not in [0, 1]:
            raise ValueError('Liability must be 0 or 1')
        self._liability_fg = fg

    @property
    def interest_rate(self):
        return self._interest_rate

    @interest_rate.setter
    def interest_rate(self, rate):
        if rate < 0:
            raise ValueError('Interest Rate should be >= 0')
        self._interest_rate = rate

    def debit(self, amt):
        if amt < 0:
            raise ValueError('Cash flows must be positive')
        self.balance += (1-2*self.liability_fg)*amt
        return Transaction(account_id=self.account_id, transaction_type='DEBIT', amount=amt)

    def credit(self, amt):
        if amt < 0:
            raise ValueError('Cash flows must be positive')
        self.balance -= (1-2*self.liability_fg)*amt
        return Transaction(account_id=self.account_id, transaction_type='CREDIT', amount=amt)

    @classmethod
    def make_checking_account(cls, indvdl_id, starting_balance):
        return cls(indvdl_id=indvdl_id, account_type='Checking', balance=starting_balance, liability_fg=0, interest_rate=0)

    @classmethod
    def make_savings_account(cls, indvdl_id, starting_balance):
        return cls(indvdl_id=indvdl_id, account_type='Savings', balance=starting_balance, liability_fg=0, interest_rate=0.05)

    @classmethod
    def make_credit_card_account(cls, indvdl_id, starting_balance):
        return cls(indvdl_id=indvdl_id, account_type='Credit Card', balance=starting_balance, liability_fg=1, interest_rate=0.025)


class Transaction(Base):
    """Declarative base class describing unique transactions in the banking system. This will correspond to
    and `transactions` table in the banking database.

    Parameters
    ----------

    transaction_id : str
        Unique identifier for a transaction. If not specified, will create a unique UUID. This is the primary key
        for the `transactions` table.

    account_id : str
        This corresponds to the `accounts.account_id` that is the owner of the account. This will be a foreign
        key in the `transactions` table.

    transaction_type : str
        This is the transaction type (credit or debit)

    amount : int
        This is the amount of the transaction cash flow

    transaction_timestamp : datetime.datetime
        This is the timestamp of the transaction (when the object was created)

    """

    __tablename__ = 'transactions'

    _transaction_id = Column('transaction_id', String(36), primary_key=True)
    _account_id = Column('account_id', String(
        36), ForeignKey('accounts.account_id'))
    _transaction_type = Column('transaction_type', String(255))
    _amount = Column('amount', Integer)
    _transaction_timestamp = Column(
        'transaction_timestamp', TIMESTAMP(timezone=False))

    def __init__(self, account_id, transaction_type, amount, transaction_id=None, transaction_timestamp=None):
        self._transaction_id = str(
            uuid4()) if transaction_id is None else transaction_id
        self._account_id = account_id
        self._transaction_type = transaction_type
        self._amount = amount
        self._transaction_timestamp = datetime.now(
        ) if transaction_timestamp is None else transaction_timestamp

    @property
    def transaction_id(self):
        return self._transaction_id

    @property
    def account_id(self):
        return self._account_id

    @property
    def transaction_type(self):
        return self._transaction_type

    @property
    def amount(self):
        return self._amount

    @property
    def transaction_timestamp(self):
        return self._transaction_timestamp
