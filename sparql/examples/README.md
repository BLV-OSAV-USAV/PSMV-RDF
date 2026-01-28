# SPARQL queries

Put any example SPARQL queries into this directory.

```
curl -G https://query.wikidata.org/sparql \
  --data-urlencode "query@sparql/queries/wikidata_GHS_hazard_pictograms.rq" \
  -H "Accept: text/turtle" \
  > ghs_hazard_pictograms.ttl

```