
import os
import json
import uuid

DEV_KEYS_FILE = "dev_keys.json"

# Ensure the file exists
if not os.path.exists(DEV_KEYS_FILE):
    with open(DEV_KEYS_FILE, "w") as f:
        json.dump([], f)

def load_keys():
    with open(DEV_KEYS_FILE, "r") as f:
        return json.load(f)

def save_keys(keys):
    with open(DEV_KEYS_FILE, "w") as f:
        json.dump(keys, f, indent=4)

def create_api_key(owner_name: str):
    key = str(uuid.uuid4())
    keys = load_keys()
    keys.append({"owner": owner_name, "key": key})
    save_keys(keys)
    return key

def list_keys():
    return load_keys()

def revoke_key(key: str):
    keys = load_keys()
    new_keys = [k for k in keys if k["key"] != key]
    save_keys(new_keys)
    return len(keys) != len(new_keys)

def verify_api_key(key: str):
    keys = load_keys()
    return any(k["key"] == key for k in keys)
