"""Central logging setup for the Whitfield WMS backend.

Creates file handlers, applies a formatter, prevents duplicate propagation, and
exposes ``logger(__name__)`` for normal modules. Applications should write through
this helper rather than creating ad hoc log files.
"""
import logging
import os
import sys
from logging.handlers import RotatingFileHandler

_LOGS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
_LOG_FILE = os.path.join(_LOGS_DIR, "wms.log")

_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
_LEVEL = logging.DEBUG if os.getenv("DEBUG", "false").lower() == "true" else logging.INFO


def setup_process_logger(module_name: str = "wms") -> logging.Logger:
    """Configure and return the process-level logger.

    Creates the ``logs/`` directory and a rotating file handler on first call.
    Prevents duplicate handler propagation so module loggers do not double log.

    Args:
        module_name: Root logger name.

    Returns:
        logging.Logger: Configured root logger.
    """
    os.makedirs(_LOGS_DIR, exist_ok=True)
    root = logging.getLogger(module_name)
    if root.handlers:
        return root

    root.setLevel(_LEVEL)
    formatter = logging.Formatter(_FORMAT)

    file_handler = RotatingFileHandler(_LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=5, encoding="utf-8")
    file_handler.setFormatter(formatter)
    root.addHandler(file_handler)

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    root.addHandler(stream_handler)

    root.propagate = False
    return root


def logger(module_name: str) -> logging.Logger:
    """Return a logger for a given module.

    Args:
        module_name: Module name to attach to the log records.

    Returns:
        logging.Logger: Child logger under the ``wms`` root.
    """
    setup_process_logger()
    return logging.getLogger("wms").getChild(module_name)
