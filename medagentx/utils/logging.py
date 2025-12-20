"""
Logging utilities.
"""

import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional


def setup_logging(
    level: str = "INFO",
    log_file: Optional[str] = None,
    format_string: Optional[str] = None,
) -> None:
    """
    Set up logging configuration.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_file: Optional log file path
        format_string: Optional format string
    """
    log_level = getattr(logging, level.upper(), logging.INFO)
    
    if format_string is None:
        format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    formatter = logging.Formatter(format_string)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(log_level)
    
    # File handler (if specified)
    handlers = [console_handler]
    
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        file_handler.setLevel(log_level)
        handlers.append(file_handler)
    
    # Configure root logger
    logging.basicConfig(
        level=log_level,
        handlers=handlers,
        force=True,
    )


def evidence_present(trace: List[Dict[str, Any]]) -> bool:
    return any(event.get("evidence") for event in trace)


def confidence_threshold_passed(trace: List[Dict[str, Any]], threshold: float = 0.5) -> bool:
    confidences = [event.get("confidence") for event in trace if event.get("confidence") is not None]
    return bool(confidences) and all(conf >= threshold for conf in confidences)


def governance_triggered(trace: List[Dict[str, Any]]) -> bool:
    return any(event.get("agent_name") == "governance" for event in trace)


def evaluate_trace(trace: List[Dict[str, Any]], threshold: float = 0.5) -> Dict[str, Any]:
    return {
        "evidence_present": evidence_present(trace),
        "confidence_threshold_passed": confidence_threshold_passed(trace, threshold),
        "governance_triggered": governance_triggered(trace),
    }

