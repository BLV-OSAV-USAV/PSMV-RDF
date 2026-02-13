import yaml
from rdflib import Namespace

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