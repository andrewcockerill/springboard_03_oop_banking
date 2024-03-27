import sys
sys.path.append('../src')
from banking_utils import Individual, Account, Transaction

def test_accounts():
    test_account = Account.make_checking_account('test', 100)
    test_transaction_1 = test_account.debit(100)
    test_transaction_2 = test_account.credit(50)
    assert test_account.balance == 150
    assert test_transaction_1.amount == 100
    assert test_transaction_2.amount == 50
