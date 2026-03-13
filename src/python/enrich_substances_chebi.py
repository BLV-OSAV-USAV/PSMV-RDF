import re
import json
from pathlib import Path
from collections import defaultdict
from rdflib import Graph, URIRef, Namespace, Literal
from rdflib.namespace import OWL
from SPARQLWrapper import SPARQLWrapper, JSON, POST

def normalize_name(name: str) -> str:
    return re.sub(r"\s+", " ", name.strip().lower())

def enrich_substances_chebi(
    graph_path="rdf/data/substance.ttl",
    query_path="src/sparql/queries/enrich_chebi.rq",
    batch_size=50,
    cache_path="rdf/enrichment_cache.json"
):
    graph = Graph()
    graph.parse(graph_path, format="turtle")

    EX = Namespace("https://agriculture.ld.admin.ch/plant-protection/")
    graph.bind("ex", EX)

    iupac_prop = EX.iupacName

    substances = list(graph.subject_objects(iupac_prop))
    print(f"[i] Found {len(substances)} substances")

    # Build lookup dict: normalized iupac_name -> substance URI
    lookup = {normalize_name(str(o)): s for s, o in substances}

    # Load cache
    try:
        with open(cache_path, "r") as f:
            cache = json.load(f)
    except FileNotFoundError:
        cache = {}

    # Prepare batch names not in cache
    names_to_query = [n for n in lookup.keys() if n not in cache]
    print(f"[i] {len(names_to_query)} names to enrich (not cached)")

    sparql = SPARQLWrapper("https://sparql.rhea-db.org/sparql")
    sparql.setReturnFormat(JSON)
    sparql.setMethod(POST)  # Use POST to avoid 414 errors

    query_template = Path(query_path).read_text()
    enriched = 0

    for i in range(0, len(names_to_query), batch_size):
        batch = names_to_query[i:i+batch_size]
        values = " ".join(f'"{n}"' for n in batch)
        query = query_template.replace("{values}", values)

        try:
            sparql.setQuery(query)
            results = sparql.query().convert()

            for binding in results["results"]["bindings"]:
                input_name = normalize_name(binding["label"]["value"])  # assumes SPARQL returns label matching input
                chebi_uri = binding["chebiURI"]["value"]

                # Update cache
                cache[input_name] = chebi_uri

                # Apply enrichment
                if input_name in lookup:
                    graph.add((lookup[input_name], OWL.sameAs, URIRef(chebi_uri)))
                    enriched += 1
                    print(f"  ✓ {input_name} → {chebi_uri}")

        except Exception as e:
            print(f"[!] Batch {i//batch_size+1} failed: {e}")

    # Save cache
    with open(cache_path, "w") as f:
        json.dump(cache, f, indent=2)

    print(f"[i] Enriched {enriched}/{len(substances)} substances")
    graph.serialize(destination=graph_path, format="turtle")
    print(f"[i] Saved enriched graph → {graph_path}")
    
if __name__ == "__main__":
    enrich_substances_chebi()