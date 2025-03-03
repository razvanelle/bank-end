from contextlib import contextmanager
import mysql.connector
import mysql.connector.abstracts
import pika
import json
import config
import logging
import fastapi


"""
This is a simulation module for the "clients" connectors. This was done for simplicity.

The good practice is to have cleints as separate classes, with persistent connections,
connection management, exceptions handling, etc. 
"""

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)

# RabbbitMQ
def rmq_publish_transaction(transaction_data: dict):
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters(host=config.RABBITMQ_HOST))
        channel = connection.channel()
        channel.queue_declare(queue=config.RABBITMQ_TRASACTIONS_QUEUE)
        channel.basic_publish(
            exchange='', routing_key=config.RABBITMQ_TRASACTIONS_QUEUE, body=json.dumps(transaction_data)
        )
        log.info(f"Published transaction: {transaction_data['transaction_id']}")
    except Exception as e:  # TODO: Specific exceptions
        log.error(f"Error publishing: {e}")
    finally:
        if connection:
            connection.close()

# Using a ctx manager as client to handle SQL connectivity, just for simplicity.
@contextmanager
def mysql_client(query:str, params:tuple = None):
    try:
        mydb = mysql.connector.connect(
            host=config.MYSQL_HOST,
            user=config.MYSQL_USER,
            password=config.MYSQL_PASSWORD,
            database=config.MYSQL_DATABASE
        )
        mycursor = mydb.cursor()

        mycursor.execute(operation=query, params=params)
        yield mycursor  # Pass cursor to allow getting results for one or more rows

    except mysql.connector.Error as e:
        log.error(f"Database error: {e}")
        raise fastapi.HTTPException(status_code=500, detail="Database error")
    except Exception as e:  # TODO: Specific exceptions
        log.error(f"An unexpected error: {e}")
        raise fastapi.HTTPException(status_code=500, detail="Internal server error")
    finally:
        if mycursor: 
            mycursor.close()
        mydb.close()
