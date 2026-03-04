import yaml
from rdflib import Namespace
import os
import sys
import shutil
import subprocess
import urllib.request

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "..", "..")) 

SHACL_PLAY_VERSION = "0.11.6"

SHACL_PLAY_JAR_PATH = os.path.join(
    ROOT_DIR,
    "service",
    "shacl_play",
    f"shacl-play-app-{SHACL_PLAY_VERSION}-onejar.jar",
)

SHACL_PLAY_JAR_URL = (
    f"https://github.com/sparna-git/shacl-play/releases/download/"
    f"{SHACL_PLAY_VERSION}/"
    f"shacl-play-app-{SHACL_PLAY_VERSION}-onejar.jar"
)

def load_namespaces(path="data/namespaces/namespaces.yaml"):
    """
    Loads namespaces from namespaces in data.

    Args:
        path (str, optional): Path to namespaces. Defaults to "data/namespaces/namespaces.yaml".

    Returns:
        Namespaces
    """
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    namespaces = {}
    for prefix, uri in data.items():
        namespaces[prefix] = Namespace(uri)

    return namespaces

def load_rdf_mappings(namespaces, path="data/mapping/mapping_rdf.yaml", namespace_map=None):
    """
    Load RDF-specific mappings from YAML and convert to namespace URIs.
    
    Args:
        namespaces: Dictionary of namespace objects from load_namespaces()
        path: Path to YAML file containing RDF mappings
        namespace_map: Dict mapping YAML keys to namespace names
                      Example: {"country_mapping": "country", "type_mapping": "base"}
                      If None, infers namespace from key name (e.g., "country_mapping" -> "country")
    
    Returns:
        dict: Dictionary of mapping names to their URI-converted dictionaries
              Example: {"country_mapping": {...}, "type_mapping": {...}}
    """
    import yaml
    
    with open(path, "r") as file:
        yaml_mappings = yaml.safe_load(file)

    if yaml_mappings is None:
        return {}

    result = {}

    for yaml_key, mapping_dict in yaml_mappings.items():
        if not isinstance(mapping_dict, dict):
            continue
        
        if namespace_map and yaml_key in namespace_map:
            namespace_name = namespace_map[yaml_key]
        else:
            namespace_name = yaml_key.replace("_mapping", "")
        
        ns = namespaces.get(namespace_name)
        if ns is None:
            print(f"Warning: Namespace '{namespace_name}' not found for '{yaml_key}'")
            continue

        converted = {
            key: getattr(ns, value)
            for key, value in mapping_dict.items()
        }

        result[yaml_key] = converted

    return result

def ensure_jar(jar_path: str = SHACL_PLAY_JAR_PATH) -> str:
    if os.path.isfile(jar_path):
        return jar_path

    jar_dir = os.path.dirname(os.path.abspath(jar_path))
    os.makedirs(jar_dir, exist_ok=True)

    print(f"  JAR not found locally. Downloading v{SHACL_PLAY_VERSION} …")
    try:
        urllib.request.urlretrieve(SHACL_PLAY_JAR_URL, jar_path)
        print(f"  ✓ JAR cached at: {jar_path}")
        return jar_path  # <-- this was missing
    except Exception as exc:
        if os.path.isfile(jar_path):
            print("  ⚠ Download failed, using existing cached JAR.")
            return jar_path
        raise RuntimeError(...) from exc