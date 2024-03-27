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
from banking_utils import Individual, Account, Transaction

# Constants
TEST_DATA = 'test_db_data.json'

load_dotenv()
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
HOST = os.getenv("HOST")
PORT = os.getenv("PORT")
DB_NAME = "banking"
INIT_CONNECT_STR = f"mysql+mysqlconnector://{DB_USER}:{DB_PASSWORD}@{HOST}:{PORT}"
DB_CONNECT_STR = INIT_CONNECT_STR+f"/{DB_NAME}"

# Setup Database
engine = create_engine(INIT_CONNECT_STR)

with engine.connect() as conn:
    conn.execute(f"DROP DATABASE IF EXISTS {DB_NAME}")
    conn.execute(f"CREATE DATABASE {DB_NAME}")

engine.dispose()

# Setup tables and objects
engine = create_engine(DB_CONNECT_STR)

Base = declarative_base()

# Create tables
Individual.__table__.create(engine)
Account.__table__.create(engine)
Transaction.__table__.create(engine)
Session = sessionmaker(engine)

# Populate test data
with Session() as session:
    with open(TEST_DATA) as f:
        test_dat = json.load(f)

    # Add individuals
    test_indvdls = [Individual(**kwargs) for kwargs in test_dat.values()]

    for indvdl in test_indvdls:
        session.add(indvdl)

    session.commit()

    # Add accounts
    test_accounts = [(Account.make_checking_account(
        indvdl_id=indvdl.indvdl_id, starting_balance=1000),
        Account.make_savings_account(
        indvdl_id=indvdl.indvdl_id, starting_balance=1000),
        Account.make_credit_card_account(
        indvdl_id=indvdl.indvdl_id, starting_balance=1000)
    ) for indvdl in test_indvdls]

    for account_group in test_accounts:
        session.add(account_group[0])
        session.add(account_group[1])
        session.add(account_group[2])

    session.commit()

    # Add transactions
    test_transactions = [acct_groups[0].debit(
        100) for acct_groups in test_accounts]
    for transaction in test_transactions:
        session.add(transaction)

    session.commit()

engine.dispose()
