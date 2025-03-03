# Case study - Transaction Processor


## Problem to solve:
Design and implement an asynchronous task queue system that simulates processing payment transactions. The system should illustrate the following workflow:
* Banking System Simulation: A simulated banking system receives notifications about payment transactions (e.g., deposits, withdrawals, or card payments). Each transaction should result in updating the balance of a wallet.
* User-Facing Accounting Updates: After processing a transaction, the system should send an update (e.g., a notification or a log entry) to a user-facing accounting system.


## Boundaries & Simplifications
* Command Line Execution: The solution must be runnable from the command line.
* Infrastructure Setup: Provide a simple Docker Compose script that sets up the necessary infrastructure (for example, a message queue like RabbitMQ, a simple web server, or any other components you deem necessary). This helps demonstrate that the system is capable of generating and processing messages.
* Message Processing Demonstration: Your system should visibly demonstrate the flow of messages (e.g., through logging or printed output) as transactions are generated, queued, and processed.
* AWS Integration (Optional): Although our startup primarily uses AWS and the Boto library is mentioned as a suggestion, it is not mandatory. You may implement the task queue using local services or other methods as long as the asynchronous processing concept is clearly demonstrated.


# Research
From the problem statement we deduct some ideas that we have to research a bit, before we dive any further. It is suggested that we have to implement a queue system, here are some topics to consider:
* What banking systems are about these days?
  * https://www.youtube.com/watch?v=FLS7NP8YMUQ (revolut)
  * ... Some other resources about banking systems
  * Never lose money!: Data safety, fault tolerance, replication(-), transactions, reconciliation(-), state management(?).
  * Important systems: Fraud prevention(~), identity(~), tracking/traceability(?)
  * Authorization flow: Card > Balance > Fraud checks
* Using queues in banking systems. Not sure if it's necessary, but was suggested by the case study...
* Key metrics and success factors.
* Scalability, Security, Asynchronous/parallel/non-blocking processing.
* Potential Issues and risks - to be studied: 
  * Order of operations is super important, we need a deterministic approach, i.e. operations can be influenced by balance, etc.
  * Managing balance in real time: Escrow???
  * Extensibility: allow adding new functionality, transaction states, in-between checks performed by other systems, out-of-system calls, etc.


# Functional requirements, components:

* Docker compose file, with all components, exposed services, etc
* Components:
  * DB:
    * Users (Accounts)
    * Transactions
      * Transactions should have states (Requested, Queued, ..., Completed) -> In this exercise, just saving the successful ones in DB -> "completed"
      * Transactions should have resolution: Success, Rejected, Error (not implemented)
  * Wallet service / API for:
    * Get all wallets (users)
    * Get balance for wallet
    * Get transactions for wallet:
      * Deposit
      * Withdrawal
      * Payment
  * Queue broker:
    * Transaction exchange -> In this exercise we do not implement complex routing
    * Transaction queue -> All valid transactions
    * Error -> We send here the suspicious or failed trasnactions
  * Worker thread(s):
    * Read from transaction queue. Execute based on transaction type:
      * Authorization (balance check)
      * Processing success (DB Update)
      * Send to error queue

* Work Flows (worker functionaloty):
  * POSITIVE: New transaction > Authorization > Update > Save to DB > Ack.
  * NEGATIVE / error handling: 
    * New transaction > Authorization Error (balance) > Ack + Send to Error queue
    * New transaction > Authorization > Update Error > Ack + Send to Error queue
    * New transaction > Authorization > System Error > NAck+ Retry
  * Workflows checks are done in SQL, and queues processing is signalled with custom Exceptions.

Requiremets:
* Visual demonstration of transaction processing is achieved with logs. It's clear which worker is processing transactions, and the result.
* We can review the final list of successful transactions in API.
* We can also find all error transactions in the Error queue.
* N/A Boto not used.

# Scalability, async, optimizations, other issues

## How do we achieve concurrency in this example
* Parallelization is achieved by scaling number of workers, in Docker, using replicas.
* Queues offer a way to balance (flatten) the load, giving us a steady stream for processing transactions.
* We can dynamically scale by adding/removing workers (replicas)

## Known issues with this approach
* Non-determinism: Order of operations is not guaranteed. Potential solutions: 
  * Use an "escrow" system, to make sure the transations are predictible, even if they are processed in random order.
  * Use a single queue per client, and process in a serial manner.
* We can only see successful transactions, we have no info on failed transactions.
* We should share some code between API and Worker. We could implement a shared lib that implements clients, configuration, data types.

## Potential optimizations
* In the same worker, we can do an async implementation and use multithreading, running more workers in the same process (to increase saturation of CPU if running in EC2).
* This implementation is not super data-safe, as we need to run operations across multiple systems "transactionally". They proper way to do it is:
  * Instantiate transaction to DB > Push from DB to queue, either using a trigger(?) or SQL Worker/ETL > Process message > send to processed queue > Send to DB
* We can use multiple queues with their specilized workers to execute various operations. Auth > Processing > Notification.


# How to use

## Starting in docker

Clone repo, cd into and run:

```
docker compose build
docker compose up
```

You might want to keep terminal open to view worker logs. Wait for about 10s for the workers to start.

... during bootstrap, some accounts should be prepopulated in MySql, from 100 to 105

After the workers connect, wither use API below, or run the CLI script to cenerate random transactions:

*optional: create virtual env and run:
```
pip install requests
python gen_transactions.py 10
```
This will add 10 transactions to the queue by calling the API.


## Access components:
**API client** can be accessed at: 
http://localhost:8000/docs

using the API you can create transactions and you can find for a user the list of completed transactions.

**Rabbit MQ Console** can be accessed at 
http://localhost:15672/

user: guest
pass: guest

**MySQL** available if you have a client on localhost:3306
jdbc:mysql://localhost:3306/payments?allowPublicKeyRetrieval=true&useSSL=False;

user: root
pass: mysecretpassword

## Scaling
Change the number of worker replicas, in docker-compose file. Default is 3, works ok for batches up to 50 transactions.

# Debug, run locally

You can run the API and the Worker in your local command line/environment. 
Just start only RabbitMQ and MySQL from docker compose, either comment worker and api or stop them from docker after booting up.

The default config values are setup already for local running for both apps.

create env, install requirements and run:
```
python app/main.py
```
...you can run multiple workers, as expected.