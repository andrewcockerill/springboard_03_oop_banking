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
    __tablename__ = 'accounts'

    _account_id = Column('account_id', String(36), primary_key=True)
    indvdl_id = Column('indvdl_id', String(
        36), ForeignKey('individuals.indvdl_id'))
    account_type = Column('account_type', String(255))
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
