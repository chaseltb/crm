"""
utils/config.py — Centralised config loader for EtherealCRM.

Every page and module should import from here instead of duplicating load/save logic.
The CRM_CONFIG env var lets demo instances point at a different config file without
touching any source code — set it in the launch script (run_heritage.bat, etc.).
"""

import os
import yaml

# Resolve once at import time.  CRM_CONFIG env var wins; otherwise fall back to
# config.yaml in the project root (one level above this utils/ directory).
CONFIG_PATH: str = os.environ.get(
    "CRM_CONFIG",
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "config.yaml")),
)


def load_config() -> dict:
    """Return the current config as a plain dict.  Safe to call on every request."""
    with open(CONFIG_PATH, "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def save_config(cfg: dict) -> None:
    """Persist a full config dict back to the config file."""
    with open(CONFIG_PATH, "w", encoding="utf-8") as fh:
        yaml.safe_dump(cfg, fh, default_flow_style=False, sort_keys=False)
