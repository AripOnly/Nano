# app/utils/logger.py

from loguru import logger
from datetime import datetime
import os
from app.config import config


def setup_logger():
    logger.remove()

    if config.LOG_ENABLED:
        # Buat folder logs
        log_dir = "app/logs"
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        # File log per hari
        current_date = datetime.now().strftime("%d_%m_%Y")
        log_file = f"{log_dir}/system_log-{current_date}.log"

        logger.add(
            lambda msg: print(msg, end=""),
            level="DEBUG",
            format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
            colorize=True,
        )

        # Handler untuk file
        logger.add(
            log_file,
            level="DEBUG",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}",
            rotation="00:00",
        )

    return logger


# Buat instance logger
log = setup_logger()
