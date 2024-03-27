from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from banking_utils import Individual, Account, Transaction, Employee
from dotenv import load_dotenv, dotenv_values
import os
from getpass import getpass
from uuid import uuid4
from hashlib import sha256
import cmd
import pandas as pd
import logging


class CredentialHandler:
    """Holds a collection of methods for user credential validation to use the banking app.

    Attributes
    ----------
    session : sqlalchemy Session
        SQLAlchemy session for interfacing with database

    context : sqlalchemy query object
        Holds results of queries made using sqlalchemy when retrieving users/accountts

    logger : Logger
        Logging object for the class

    Methods
    -------

    start_screen:
        Presents the user with options to for customer login, customer account creation, and employee login

    customer_login:
        Prompts and credential validation for an existing customer

    employee_login:
        Prompts and credential validation for an employee

    new_user:
        Prompts to collect needed data to create a new customer in the Individual table and set up
        checking, savings, and credit card accounts

    """

    def __init__(self, session, logger):
        self.session = session
        self.context = None
        self.logger = logger
        self.logger.info('credential handler started')

    def start_screen(self):
        print('Welcome to the Banking Customer Portal! Please choose an option.')
        print('')
        print('1: Existing customer login')
        print('2: New customer setup')
        print('3: Employee login')
        print('4: Exit')
        print('')

        cli = []

        while True:
            option = input('Choose an option: ')
            if option == '1':
                if self.customer_login():
                    cli = CustomerCLI(self.session, self.logger, self.context)
                    break
            elif option == '2':
                if self.new_user():
                    break
            elif option == '3':
                if self.employee_login():
                    cli = EmployeeCLI(self.session, self.logger, self.context)
                    break
            elif option == '4':
                exit()
            else:
                print('Please enter a valid option.')

        os.system('cls')
        cli.cmdloop()

    def _get_context(self, indvdl_obj, indvdl_id_num):
        accounts = self.session.query(Account).filter(
            Account.indvdl_id == indvdl_id_num)
        output = {account.account_type.lower(
        ).replace(' ', ''): account for account in accounts}
        output['user'] = indvdl_obj
        return output

    def customer_login(self):
        username = input('Enter Username: ')
        password = sha256(
            getpass('Enter Password: ').encode('utf-8')).hexdigest()
        results = self.session.query(Individual).filter(
            (Individual.user_name == username) & (Individual._password == password))
        if results.count() == 0:
            print(
                'User not found/invalid credentials. Please try again or complete new customer setup.')
            self.logger.info('customer login attempt failed')
            return False
        else:
            self.context = self._get_context(results[0], results[0].indvdl_id)
            self.logger.info('customer login attempt success')
            return True

    def employee_login(self):
        username = input('Enter Username: ')
        password = sha256(
            getpass('Enter Password: ').encode('utf-8')).hexdigest()
        results = self.session.query(Employee).filter(
            (Employee.user_name == username) & (Employee._password == password))
        if results.count() == 0:
            print('Employee not found/invalid credentials. Please try again.')
            self.logger.info('employee login attempt failed')
            return False
        else:
            self.context = results[0]
            self.logger.info('employee login attempt success')
            return True

    def new_user(self):
        try:
            username = input('Create Username: ')
            password = getpass('Create Password: ')
            first_name = input('First name: ')
            last_name = input('Last Name: ')
            age = int(input('Age: '))
            address = input('Address: ')
            new_user = Individual(user_name=username, password=password,
                                  first_name=first_name, last_name=last_name, age_num=age, address=address)
            self.session.add(new_user)
            self.session.commit()
            checking, savings, credit = new_user.make_basic_accounts()
            self.session.add(checking)
            self.session.add(savings)
            self.session.add(credit)
            self.session.commit()
            self.logger.info('new customer creation success')
            print('Account created! Please login using your new credentials.')
        except Exception as e:
            self.logger.info('new customer creation failed')
            print(e)
            print(
                'Input error, please ensure all responses are filled and that you are 18 years of age or older.')


class CustomerCLI(cmd.Cmd):
    """Handles loop for Customer Interface.

    Attributes
    ----------
    session : sqlalchemy Session
        SQLAlchemy session for interfacing with database

    context : sqlalchemy query object
        Holds results of queries made using sqlalchemy when retrieving users/accountts

    logger : Logger
        Logging object for the class

    Methods
    -------

    preloop:
        Presents user with greeting and calls do_help() method.

    do_statement(line : str):
        Allows querying of a user's accounts.

    do_deposit(line : str)
        Allows for depositing of funds to an account

    do_withdraw(line : str)
        Allows for withdraw of funds from an account

    do_quit:
        Quits application
    """

    prompt = ">>"
    intro = "================================================================================="

    def __init__(self, session, logger, context):
        super().__init__()
        self.session = session
        self.context = context
        self.logger = logger
        self.logger.info('customer cli started')

    def preloop(self):
        print(
            f"Welcome to the customer dashboard. You are logged in as {self.context['user'].user_name}.\nPlease type help to show available options.")
        self.do_help(None)

    def do_statement(self, line):
        """Get the balance statement on your accounts."""
        print("Assets")
        print("-----------")
        print(f"Checking: {self.context['checking'].balance}")
        print(f"Savings: {self.context['savings'].balance}")
        print('\n')
        print("Liabilities")
        print("-----------")
        print(f"Credit Card: {self.context['creditcard'].balance}")
        print('')

    def do_deposit(self, line=None):
        """Deposit money to an account. Acceptable accounts are `checking`, `savings`, and `creditcard`.
        Use the format deposit <amount> <account>"""
        try:
            args = line.split()
            amount = int(args[0])
            account = args[1]
            transaction = self.context[account].debit(amount)
            self.session.add(transaction)
            self.session.commit()
            self.logger.info('customer deposit success')
            print('Transaction successful. \n')
        except Exception as e:
            self.logger.info('customer deposit failed')
            print(e)
            print(
                "Error. Please ensure you are depositing an integer amount > 0 to an acceptable account.\n")

    def do_withdraw(self, line):
        """Withdraw money from an account. Acceptable accounts are `checking`, `savings`, and `creditcard`.
        Use the format withdraw <amount> <account>"""
        try:
            args = line.split()
            amount = int(args[0])
            account = args[1]
            transaction = self.context[account].credit(amount)
            self.session.add(transaction)
            self.session.commit()
            self.logger.info('customer withdraw success')
            print('Transaction successful. \n')
        except Exception as e:
            self.logger.info('customer withdraw failed')
            print(e)
            print(
                'Error. Please ensure you are withdrawing an integer amount > 0 to an acceptable account.\n')

    def do_quit(self, line):
        """Exit the program."""
        self.logger.info('customer cli ended')
        return True


class EmployeeCLI(cmd.Cmd):
    """Handles loop for Employee Interface.

    Attributes
    ----------
    session : sqlalchemy Session
        SQLAlchemy session for interfacing with database

    context : sqlalchemy query object
        Holds results of queries made using sqlalchemy when retrieving users/accountts

    logger : Logger
        Logging object for the class

    Methods
    -------

    preloop:
        Presents user with greeting and calls do_help() method.

    do_search(line : str)
        Allows employee to search for all records matching input username.

    do_quit:
        Quits application
    """

    prompt = ">>"
    intro = "================================================================================="

    def __init__(self, session, logger, context):
        super().__init__()
        self.session = session
        self.context = context
        self.logger = logger
        self.logger.info('employee cli started')

    def preloop(self):
        print(
            f"Welcome to the employee dashboard. You are logged in as {self.context.user_name}.\nPlease type help to show available options.")
        self.do_help(None)

    def do_search(self, line=''):
        """Search for a member's details by username. Please use the following format.
        search <username>"""
        try:
            results = self.session.query(Individual).filter(
                (Individual.user_name == line))
            if results.count() > 0:
                df_results = pd.read_sql(
                    results.statement, results.session.bind)
                print('Found the following results:\n')
                print(df_results[['indvdl_id', 'user_name',
                      'first_name', 'last_name', 'address']])
                print('')
            else:
                print('No results found.\n')
        except:
            print('Error. Please ensure you have searched according to the directions.')

    def do_quit(self, line):
        """Exit the program."""
        self.logger.info('employee cli ended')
        return True
