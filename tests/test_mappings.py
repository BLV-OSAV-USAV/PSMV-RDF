from src.python.utils.helper_functions import load_namespaces, load_rdf_mappings

NAMESPACE_CONFIG = {
    "country_mapping": "country",
    "type_mapping": "base",
    "unit_mapping": "unit",
    "category_mapping": "base",
}


def test_unit_mapping_has_keys_used_by_products_ttl():
    mappings = load_rdf_mappings(load_namespaces(), namespace_map=NAMESPACE_CONFIG)
    missing = {"percent", "gram_per_litre"} - set(mappings["unit_mapping"])
    assert not missing, f"unit_mapping lacks {missing}"


def test_mapping_values_are_absolute_uris():
    mappings = load_rdf_mappings(load_namespaces(), namespace_map=NAMESPACE_CONFIG)
    for name, mapping in mappings.items():
        bad = [v for v in mapping.values() if not str(v).startswith(("http://", "https://"))]
        assert not bad, f"{name}: {bad[:5]}"