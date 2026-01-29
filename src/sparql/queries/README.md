# Workflow

1. **Create the SPARQL query**
   Write or update the SPARQL query that generates the required RDF (Turtle) output.

2. **Run the query and export Turtle via `curl`**
   Execute the query against the endpoint using `curl` and save the response as a `.ttl` file.

```
curl -G https://query.wikidata.org/sparql \
  --data-urlencode "query@sparql/queries/wikidata_GHS_hazard_pictograms.rq" \
  -H "Accept: text/turtle" \
  > ghs_hazard_pictograms.ttl

```

3. **Post-process / clean the Turtle file**
   Normalise and clean the generated TTL (e.g. fix combined codes, enforce naming conventions), either

   * with a small Python script,
   * with LLM-assisted editing, or
   * manually (only for small changes).
