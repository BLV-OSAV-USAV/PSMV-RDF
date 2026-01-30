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
