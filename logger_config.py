import logging

def configure_logger():
    """Configure and return a logger instance."""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    # Add file handler for trade logs
    trade_file_handler = logging.FileHandler('trade_logs.log')
    trade_file_handler.setLevel(logging.INFO)
    trade_file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

    logger = logging.getLogger()
    logger.addHandler(trade_file_handler)

    return logger, trade_file_handler