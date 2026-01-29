python3 src/python/reason.py \
  -i rdf/ontology/ghs.ttl \
  -o rdf/processed/ontology.ttl \
  -r src/sparql/rules/subclass.rq src/sparql/rules/schema_to_rdfs.rq \
  -p rdf/ontology/prefixes.ttl