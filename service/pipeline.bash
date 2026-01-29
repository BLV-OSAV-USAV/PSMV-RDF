#!/bin/bash
set -e # immediately exit on error
source .env

echo "Validate syntax of turtle files"
python3 src/python/validate.py rdf

echo "Create a dedicated ontology file for subsequent WebVOWL visualization"
python3 src/python/reason.py \
  -i rdf/ontology/*.ttl \
  -o rdf/processed/ontology.ttl \
  -r src/sparql/rules/*.rq

echo "Merge all data into one graph for subsequent LINDAS upload"
python3 src/python/reason.py \
  -i rdf/ontology/*.ttl rdf/data/*.ttl \
  -o rdf/processed/graph.ttl \
  -r src/sparql/rules/inverse.rq src/sparql/rules/subclass.rq

echo "Delete existing data from LINDAS"
curl \
  --user $USER:$PASSWORD \
  -X DELETE \
  "$ENDPOINT?graph=$GRAPH"

echo "Upload graph.ttl file to LINDAS"
curl \
  --user $USER:$PASSWORD \
  -X POST \
  -H "Content-Type: text/turtle" \
  --data-binary @rdf/processed/graph.ttl \
  "$ENDPOINT?graph=$GRAPH"

echo "All commands executed."