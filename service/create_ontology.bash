python3 src/python/reason.py \
  -i rdf/ontology/*.ttl \
  -o rdf/processed/ontology.ttl \
  -r src/sparql/rules/*.rq \
  -p rdf/ontology/prefixes.ttl