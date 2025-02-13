import logging
from datetime import datetime
from typing import Dict, Any

def setup_logging():
    """Configure error logging"""
    logging.basicConfig(
        level=logging.ERROR,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def log_error(error_info: Dict[str, Any]):
    """Log error information"""
    logger = logging.getLogger('error_boundary')
    logger.error(
        "Error occurred: %s\nComponent stack: %s",
        error_info.get('error'),
        error_info.get('info')
    )

def report_error(error_info: Dict[str, Any]):
    """Report error to monitoring service"""
    # TODO: Implement error reporting integration
    pass

# Initialize logging when module is loaded
setup_logging()
