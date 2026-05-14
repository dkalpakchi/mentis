"""Configuration management for Mentis."""

import json
from pathlib import Path
from typing import Dict, Any, Optional


CONFIG_DIR = Path(".mentis")
CONFIG_FILE = CONFIG_DIR / "config.json"


def ensure_config_dir():
    """Ensure the config directory exists."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def load_config() -> Dict[str, Any]:
    """Load configuration from file. Returns empty dict if not found."""
    ensure_config_dir()
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        except json.JSONDecodeError, IOError:
            return {}
    return {}


def save_config(config: Dict[str, Any]) -> None:
    """Save configuration to file."""
    ensure_config_dir()
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)


def get_config(key: str, default: Any = None) -> Any:
    """Get a configuration value."""
    config = load_config()
    return config.get(key, default)


def set_config(key: str, value: Any) -> None:
    """Set a configuration value and save."""
    config = load_config()
    config[key] = value
    save_config(config)


def get_model() -> Optional[str]:
    """Get the stored model name, if any."""
    return get_config("model")


def set_model(model: str | None) -> None:
    """Store the model name."""
    if model is not None:
        set_config("model", model)


def get_username() -> Optional[str]:
    """Get the stored username, if any."""
    return get_config("username")


def set_username(username: str) -> None:
    """Store the username."""
    set_config("username", username)


def find_existing_usernames() -> list:
    """Find usernames from existing KG files in the current directory."""
    import glob

    usernames = set()

    # Look for GraphML KG files: kg_{username}.graphml
    for filepath in glob.glob("kg_*.graphml"):
        # Extract username from filename: kg_{username}.graphml
        filename = Path(filepath).name
        if filename.startswith("kg_") and filename.endswith(".graphml"):
            username = filename.replace("kg_", "").replace(".graphml", "")
            usernames.add(username)

    # Look for RDF KG files: kg_{username}.ttl
    for filepath in glob.glob("kg_*.ttl"):
        filename = Path(filepath).name
        if filename.startswith("kg_") and filename.endswith(".ttl"):
            username = filename.replace("kg_", "").replace(".ttl", "")
            usernames.add(username)

    # Also check config for stored usernames
    config = load_config()
    if "usernames" in config:
        for username in config["usernames"]:
            usernames.add(username)
    elif "username" in config:
        usernames.add(config["username"])

    return sorted(list(usernames))


def add_known_username(username: str) -> None:
    """Add a username to the list of known usernames in config."""
    config = load_config()
    if "usernames" not in config:
        config["usernames"] = []
    if username not in config["usernames"]:
        config["usernames"].append(username)
    save_config(config)
