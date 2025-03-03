import os
import random
import decimal
import time
import requests
import logging
import string
import sys

logging.basicConfig(level=logging.INFO, format='%(message)s')
log = logging.getLogger(__name__)

API_ENDPOINT = os.environ.get("API_ENDPOINT", "http://localhost:8000/transactions")
ACCOUNT_IDS = ["101", "102", "103", "104", "105", "106"]  # Adding 106 as fraud account.
TRANSACTION_TYPES = ["deposit", "withdrawal", "payment"]

def create_transaction():
    """Creates and sends a transaction to the API."""
    account_id = random.choice(ACCOUNT_IDS)
    transaction_type = random.choice(TRANSACTION_TYPES)
    amount = decimal.Decimal(f"{random.randint(1, 1000)}")
    details = ''.join(random.choice(string.ascii_letters) for _ in range(20))

    payload = {
        "account_id": account_id,
        "transaction_type": transaction_type,
        "amount": str(amount),
        "details": details,
    }

    response = requests.post(API_ENDPOINT, json=payload)
    response.raise_for_status() 
    log.info(f"Transaction created: {response.json()}") 


num_transactions = int(sys.argv.pop(1))

for i in range(num_transactions):
    create_transaction()
    time.sleep(0.01)

log.info(f"Generated {num_transactions} random transactions.")

