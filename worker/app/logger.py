import logging


log = logging.getLogger("PROCESSOR")


def configure_logging(log_level=logging.INFO):
    global log

    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s')
    log.setLevel(log_level)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    log.addHandler(console_handler)

    return log