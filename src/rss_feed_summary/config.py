import os
from typing import Any, Dict
import yaml

DEFAULT_CONFIG_PATH = os.environ.get("RSS_SUMMARY_CONFIG", "config.yaml")


def load_config(path: str | None = None) -> Dict[str, Any]:
    cfg_path = path or DEFAULT_CONFIG_PATH
    with open(cfg_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    # minimal validation
    if "feeds" not in data or not isinstance(data["feeds"], list):
        raise ValueError("config.yaml must contain a 'feeds' list")
    email = data.get("email", {})
    if not email.get("smtp_host"):
        raise ValueError("email.smtp_host is required")
    if not email.get("from") or not email.get("to"):
        raise ValueError("email.from and email.to are required")
    return data