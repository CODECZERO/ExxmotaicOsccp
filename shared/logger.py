import logging
import os
from logging.handlers import RotatingFileHandler

def setup_logging(service_name: str, log_level: str = "INFO"):
    """
    Configures logging to both console and a rotating file.
    Limits log files to 10MB each with 3 backups to prevent disk exhaustion.
    """
    level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Ensure the root logger is configured
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Prevent adding handlers multiple times if imported multiple times
    if root_logger.handlers:
        root_logger.handlers.clear()

    formatter = logging.Formatter("%(asctime)s  %(levelname)-8s  %(name)s  %(message)s")

    # 1. Console Output (for docker logs)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # 2. File Output (Rotating logs)
    # Get the logs directory from env var or default to './logs' in the project root
    log_dir = os.getenv("LOG_DIR", os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs"))
    os.makedirs(log_dir, exist_ok=True)
    
    log_file = os.path.join(log_dir, f"{service_name}.log")
    
    # Max size 10MB per file, keep 3 backup files (Total 40MB max per service)
    file_handler = RotatingFileHandler(log_file, maxBytes=10*1024*1024, backupCount=3)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    logging.info(f"Logging initialized for {service_name} (Level: {log_level})")
