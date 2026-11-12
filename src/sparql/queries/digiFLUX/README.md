# LINDAS PSMV data integration for digiFLUX

This subdirectory contains a bunch of SPARQL queries that export the Swiss registry of plant protection products (SRPPP) from LINDAS in the shape of the digiFLUX product catalogue for downstream integration.

## Run all SPARQL queries and download data from LINDAS

To start the integration process, navigate into this directory, run `make` (equivalent to `make json`), or `make csv` (or `xml`, `tsv`) to execute all queries in `queries/` and write the results to `data/<format>/`.

Use `make clean` to remove all downloaded files.

## Mapping to the digiFLUX DDL

One table per entity, one table per relationship. Every entity table starts with `id`
(the primary key, fits the DDL's `nvarchar(50)` key columns) followed by `iri` (the LINDAS IRI, informational only). Relationship tables consist of two id columns named after the tables they join, plus attributes of the relationship where the source has them. Column names and types otherwise follow [`docs/schema.sql`](docs/schema.sql).

Identifiers are

- the federal admission number for products,
- the class name for product types,
- and the Infofito UUID for everything else.

| Query                                                         | digiFLUX table                                                 | Key                           |
|---------------------------------------------------------------|----------------------------------------------------------------|-------------------------------|
| 01_plant_protection_product                                   | plant_protection_product                                       | id (admission number)         |
| 02_plant_protection_product_alternate_id                      | alternate_id                                                   | product id + value            |
| 03_plant_protection_product_category                          | plant_protection_product_category                              | id (class name)               |
| 04_plant_protection_product_plant_protection_product_category | plant_protection_product_plant_protection_product_category     | product id + category id      |
| 05_mail_address                                               | mail_address                                                   | id (organisation UUID)        |
| 06_substance                                                  | substance                                                      | id                            |
| 07_ingredient                                                 | ingredient                                                     | product id + substance id     |
| 08_indication                                                 | indication (+ plant_protection_product_indication as a column) | id                            |
| 09_indication_plant_protection_product_culture                | indication_plant_protection_product_culture                    | indication id + culture id    |
| 10_plant_protection_product_culture                           | plant_protection_product_culture                               | id                            |
| 11_plant_protection_product_culture_parent                    | `none`                                                         | culture id + parent id        |
| 12_pathogen                                                   | pathogen                                                       | id                            |
| 13_indication_pathogen                                        | indication_pathogen                                            | indication id + pathogen id   |
| 14_hazard_label                                               | hazard_label (GHS elements and plant protection statements)    | id                            |
| 15_plant_protection_product_hazard_label                      | plant_protection_product_hazard_label                          | product id + label id         |
| 16_obligation                                                 | `none`                                                         | id                            |
| 17_indication_obligation                                      | `none`                                                         | indication id + obligation id |
| 18_application_comment                                        | `none`                                                         | id                            |
| 19_indication_application_comment                             | `none`                                                         | indication id + comment id    |
| 20_application_area                                           | `none` (referenced by 08_indication.application_area_id)       | id                            |
| 21_formulation_type                                           | `none`                                                         | id                            |
| 22_plant_protection_product_formulation_type                  | `none`                                                         | product id + formulation id   |

_Note: Single-valued relationships (indication to product, indication to application area, product to permission holder, product to reference product) are columns on the entity table rather than separate tables. Entities marked `none` have no counterpart in the DDL and are exported in the same style so that they can be modelled later if needed._

## Known gaps and conventions

- `permission_holder` (`nvarchar(20)`, UID/BUR) is not available in Infofito.
- Ingredients are blank nodes in PSMV and have neither an id nor an IRI. The pair (product id, substance id) is unique and serves as the key.
- Product names are language-neutral brand names and are repeated in all four `designation_*` columns.
- Waiting period is exported in days (`waiting_period int`); weeks are multiplied by 7. The original value and unit are kept in `waiting_period_source_value/_unit`.
- Dosage has only min/max in Infofito, mapped to `dosage_from` / `dosage_to`. The expenditure (amount per area) is exported as extra columns.
- Ingredient shares come in percent and/or g/l: percent goes to `quantity`/`unit`,  g/l to `quantity2`/`unit2`. The ingredient additional text fills `designation_*`.
- Country code and name come from the LINDAS country register in the graph `https://lindas.admin.ch/territorial`; every lookup outside the PSMV graph names its graph explicitly. The register's `schema:alternateName` is a common abbreviation, not strictly ISO 3166-1 alpha-2: the United Kingdom is `UK` there, not `GB`.
- Street and house number are not separated in Infofito; the full street address goes to `street`. Non-numeric P.O. box texts go to `address_line1`.
- Hazard label codes are not unique (e.g. H318 appears on two elements, phrase codes of plant protection statements are optional); the UUID `id` is the key.
- Obligation texts (no digiFLUX table) can exceed 255 characters, up to about 800. The indication `unit` fits `nvarchar(20)` with the longest value at exactly 20 characters.
- Product categories are labelled in English only in Infofito; `designation_de/fr/it` are exported but empty.
- Columns that Infofito cannot fill (approval_date, usage_category, valid_from/to, eppo_code, molecular_formula, admission_type, ...) are omitted rather than exported empty.
- Three indications refer to products that are no longer in the dataset. They are excluded from the indication table and from all relationship tables that reference indications.
- `:referenceProductId` (6 products, all pointing to a deprecated reference product) is exported as `reference_product_source_id` on the product table only; it is not an alternate id of the product.
- Co-formulants in the substance table still have legacy primary keys in Infofito. This is likely a bug to be fixed in the future, however their `id` is still unique and can be used as a key.

## Additional documentation

The one file that best describes the entire SRPPP data structure is this one:

<https://github.com/BLV-OSAV-USAV/PSMV-RDF/blob/main/rdf/shapes/data_shape.ttl>

It contains the SHACL shapes that define the data model, including all entities, relationships, and constraints. However, it is important to note that the graph (at the moment) does not fully conform to the shapes, and some constraints are not enforced. The goal is to have a conforming graph by 2027.