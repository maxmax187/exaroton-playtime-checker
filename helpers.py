import json
from pathlib import Path
from dataclasses import dataclass, fields
from typing import Optional, Any, Dict
from urllib.parse import quote
import requests

# class definition for config file, add any keys in config to this definition, otherwise they will be ignored
@dataclass
class Config:
    API_KEY: Optional[str] = None
    SERVER_ID: Optional[str] = None


def load_config() -> Config:
    """
    Load config.json and overwrite empty or missing values
    with values from secure/secure_config.json if it exists.
    """
    base_dir = Path(__file__).parent
    config_path = base_dir / "config.json"
    secure_path = base_dir / "secure" / "secure_config.json"

    # Load main config (required)
    if not config_path.exists():
        raise FileNotFoundError("config.json not found")

    with config_path.open("r", encoding="utf-8") as f:
        config_data = json.load(f)

    # Load secure config (optional)
    secure_data = {}
    if secure_path.exists():
        with secure_path.open("r", encoding="utf-8") as f:
            secure_data = json.load(f)

    # Merge: secure config fills empty or missing values
    for key, secure_value in secure_data.items():
        if key not in config_data or config_data[key] in ("", None):
            config_data[key] = secure_value


    def make_config(config_data: dict) -> Config:
        allowed_fields = {f.name for f in fields(Config)}
        filtered_data = {
            k: v for k, v in config_data.items()
            if k in allowed_fields
        }
        return Config(**filtered_data)

    config = make_config(config_data)


    # Final validation (fail fast)
    if not config.API_KEY:
        raise RuntimeError("API_KEY is required but missing")

    return config


def list_dir_children(api_token: str, server_id: str, path: str) -> list[dict]:
    """
    Calls exaroton 'Get file information' to list a directory's children.
    """
    # API expects .../files/info/{path}/ with a trailing slash. :contentReference[oaicite:2]{index=2}
    url = f"https://api.exaroton.com/v1/servers/{server_id}/files/info/{quote(path, safe='')}/"
    r = requests.get(url, headers={"Authorization": f"Bearer {api_token}"}, timeout=30)
    r.raise_for_status()
    payload = r.json()

    if not payload.get("success"):
        raise RuntimeError(payload.get("error") or "Unknown API error")

    data = payload.get("data") or {}
    if not data.get("isDirectory"):
        raise ValueError(f"{path!r} is not a directory")

    return data.get("children") or []


def fetch_stats_files(
    exa,
    api_token: str,
    server_id: str,
    stats_dir: str = "world/stats",
) -> Dict[str, Any]:
    """
    Lists world/stats, then downloads and parses all *.json files.
    Returns: {filename: parsed_json}
    """
    children = list_dir_children(api_token, server_id, stats_dir)

    out: Dict[str, Any] = {}

    for child in children:
        name = child.get("name")
        if not name or not name.endswith(".json"):
            continue

        file_path = f"{stats_dir}/{name}"
        name = name[:-5]       # strip '.json' from end such that UUID becomes the key

        # Your wrapper provides only this:
        raw = exa.get_file_data(server_id, file_path)

        # Normalize to text
        if hasattr(raw, "content"):          # requests.Response-like
            raw_bytes = raw.content
        else:
            raw_bytes = raw                  # often bytes
        if isinstance(raw_bytes, str):
            text = raw_bytes
        else:
            text = raw_bytes.decode("utf-8", errors="replace")

        out[name] = json.loads(text)

    return out

def fetch_json_file(exa, server_id: str, path: str):
    '''
    Fetch JSON file from server
    
    :param server_id: Description
    :type server_id: str
    :param path: Description
    :type path: str
    '''
    # Your wrapper provides only this:
    raw = exa.get_file_data(server_id, path)

    # Normalize to text
    if hasattr(raw, "content"):          # requests.Response-like
        raw_bytes = raw.content
    else:
        raw_bytes = raw                  # often bytes
    if isinstance(raw_bytes, str):
        text = raw_bytes
    else:
        text = raw_bytes.decode("utf-8", errors="replace")

    return json.loads(text)
     


def list_to_dict(player_list:list, key="uuid") -> Dict[str, Any]:
    '''
    Turn player list into dictionary
    dictionary keys default to uuid
    '''
    d: Dict[str, Any] = {}

    for player in player_list:
        k = player[key]
        d[k] = player["name"]

    return d