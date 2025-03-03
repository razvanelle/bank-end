import logging
import os

# TRANSACTION PROCESSOR
PROCESSOR_START_DELAY = int(os.environ.get("START_DELAY", "5")) # seconds to wait
WORKER_ID = os.environ.get("WORKER_ID", "0") # ID from docker env, default to "0" for local clients
PROCESSOR_PROCESS_TIME = 3 # Artificial delay to simulate time taken by Transaction Processing
LOG_LEVEL = os.environ.get("LOG_LEVEL", logging.INFO)

# RMQ
RABBITMQ_HOST = os.environ.get("RABBITMQ_HOST", "localhost")
RABBITMQ_USER = os.environ.get("RABBITMQ_USER", "guest")
RABBITMQ_PASS = os.environ.get("RABBITMQ_PASS", "guest")
RABBITMQ_TRASACTIONS_QUEUE = os.environ.get("LISTEN_QUEUE", "transaction_queue")
RABBITMQ_ERROR_QUEUE = os.environ.get("ERROR_QUEUE", "error")

#MYSQL
MYSQL_HOST = os.environ.get("MYSQL_HOST", "localhost")
MYSQL_USER = os.environ.get("MYSQL_USER", "root")
MYSQL_PASSWORD = os.environ.get("MYSQL_PASSWORD", "mysecretpassword")
MYSQL_DATABASE = os.environ.get("MYSQL_DATABASE", "payments")
