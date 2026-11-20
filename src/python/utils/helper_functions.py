import re
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

import pandas as pd
import yaml
from rdflib import Literal, Namespace
from rdflib.namespace import RDF, XSD

SCHEMA = Namespace("http://schema.org/")

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

    out = {}
    for k, v in raw.items():
        v = str(v).strip()
        if v.startswith("http"):
            raise ValueError(f"unit_map.yaml: expected a local name, got IRI for '{k}': {v}")
        out[str(k).strip()] = unit_ns[v]
    return out


def to_decimal(value) -> Decimal:
    """
    Convert a numeric source value to an exact Decimal without float artifacts.

    str() yields the shortest round-trip representation, so 0.1 stays 0.1
    instead of 0.1000000000000000055511151231257827.
    Trailing zeros are removed, integers keep plain notation (100, not 1E+2).
    """
    d = Decimal(str(value)).normalize()
    if d == d.to_integral_value():
        d = d.quantize(Decimal(1))
    return d


def format_psm(value) -> str:
    """
    Format a share value the same way as the PSM register.

    Values > 0.1: rounded to 2 decimal places.
    Values <= 0.1: rounded to 2 significant digits.
    Trailing zeros are removed in both cases. Rounding is half away from zero,
    matching SQL Server ROUND (Python's round() would round half to even).

    Examples:
        12.345   -> "12.35"
        0.5      -> "0.5"
        0.0023   -> "0.0023"
        0.0100   -> "0.01"
        0.00045  -> "0.00045"
    """
    d = to_decimal(value)
    if d == 0:
        return "0"
    if abs(d) > Decimal("0.1"):
        q = d.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    else:
        q = d.quantize(Decimal(1).scaleb(d.adjusted() - 1), rounding=ROUND_HALF_UP)
    return format(q.normalize(), "f")

# Placeholder for products whose register entry only names the category
# ("Netz- und Haftmittel") without any substance
UNSPECIFIED_ADJUVANT_ID = "unspecified-wetting-and-adhesion-agent"

def add_amount(graph, node, v_from, v_to):
    """Single value -> schema:value, range -> schema:minValue/maxValue.

    A value given only as 'from' or only as 'to' is a single value:
    the PSM directory shows e.g. "1.1 kg/ha", not "bis 1.1 kg/ha".
    """
    has_from, has_to = pd.notna(v_from), pd.notna(v_to)
    if has_from != has_to or (has_from and float(v_from) == float(v_to)):
        single = v_from if has_from else v_to
        graph.add((node, SCHEMA.value, Literal(float(single), datatype=XSD.decimal)))
        return
    graph.add((node, SCHEMA.minValue, Literal(float(v_from), datatype=XSD.decimal)))
    graph.add((node, SCHEMA.maxValue, Literal(float(v_to), datatype=XSD.decimal)))