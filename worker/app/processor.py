import datetime
import random
import pika
from pika.adapters.blocking_connection import BlockingChannel
import json
import mysql.connector
import time
from decimal import Decimal
import config
from logger import log
from exceptions import ProcessingError, RejectTransactionError, RetryTransactionError, WalletAuthorizationError
from transaction import Transaction


class TransactionProcessor:
    def __init__(self, worker_id, sub_queue=None, err_queue=None):
        self.worker_id = worker_id
        self.connection = None
        self.channel = None
        self.subscribe_queue = sub_queue or config.RABBITMQ_TRASACTIONS_QUEUE
        self.error_queue = err_queue or config.RABBITMQ_ERROR_QUEUE

    def authorize_transaction(self, tr:Transaction, cursor):
        # Check if the transaction already registered (deduplication)
        cursor.execute("SELECT transaction_id FROM transactions WHERE transaction_id = %s", (tr.transaction_id,))
        return cursor.fetchone()

    def authorize_wallet(self, tr:Transaction, cursor):
        """
        Checks banalnce and "simulates" the transaction, returning the resulting balance
        """

        # Get current account balance
        cursor.execute("SELECT balance FROM accounts WHERE account_id = %s", (tr.account_id,))
        result = cursor.fetchone()
        if result is None:
            log.debug(f"Account {tr.account_id} not found.")
            raise ProcessingError(f"Account {tr.account_id} not found. FRAUD?", transaction_id=tr.transaction_id)
        current_balance = Decimal(str(result[0])) 
    
        # Update account balance depending on transaction
        if tr.transaction_type == "deposit":
            new_balance = current_balance + tr.amount
        elif tr.transaction_type == "withdrawal":
            if current_balance < tr.amount:
                log.debug(f"Insufficient funds for withdrawal {tr.transaction_id}")
                raise WalletAuthorizationError("Insufficient funds for withdrawal", transaction_id=tr.transaction_id)
            new_balance = current_balance - tr.amount
        elif tr.transaction_type == "payment":
            if current_balance < tr.amount:
                log.debug(f"Insufficient funds for payment {tr.transaction_id}")
                raise WalletAuthorizationError("Insufficient funds for payment", transaction_id=tr.transaction_id)
            new_balance = current_balance - tr.amount
        else:
            log.error(f"Invalid transaction type: {tr.transaction_type}")
            raise ProcessingError(f"Invalid transaction type: {tr.transaction_type}", transaction_id=tr.transaction_id)
        return new_balance

    def apply_transaction(self, tr:Transaction, new_balance, cursor):
        # Update balance
        cursor.execute("UPDATE accounts SET balance = %s WHERE account_id = %s", (new_balance, tr.account_id))

        # Add transaction
        sql = "INSERT INTO transactions (transaction_id, account_id, transaction_type, amount, timestamp, status, details) VALUES (%s, %s, %s, %s, %s, %s, %s)"
        val = (tr.transaction_id, tr.account_id, tr.transaction_type, tr.amount, tr.timestamp, "completed", tr.details)
        cursor.execute(sql, val)

    def process_transaction(self, tr:Transaction):
        """
        Executes the transaction Processing workflow. Should only return normally if the transaction is successful.
        Otherwise it will raise a TransactionError exception (child):

        ProcessingError - if an error occurred during processing.
        WalletAuthorizationError - Error with balance, or authorization
        ... etc
        """

        with mysql.connector.connect(
            host=config.MYSQL_HOST,
            user=config.MYSQL_USER,
            password=config.MYSQL_PASSWORD,
            database=config.MYSQL_DATABASE
        ) as mydb:
            with mydb.cursor() as mycursor:
                # Simulate some random long work
                time.sleep(random.randint(0, config.PROCESSOR_PROCESS_TIME))

                # Authorization
                if self.authorize_transaction(tr, mycursor):
                    log.debug(f"Transaction {tr.transaction_id} already processed. Skipping.")
                    return

                new_balance = self.authorize_wallet(tr, mycursor)

                # This part at least, should allow rollback in case of error
                try: 
                    self.apply_transaction(tr, new_balance, mycursor)
                    mydb.commit()
                except Exception as e:  # Should NOT capture Exception, this is for simplicity.
                    mydb.rollback()  # Rollback in case of any error
                    log.error(f"Error processing transaction {tr.transaction_id}, rolling back: {e}", exc_info=True)
                    raise


    def transaction_handler(self, ch:BlockingChannel, method, properties, body):
        """
        Message handler, called for any new message. Handles further actions with RMQ.

        Depending on the result of process_transaction, either:
            ack's the message (Reject)
            re-enqueues (Retry)
            or sends it to the error queue (Error).
        """
        try:
            tr = Transaction.from_dict(json.loads(body))
            # TODO: Check format of transaction data
            log.info(f"TRANSACTION:{tr.transaction_id} START")

            self.process_transaction(tr)

            # Success, if no exception so far
            ch.basic_ack(delivery_tag=method.delivery_tag)
            log.info(f"TRANSACTION:{tr.transaction_id} SUCCESS")

        except ProcessingError as e: 
            log.warning(f"TRANSACTION:{tr.transaction_id}, ERROR {e}")
            self.send_to_error_queue(ch, method, body, e)
            ch.basic_ack(method.delivery_tag)
        except RejectTransactionError as e: 
            log.warning(f"TRANSACTION:{tr.transaction_id}, REJECT reason {e.message}")
            ch.basic_ack(method.delivery_tag)
        except RetryTransactionError as e: 
            log.warning(f"TRANSACTION:{tr.transaction_id} RETRY (requeue).")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
        except Exception as e:
            log.error(f"Unexpected Error: {e}", exc_info=True)
            self.send_to_error_queue(ch, method, body, e)
            ch.basic_ack(method.delivery_tag)

    def send_to_error_queue(self, ch:BlockingChannel, method, body, error: ProcessingError):
        """Sends the message to the error queue along with the error message."""
        try:
            # Add the error message to the message body
            error_message = str(error)
            error_data = {
                "original_message": json.loads(body),
                "error_message": error_message,
                "worker_id": self.worker_id,
                "timestamp": str(datetime.datetime.now())
            }

            ch.queue_declare(queue=self.error_queue)
            ch.basic_publish(
                exchange='',
                routing_key=self.error_queue,
                body=json.dumps(error_data),
                properties=pika.BasicProperties(
                    delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE
                )
            )
            log.debug(f"Message sent to error queue: {self.error_queue}")

        except Exception as e:
            log.error(f"Error sending message to error queue: {e}", exc_info=True)

    def start_consuming(self):
        log.info(f"Connecting to RabbitMQ at {config.RABBITMQ_HOST}, user:{config.RABBITMQ_USER}")
        try:
            self.connection = pika.BlockingConnection(pika.ConnectionParameters(host=config.RABBITMQ_HOST))
            self.channel = self.connection.channel()
            self.channel.queue_declare(queue=config.RABBITMQ_TRASACTIONS_QUEUE)
            self.channel.basic_consume(queue=config.RABBITMQ_TRASACTIONS_QUEUE, on_message_callback=self.transaction_handler)
            log.info(f"Listening to {self.subscribe_queue}... To exit press CTRL+C")
            self.channel.start_consuming()
        except Exception as e:
            log.error(f"Error connecting to RabbitMQ or consuming messages: {e}", exc_info=True)
        finally:
            if self.connection and self.connection.is_open:
                self.connection.close()

