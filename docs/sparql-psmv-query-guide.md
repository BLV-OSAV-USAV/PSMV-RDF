# SPARQL Query Guide: Plant Protection Products (PSMV)

**Graph:** `https://lindas.admin.ch/fsvo/plant-protection-products`  
**Base namespace:** `https://agriculture.ld.admin.ch/plant-protection/`  
**SPARQL endpoint:** `https://lindas.admin.ch/query`

---

## Introduction

Copy any query from this guide and paste it into the interactive SPARQL editor:

**https://agriculture.ld.admin.ch/sparql/#**

No installation needed. Just paste, hit **Run**, and browse the results in your browser.

### Key concepts

```
                ┌──► Product
                ├──► Crop
Indication ─────┼──► Pest  (full / partial / side effect)
                └──► ApplicationArea
```

| Term | Meaning |
|------|---------|
| `Indication` | One approved use case (product + crop + pest + area) |
| `Crop` | The plant being protected (e.g. Zuckermais) |
| `Pest` | The organism being controlled (e.g. Thripse) |
| `ApplicationArea` | Where it is applied (e.g. Freiland, Gewächshaus) |
| `fullEffect` / `partialEffect` / `sideEffect` | Links an indication to a pest, by level of efficacy |
| `schema:name` | The human-readable label |

Labels exist in `"de"`, `"fr"`, `"it"` and `"en"`. Always add a `lang()` filter to avoid duplicate rows.

## For Users and Subject Matter Experts

---

### Template 1

> *"Which products can I use on sugar maize against thrips?"*

Change `"zuckermais"` and `"thripse"` to search for other crops and pests.

```sparql
PREFIX : <https://agriculture.ld.admin.ch/plant-protection/>
PREFIX schema: <http://schema.org/>

SELECT DISTINCT ?product ?productName ?cropName ?pestName ?areaName
WHERE {
  GRAPH <https://lindas.admin.ch/fsvo/plant-protection-products> {

    ?indication a :Indication ;
                :crop ?crop ;
                :fullEffect ?pest ;
                :applicationArea ?area ;
                :product ?product .

    ?product schema:name ?productName .
    ?crop a :Crop ; schema:name ?cropName .
    ?pest a :Pest ; schema:name ?pestName .
    ?area a :ApplicationArea ; schema:name ?areaName .

    FILTER (
      lang(?productName) IN ("de", "") &&
      lang(?cropName) = "de" && CONTAINS(LCASE(?cropName), "zuckermais") &&
      lang(?pestName) = "de" && CONTAINS(LCASE(?pestName), "thripse") &&
      lang(?areaName) = "de"
    )
  }
}
ORDER BY ?productName
```

---

### Template 2

> *"Show me ALL approved effects, not just full efficacy."*

Same question as Template 1, but includes partial and side effects. The column `?effectType` shows which one applies.

```sparql
PREFIX : <https://agriculture.ld.admin.ch/plant-protection/>
PREFIX schema: <http://schema.org/>

SELECT DISTINCT ?product ?productName ?effectType ?cropName ?pestName ?areaName
WHERE {
  GRAPH <https://lindas.admin.ch/fsvo/plant-protection-products> {

    VALUES (?effectProperty ?effectType) {
      (:fullEffect    "full")
      (:partialEffect "partial")
      (:sideEffect    "side")
    }

    ?indication a :Indication ;
                :crop ?crop ;
                ?effectProperty ?pest ;
                :applicationArea ?area ;
                :product ?product .

    ?product schema:name ?productName .
    ?crop a :Crop ; schema:name ?cropName .
    ?pest a :Pest ; schema:name ?pestName .
    ?area a :ApplicationArea ; schema:name ?areaName .

    FILTER (
      lang(?productName) IN ("de", "") &&
      lang(?cropName) = "de" && CONTAINS(LCASE(?cropName), "zuckermais") &&
      lang(?pestName) = "de" && CONTAINS(LCASE(?pestName), "thripse") &&
      lang(?areaName) = "de"
    )
  }
}
ORDER BY ?productName ?effectType
```

---

### Template 3

> *"What is product 'Karate Zeon' approved for?"*

Lists every crop, pest and application area for one product. Change `"karate zeon"` to look up another product (lowercase, partial names work).

```sparql
PREFIX : <https://agriculture.ld.admin.ch/plant-protection/>
PREFIX schema: <http://schema.org/>

SELECT DISTINCT ?product ?productName ?cropName ?pestName ?effectType ?areaName
WHERE {
  GRAPH <https://lindas.admin.ch/fsvo/plant-protection-products> {

    VALUES (?effectProperty ?effectType) {
      (:fullEffect    "full")
      (:partialEffect "partial")
      (:sideEffect    "side")
    }

    ?indication a :Indication ;
                :product ?product ;
                :crop ?crop ;
                ?effectProperty ?pest ;
                :applicationArea ?area .

    ?product schema:name ?productName .
    ?crop a :Crop ; schema:name ?cropName .
    ?pest a :Pest ; schema:name ?pestName .
    ?area a :ApplicationArea ; schema:name ?areaName .

    FILTER (
      lang(?productName) IN ("de", "") &&
      CONTAINS(LCASE(STR(?productName)), "karate zeon") &&
      lang(?cropName) = "de" &&
      lang(?pestName) = "de" &&
      lang(?areaName) = "de"
    )
  }
}
ORDER BY ?cropName ?pestName ?effectType
```

---

## For developers

### Endpoint & authentication

```
Endpoint:  https://lindas.admin.ch/query
Method:    GET or POST (application/x-www-form-urlencoded)
Accept:    application/sparql-results+json
Auth:      None required for public read access
```

### Minimal fetch (vanilla JS)

```js
const ENDPOINT = "https://lindas.admin.ch/query";

async function querySparql(sparql) {
  const url = new URL(ENDPOINT);
  url.searchParams.set("query", sparql);

  const res = await fetch(url.toString(), {
    headers: { Accept: "application/sparql-results+json" },
  });

  // The response body contains the SPARQL error message, if any
  if (!res.ok) throw new Error(`SPARQL error ${res.status}: ${await res.text()}`);
  const json = await res.json();

  // json.results.bindings is an array of row objects;
  // flatten each cell to its plain value
  return json.results.bindings.map(row =>
    Object.fromEntries(Object.entries(row).map(([k, v]) => [k, v.value]))
  );
}
```

**Example**

```js
const rows = await querySparql(`
  PREFIX : <https://agriculture.ld.admin.ch/plant-protection/>
  PREFIX schema: <http://schema.org/>

  SELECT DISTINCT ?product ?productName ?cropName ?pestName ?areaName
  WHERE {
    GRAPH <https://lindas.admin.ch/fsvo/plant-protection-products> {
      ?indication a :Indication ;
                  :crop ?crop ;
                  :fullEffect ?pest ;
                  :applicationArea ?area ;
                  :product ?product .

      ?product schema:name ?productName .
      ?crop a :Crop ; schema:name ?cropName .
      ?pest a :Pest ; schema:name ?pestName .
      ?area a :ApplicationArea ; schema:name ?areaName .

      FILTER (
        lang(?productName) IN ("de", "") &&
        lang(?cropName) = "de" && CONTAINS(LCASE(?cropName), "zuckermais") &&
        lang(?pestName) = "de" && CONTAINS(LCASE(?pestName), "thripse") &&
        lang(?areaName) = "de"
      )
    }
  }
  ORDER BY ?productName
`);

console.log(`${rows.length} rows`);
console.table(rows);
```

**To try it quickly:** save both blocks as `test.mjs` and run `node test.mjs`

### Full example

This query lists all plant protection products containing sulphur, showing for each its name, federal admission number, formulation, permission holder and product type.

```js
const ENDPOINT = "https://lindas.admin.ch/query";

async function querySparql(sparql) {
  const url = new URL(ENDPOINT);
  url.searchParams.set("query", sparql);

  const res = await fetch(url.toString(), {
    headers: { Accept: "application/sparql-results+json" },
  });

  if (!res.ok) throw new Error(`SPARQL error ${res.status}: ${await res.text()}`);
  const json = await res.json();

  return json.results.bindings.map(row =>
    Object.fromEntries(Object.entries(row).map(([k, v]) => [k, v.value]))
  );
}

const query = `
PREFIX psmv: <https://agriculture.ld.admin.ch/plant-protection/>
PREFIX schema: <http://schema.org/>

SELECT ?productName ?admissionNumber
       ?formulationName ?holderName
       (GROUP_CONCAT(DISTINCT ?productTypeName; separator=", ") AS ?productTypes)
       (GROUP_CONCAT(DISTINCT ?substanceName; separator=", ") AS ?substances)
WHERE {
  GRAPH <https://lindas.admin.ch/fsvo/plant-protection-products> {

    ?product a psmv:Product ;
             schema:name ?productName .
    FILTER (lang(?productName) IN ("de", ""))

    OPTIONAL { ?product psmv:federalAdmissionNumber ?admissionNumber }

    OPTIONAL {
      ?product psmv:formulation ?formulation .
      ?formulation schema:name ?formulationName .
      FILTER (lang(?formulationName) IN ("de", ""))
    }

    OPTIONAL {
      ?product psmv:permissionHolder ?holder .
      ?holder schema:name ?holderName .
      FILTER (lang(?holderName) IN ("de", ""))
    }

    OPTIONAL {
      ?product psmv:productType ?productType .
      ?productType schema:name ?productTypeName .
      FILTER (lang(?productTypeName) = "en")
    }

    OPTIONAL {
      ?product ?p ?ingredient .
      ?ingredient psmv:substance ?substance .
      ?substance schema:name ?substanceName .
      FILTER (lang(?substanceName) = "en")
    }

    # Only products containing sulphur; remove this block to list all products
    FILTER EXISTS {
      ?product ?p2 ?i2 .
      ?i2 psmv:substance ?s2 .
      ?s2 schema:name ?n2 .
      FILTER (lang(?n2) = "en" && CONTAINS(LCASE(?n2), "sulphur"))
    }
  }
}
GROUP BY ?product ?productName ?admissionNumber ?formulationName ?holderName
ORDER BY ?productName
`;

try {
  const rows = await querySparql(query);
  console.log(`${rows.length} rows`);
  console.table(rows);
} catch (err) {
  console.error(err.message);
}
```

---

## Downloading all data

The queries above return filtered subsets. To get the **whole graph** (about 277,000 triples as of November 2026), use one of the options below.

| Option | Output | Best for |
|--------|--------|----------|
| [Full dump as JSON-LD](#option-1-full-dump-as-json-ld) | Every triple, as RDF in JSON-LD | Complete, lossless copy; loading into your own triple store |
| [All indications as flat JSON](#option-2-all-indications-as-flat-json) | One plain JSON object per indication, with names | Building apps around products, crops, pests and areas |

### Count the triples first

Use this to check that your download is complete.

```sparql
SELECT (COUNT(*) AS ?n)
WHERE {
  GRAPH <https://lindas.admin.ch/fsvo/plant-protection-products> { ?s ?p ?o }
}
```

### Option 1: Full dump as JSON-LD

```bash
curl -s https://lindas.admin.ch/query \
  -H "Accept: application/ld+json" \
  --data-urlencode 'query=
CONSTRUCT { ?s ?p ?o }
WHERE {
  GRAPH <https://lindas.admin.ch/fsvo/plant-protection-products> {
    ?s ?p ?o
  }
}' \
  -o psm_graph.jsonld
```

The output is expanded JSON-LD, so the keys are full IRIs. If the request times out or the file looks truncated, use the paged Python script below, which also checks the triple count.

<details>
<summary>Paged download with completeness check (Python)</summary>

```python
# pip install requests rdflib
import requests
from rdflib import Graph

ENDPOINT = "https://lindas.admin.ch/query"
GRAPH = "https://lindas.admin.ch/fsvo/plant-protection-products"
PAGE = 10000

count_q = f"SELECT (COUNT(*) AS ?n) WHERE {{ GRAPH <{GRAPH}> {{ ?s ?p ?o }} }}"
r = requests.post(ENDPOINT, data={"query": count_q},
                  headers={"Accept": "application/sparql-results+json"}, timeout=120)
r.raise_for_status()
TOTAL = int(r.json()["results"]["bindings"][0]["n"]["value"])

g = Graph()
for offset in range(0, TOTAL, PAGE):
    q = f"""
    CONSTRUCT {{ ?s ?p ?o }}
    WHERE {{
      {{ SELECT ?s ?p ?o WHERE {{ GRAPH <{GRAPH}> {{ ?s ?p ?o }} }}
         ORDER BY ?s ?p ?o LIMIT {PAGE} OFFSET {offset} }}
    }}"""
    r = requests.post(ENDPOINT, data={"query": q},
                      headers={"Accept": "application/n-triples"}, timeout=300)
    r.raise_for_status()
    g.parse(data=r.text, format="nt")
    print(offset, len(g))

assert len(g) == TOTAL, f"expected {TOTAL}, got {len(g)}"
g.serialize("psm_graph.nt", format="nt")
g.serialize("psm_graph.jsonld", format="json-ld")
```

</details>

<details>
<summary>Convert the dump to compact JSON with short keys (Python)</summary>

```python
# pip install pyld
import json
from pyld import jsonld

with open("psm_graph.jsonld") as f:
    doc = json.load(f)

context = {
    "@vocab": "https://agriculture.ld.admin.ch/plant-protection/",
    "schema": "http://schema.org/",
    "name": {"@id": "schema:name", "@container": "@language"},
}

compact = jsonld.compact(doc, context)

with open("psm_graph_compact.json", "w") as f:
    json.dump(compact, f, ensure_ascii=False, indent=2)
```

Names then look like `{"de": "...", "fr": "...", "it": "...", "en": "..."}`.

</details>

### Option 2: All indications as flat JSON

Fetches every indication in all four languages, page by page, and merges the pages into one file. Requires `curl` and `jq`.

```bash
#!/usr/bin/env bash
set -euo pipefail

ENDPOINT="https://lindas.admin.ch/query"
PAGE=10000
OFFSET=0
OUT=indications_all.json
TMP=$(mktemp -d)

while true; do
  echo "Fetching offset $OFFSET"
  curl -s --fail "$ENDPOINT" \
    -H "Accept: application/sparql-results+json" \
    --data-urlencode "query=
PREFIX : <https://agriculture.ld.admin.ch/plant-protection/>
PREFIX schema: <http://schema.org/>
SELECT DISTINCT ?lang ?indication ?product ?productName ?crop ?cropName
                ?pest ?pestName ?effectType ?area ?areaName
WHERE {
  GRAPH <https://lindas.admin.ch/fsvo/plant-protection-products> {
    VALUES ?lang { \"de\" \"fr\" \"it\" \"en\" }
    VALUES (?effectProperty ?effectType) {
      (:fullEffect \"full\") (:partialEffect \"partial\") (:sideEffect \"side\")
    }
    ?indication a :Indication ;
                :product ?product ;
                :crop ?crop ;
                ?effectProperty ?pest ;
                :applicationArea ?area .
    ?product schema:name ?productName .
    ?crop schema:name ?cropName .
    ?pest schema:name ?pestName .
    ?area schema:name ?areaName .
    FILTER (lang(?productName) IN (?lang, \"\") &&
            lang(?cropName) = ?lang &&
            lang(?pestName) = ?lang &&
            lang(?areaName) = ?lang)
  }
}
ORDER BY ?lang ?indication ?pest ?effectType
LIMIT $PAGE OFFSET $OFFSET" \
    -o "$TMP/page_$OFFSET.json"

  N=$(jq '.results.bindings | length' "$TMP/page_$OFFSET.json")
  echo "  got $N rows"
  [ "$N" -eq 0 ] && break
  OFFSET=$((OFFSET + PAGE))
done

# Merge all pages and flatten {"x": {"type":..., "value":...}} into {"x": "..."}
jq -s '[ .[].results.bindings[]
         | with_entries(.value = .value.value) ]' \
   "$TMP"/page_*.json > "$OUT"

echo "Done: $(jq length "$OUT") rows in $OUT"
rm -rf "$TMP"
```

**Example row**

One indication of *Karate Zeon*: full effect against Erdraupen on Endivien und Blattzichorien in Gemüsebau.

```json
{
  "lang": "de",
  "indication": "https://agriculture.ld.admin.ch/plant-protection/indication/00b2573b-c165-46ed-8d5e-2a583ae20630",
  "product": "https://agriculture.ld.admin.ch/plant-protection/product/W-6098",
  "productName": "Karate Zeon",
  "crop": "https://agriculture.ld.admin.ch/plant-protection/crop/8db1a579-6bac-4dcb-8026-e79b65d3bd3a",
  "cropName": "Endivien und Blattzichorien",
  "pest": "https://agriculture.ld.admin.ch/plant-protection/pest/b67246a4-494f-486e-a15d-ec6585aea3cf",
  "pestName": "Erdraupen",
  "effectType": "full",
  "area": "https://agriculture.ld.admin.ch/plant-protection/code/cf7c3309-3dba-4223-88c2-6ba749f2b344",
  "areaName": "Gemüsebau"
}
```

The IRIs are stable identifiers: use them as keys to join rows, and the `...Name` fields for display. One indication can appear in several rows, once per pest and per language.

**Notes**

- `?lang` keeps all names in a row in the same language. For one language only, use e.g. `VALUES ?lang { "de" }`.
- A row only appears for a language if crop, pest and area all have a label in that language.
- To split the result by language: `jq '[.[] | select(.lang=="fr")]' indications_all.json > indications_fr.json`
- If a page times out, lower `PAGE` to 5000.