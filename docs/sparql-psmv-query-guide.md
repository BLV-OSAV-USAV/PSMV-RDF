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