from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uuid
import datetime
from decimal import Decimal
import logging
from typing import List
import clients

app = FastAPI()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)

# Data types
class TransactionRequest(BaseModel):
    account_id: str
    transaction_type: str  # "deposit", "withdrawal", "payment"
    amount: Decimal
    details: str = ""

class AccountResponse(BaseModel):
    account_id: str
    balance: Decimal
    transaction_count: int

class AccountListResponse(BaseModel):
    accounts: List[AccountResponse]

class AccountCreateRequest(BaseModel):
    account_id: str
    initial_balance: Decimal = Decimal("0.00")

@app.post("/accounts", status_code=201)
async def create_account(acc: AccountCreateRequest):
    """Creates a new account."""
    query = "INSERT INTO accounts (account_id, balance) VALUES (%s, %s)"
    try:
        clients.mysql_client(query, (acc.account_id, acc.initial_balance))
    except Exception as e:
        log.error(f"Error creating account with {acc.account_id}")
        raise HTTPException(status_code=500, detail=f"Error while creating account with id {acc.account_id}")
    
    log.info(f"Created account: {acc.account_id} with initial balance: {acc.initial_balance}")
    return {"message": f"Account created with id {acc.account_id}"}

@app.get("/accounts", response_model=AccountListResponse)
async def get_all_accounts():
    query = """
        SELECT 
            a.account_id, 
            a.balance, 
            COUNT(t.transaction_id) AS transaction_count
        FROM accounts a
        LEFT JOIN transactions t ON a.account_id = t.account_id
        GROUP BY a.account_id, a.balance
    """

    with clients.mysql_client(query, None) as cursor:
        results = cursor.fetchall()

    account_list = []
    for account_id, balance, transaction_count in results:
        account_list.append(
            AccountResponse(account_id=account_id, balance=float(balance), transaction_count=transaction_count)
        )

    log.info("Got all accounts + balance and transactions")
    return AccountListResponse(accounts=account_list)


@app.post("/transactions")
async def create_transaction(transaction_request: TransactionRequest):
    transaction_id = str(uuid.uuid4())
    transaction_data = {
        "transaction_id": transaction_id,
        "account_id": transaction_request.account_id,
        "transaction_type": transaction_request.transaction_type,
        "amount": float(transaction_request.amount),
        "details": transaction_request.details,
        "timestamp": datetime.datetime.now().isoformat()
    }

    clients.rmq_publish_transaction(transaction_data)
    return {"transaction_id": transaction_id, "message": "Transaction published"}


@app.get("/accounts/{account_id}/balance")
async def get_balance(account_id: str):
    with clients.mysql_client("SELECT balance FROM accounts WHERE account_id = %s", (account_id,)) as cursor:
        result = cursor.fetchone()

    if result is None:
        raise HTTPException(status_code=404, detail="Account not found")

    balance = float(result[0])
    log.info(f"Retrieved balance for account: {account_id}")
    return {"account_id": account_id, "balance": balance}


@app.get("/accounts/{account_id}/transactions")
async def get_transactions(account_id: str):
    with clients.mysql_client(
        "SELECT transaction_id, amount, transaction_type, status FROM transactions WHERE account_id = %s",
        (account_id,),
    ) as cursor:
        results = cursor.fetchall()

    if not results:
        raise HTTPException(status_code=404, detail="No transactions found")

    transactions = []
    for row in results:
        transactions.append({
            "transaction_id": row[0],
            "amount": float(row[1]),
            "type": row[2],
            "status": row[3]
        })
    log.info(f"Got transactions for account: {account_id}")
    return transactions
