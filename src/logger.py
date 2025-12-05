import logging
import sys


def _init_logger() -> logging.Logger:
    # Set custom level names for pretty output
    logging.addLevelName(logging.DEBUG, "🔵 DEBUG")
    logging.addLevelName(logging.INFO, "🟢 INFO")
    logging.addLevelName(logging.WARNING, "🟡 WARNING")
    logging.addLevelName(logging.ERROR, "🔴 ERROR")
    logging.addLevelName(logging.CRITICAL, "🟣 CRITICAL")

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    handler = logging.StreamHandler(sys.stdout)

    formatter = logging.Formatter(
        fmt="[%(asctime)s] %(levelname)s - %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )

    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger


logger = _init_logger()
