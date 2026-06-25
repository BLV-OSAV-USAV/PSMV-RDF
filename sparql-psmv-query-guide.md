# SPARQL Query Guide — Plant Protection Products (PSMV/PSV)

**Graph:** `https://lindas.admin.ch/fsvo/plant-protection-products`  
**Base namespace:** `https://agriculture.ld.admin.ch/plant-protection/`  
**SPARQL endpoint:** `https://lindas.admin.ch/query`

---

## Introduction

Copy any query from this guide and paste it into the interactive SPARQL editor:

**https://agriculture.ld.admin.ch/sparql/#**

No installation needed — just paste, hit **Run**, and browse the results in your browser.


### Key concepts

```
Product ──► Indication ──► Crop
                      ──► Pest  (full / partial / side effect)
                      ──► ApplicationArea
```

| Term | Meaning |
|------|---------|
| `Indication` | One approved use case (product + crop + pest + area) |
| `Crop` | The plant being protected (e.g. Zuckermais) |
| `Pest` | The organism being controlled (e.g. Thripse) |
| `ApplicationArea` | Where it is applied (e.g. Freiland, Gewächshaus) |
| `schema:name` | The human-readable label — always filter by language tag (`"de"`, `"fr"`, `"it"`, `"en"`) |

`"de"` · `"fr"` · `"it"` · `"en"` — always add a `lang()` filter to avoid duplicate rows.


---

### SME Template 1 — Find products approved for a crop + pest combination

> *"Which products can I use on sugar maize against thrips?"*

```sparql
PREFIX : <https://agriculture.ld.admin.ch/plant-protection/>
PREFIX schema: <http://schema.org/>

SELECT DISTINCT
  ?product ?productName
  ?cropName
  ?pestName
  ?areaName
WHERE {
  GRAPH <https://lindas.admin.ch/fsvo/plant-protection-products> {

    ?indication a :Indication ;
                :crop          ?crop ;
                :pestFullEffect ?pest ;          # ← full efficacy only
                :applicationArea ?area ;
                :product       ?product .

    ?product schema:name ?productName .
    ?crop    schema:name ?cropName .
    ?pest    schema:name ?pestName .
    ?area    schema:name ?areaName .

    FILTER (
      lang(?productName) = "de" &&
      lang(?cropName)    = "de" &&
      lang(?pestName)    = "de" &&
      lang(?areaName)    = "de" &&
      CONTAINS(LCASE(?cropName), "zuckermais") &&
      CONTAINS(LCASE(?pestName), "thripse")
    )
  }
}
ORDER BY ?productName
```

**What to change:**
- Replace `"zuckermais"` and `"thripse"` with your crop / pest keywords (lowercase, partial match is fine).
- Change `lang(...)` values to `"fr"` or `"it"` for French / Italian results.
- Swap `"de"` for a different language on each label independently if needed.

---

### SME Template 2 — Include partial and side effects

> *"Show me ALL approved effects, not just full efficacy."*

Replace the single `:pestFullEffect` triple with a `UNION` block:

```sparql
    {
      ?indication :pestFullEffect    ?pest .
      BIND("Volle Wirkung" AS ?effectType)
    } UNION {
      ?indication :pestPartialEffect ?pest .
      BIND("Teilwirkung" AS ?effectType)
    } UNION {
      ?indication :pestSideEffect    ?pest .
      BIND("Nebenwirkung" AS ?effectType)
    }
```

Add `?effectType` to the `SELECT` clause so you can see which category each row belongs to.

---

### SME Template 3 — Look up a specific product by name

> *"What is product 'Karate Zeon' approved for?"*

```sparql
PREFIX : <https://agriculture.ld.admin.ch/plant-protection/>
PREFIX schema: <http://schema.org/>

SELECT DISTINCT
  ?productName ?cropName ?pestName ?areaName
WHERE {
  GRAPH <https://lindas.admin.ch/fsvo/plant-protection-products> {

    ?indication a :Indication ;
                :product         ?product ;
                :crop            ?crop ;
                :applicationArea ?area .
    # Include any pest effect type
    { ?indication :pestFullEffect    ?pest }
    UNION
    { ?indication :pestPartialEffect ?pest }
    UNION
    { ?indication :pestSideEffect    ?pest }

    ?product schema:name ?productName .
    ?crop    schema:name ?cropName .
    ?pest    schema:name ?pestName .
    ?area    schema:name ?areaName .

    FILTER (
      lang(?productName) = "de" &&
      lang(?cropName)    = "de" &&
      lang(?pestName)    = "de" &&
      lang(?areaName)    = "de" &&
      CONTAINS(LCASE(?productName), "karate zeon")
    )
  }
}
ORDER BY ?cropName ?pestName
```

---

## For Frontend Developers

### Endpoint & authentication

```
Endpoint:  https://lindas.admin.ch/query
Method:    GET or POST (application/x-www-form-urlencoded)
Accept:    application/sparql-results+json   (recommended)
           application/sparql-results+xml
           text/csv
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

  if (!res.ok) throw new Error(`SPARQL error ${res.status}`);
  const json = await res.json();

  // json.results.bindings is an array of row objects
  return json.results.bindings.map(row =>
    Object.fromEntries(
      Object.entries(row).map(([k, v]) => [k, v.value])
    )
  );
}
```

**Usage:**

```js
const rows = await querySparql(`
  PREFIX : <https://agriculture.ld.admin.ch/plant-protection/>
  PREFIX schema: <http://schema.org/>
  SELECT DISTINCT ?product ?productName ?cropName ?pestName ?areaName
  WHERE { ... }
`);

rows.forEach(r => console.log(r.productName, r.cropName, r.pestName));
```

