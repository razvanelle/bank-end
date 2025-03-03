import time
from processor import TransactionProcessor
import config
from logger import configure_logging, log


if __name__ == "__main__":
    configure_logging(log_level=config.LOG_LEVEL)
    worker_id = config.WORKER_ID
    
    # This is a workaround for the worker to delay connection until rabbit boots up in docker. 
    # Normally we would have a retry mechanic...
    time.sleep(config.PROCESSOR_START_DELAY)

    try:
        worker = TransactionProcessor(worker_id)
        worker.start_consuming()
    except Exception as e:
        log.error(f"Processor failed to start: {e}", exc_info=True)
