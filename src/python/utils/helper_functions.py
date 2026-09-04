import yaml
from rdflib import Namespace
import os
import sys
import shutil
import subprocess
import urllib.request
import pandas as pd
import re
from rdflib.namespace import RDF
from rdflib import Literal
from pathlib import Path

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "..", "..")) 

SHACL_PLAY_VERSION = "0.12.3"

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

        converted = {}
        for key, value in mapping_dict.items():
            if str(value).startswith("http"):
                converted[key] = str(value)
            else:
                converted[key] = getattr(ns, value)

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
        return jar_path
    except Exception as exc:
        if os.path.isfile(jar_path):
            print("  ⚠ Download failed, using existing cached JAR.")
            return jar_path
        raise RuntimeError(...) from exc


def parse_phone_numbers(raw_str):
    if pd.isna(raw_str) or not str(raw_str).strip():
        return []
    
    s = str(raw_str).strip()
    # Remove standard international (0) 
    s = re.sub(r'\(0\)', '', s)
    
    # Split by '/' if followed by '+', '00', or '0' and a digit
    s = re.sub(r'\s*/\s*(?=\+|00|0[1-9])', ' SEP ', s)
    # Split by '|'
    s = re.sub(r'\s*\|\s*', ' SEP ', s)
    # Split by any letters (e.g., 'mobile', 'direct call', 'M', 'T')
    s = re.sub(r'[a-zA-Z]+', ' SEP ', s)
    
    parts = s.split(' SEP ')
    
    formatted_nums = []
    for part in parts:
        # Keep only digits and the plus sign
        digits = re.sub(r'[^\d+]', '', part)
        
        if len(digits) < 7:
            continue
            
        # Convert initial '00' to '+'
        if digits.startswith('00'):
            digits = '+' + digits[2:]
        # Convert initial '0' to '+41'
        elif digits.startswith('0'):
            digits = '+41' + digits[1:]
        # Handle cases missing a country code prefix but having a length implying one
        elif not digits.startswith('+'):
            if len(digits) == 9:
                digits = '+41' + digits
            elif len(digits) > 9:
                digits = '+' + digits
                
        # Format typical Swiss numbers like: +41-76-472-24-53
        if digits.startswith('+41') and len(digits) == 12:
            formatted = f"{digits[0:3]}-{digits[3:5]}-{digits[5:8]}-{digits[8:10]}-{digits[10:12]}"
        # Format German numbers or long international numbers
        elif digits.startswith('+49') and len(digits) >= 12:
            formatted = f"{digits[0:3]}-" + "-".join(re.findall(r'.{1,4}', digits[3:]))
        # Format other numbers generically with hyphens
        else:
            if digits.startswith('+'):
                two_digit_cc = [
                    '30', '31', '32', '33', '34', '36', '39', '40', '41', '43', '44', '45', '46', 
                    '47', '48', '49', '51', '52', '53', '54', '55', '56', '57', '58', '60', '61', 
                    '62', '63', '64', '65', '66', '81', '82', '84', '86', '90', '91', '92', '93', 
                    '94', '95', '98'
                ]
                if digits[1] == '1' or digits[1] == '7':
                    cc_len = 2
                elif digits[1:3] in two_digit_cc:
                    cc_len = 3
                else:
                    cc_len = 4
                formatted = f"{digits[:cc_len]}-" + "-".join(re.findall(r'.{1,3}', digits[cc_len:]))
            else:
                formatted = "-".join(re.findall(r'.{1,3}', digits))
                
        if formatted not in formatted_nums:
            formatted_nums.append(formatted)
            
    return formatted_nums

def ensure_indication(graph, seen_indications, ind_id, INDICATION, BASE):
    """Ensure the Indication node is declared only once."""
    ind_id = ind_id.strip().lower()
    if ind_id not in seen_indications:
        ind_uri = INDICATION[ind_id]
        graph.add((ind_uri, RDF.type, BASE.Indication))
        seen_indications.add(ind_id)
    return INDICATION[ind_id]


def group_to_dict(df: pd.DataFrame, key_col: str) -> dict:
    return (
        df.dropna(subset=[key_col])
        .assign(**{key_col: lambda d: d[key_col].astype(str).str.strip().str.lower()})
        .groupby(key_col, sort=False)
        .apply(lambda g: g.to_dict("records"), include_groups=False)
        .to_dict()
    )

def add_lang_labels(graph, subject, predicate, row):
    for lang in ("EN", "DE", "FR", "IT"):
        val = row.get(lang)
        if pd.notna(val) and str(val).strip():
            graph.add((subject, predicate, Literal(str(val).strip(), lang=lang.lower())))

def load_unit_map(unit_ns):
    path = Path("data/mapping/unit_map.yaml")
    with open(path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    return {
        k: unit_ns[v]
        for k, v in raw.items()
    }