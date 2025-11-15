# utils.py
import os
import secrets
import json
from pathlib import Path

# Folder to store API keys
KEYS_FILE = Path("dev_keys.json")
if not KEYS_FILE.exists():
    KEYS_FILE.write_text(json.dumps({}))

# ---------------------
# API Key Management
# ---------------------
def create_api_key(owner_name):
    """
    Generate a new developer API key.
    Stores it in dev_keys.json
    Returns the key.
    """
    key = secrets.token_urlsafe(32)
    data = json.loads(KEYS_FILE.read_text())
    data[key] = {"owner": owner_name}
    KEYS_FILE.write_text(json.dumps(data, indent=2))
    return key

def verify_api_key(key):
    """
    Check if API key is valid.
    """
    data = json.loads(KEYS_FILE.read_text())
    return key in data

def list_keys():
    """
    List all dev keys (owner names + keys)
    """
    data = json.loads(KEYS_FILE.read_text())
    return [{"key": k, "owner": v["owner"]} for k, v in data.items()]

def revoke_key(key):
    """
    Revoke/delete an API key
    """
    data = json.loads(KEYS_FILE.read_text())
    if key in data:
        del data[key]
        KEYS_FILE.write_text(json.dumps(data, indent=2))
        return True
    return False
