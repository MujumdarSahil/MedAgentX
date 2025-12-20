"""Utility functions for MedAgentX platform."""

try:
    from medagentx.utils.config import load_config  # type: ignore
except Exception:
    load_config = None

try:
    from medagentx.utils.logging import setup_logging  # type: ignore
except Exception:
    setup_logging = None

__all__ = [name for name in ("load_config", "setup_logging") if globals().get(name)]

