import pandas as pd

# -----------------------------------------------------------------------------
# Config
# -----------------------------------------------------------------------------
PRODUCT_CSV = "data/processed/Product.csv"
ORG_CSV = "data/processed/Organisation.csv"
LINK_CSV = "data/processed/ProductOrganisation.csv"

SEP = ","          # ggf. anpassen: "," oder "\t"
ENCODING = "utf-8" # ggf. anpassen

OUT_INVALID_ROWS = "invalid_productorganisation_rows.csv"
OUT_DUPLICATE_LINKS = "duplicate_links.csv"

# -----------------------------------------------------------------------------
# Load (alle Keys als String, damit keine führenden Nullen verloren gehen)
# -----------------------------------------------------------------------------
df_product = pd.read_csv(PRODUCT_CSV, sep=SEP, encoding=ENCODING, dtype=str)
df_org = pd.read_csv(ORG_CSV, sep=SEP, encoding=ENCODING, dtype=str)
df_link = pd.read_csv(LINK_CSV, sep=SEP, encoding=ENCODING, dtype=str)

# -----------------------------------------------------------------------------
# Columns (deine umbenannten Spalten)
# -----------------------------------------------------------------------------
PK_PRODUCT_COL = "product_id"       # Product
PK_ORG_COL = "organisation_id"      # Organisation

FK_PRODUCT_COL = "product_id"       # ProductOrganisation
FK_ORG_COL = "organisation_id"      # ProductOrganisation

# -----------------------------------------------------------------------------
# Helper: clean key series
# -----------------------------------------------------------------------------
def clean_key(s: pd.Series) -> pd.Series:
    s = s.astype(str).str.strip()
    s = s.replace({"": pd.NA, "nan": pd.NA, "None": pd.NA})
    return s.dropna()

# -----------------------------------------------------------------------------
# Prepare key sets
# -----------------------------------------------------------------------------
pk_product = clean_key(df_product[PK_PRODUCT_COL])
pk_org = clean_key(df_org[PK_ORG_COL])

fk_product = clean_key(df_link[FK_PRODUCT_COL])
fk_org = clean_key(df_link[FK_ORG_COL])

set_pk_product = set(pk_product)
set_pk_org = set(pk_org)

# -----------------------------------------------------------------------------
# Header / Kontext
# -----------------------------------------------------------------------------
print("\n" + "=" * 80)
print("REFERENZINTEGRITÄT m:n")
print(f"- {LINK_CSV} bildet die m:n-Beziehung zwischen {PRODUCT_CSV} (Produkte) und {ORG_CSV} (Organisationen) ab.")
print(f"- Erwartung: Jede Zeile in {LINK_CSV} referenziert genau ein Produkt ({FK_PRODUCT_COL}) und genau eine Organisation ({FK_ORG_COL}).")
print(f"- Beide IDs müssen als Primärschlüssel in den Stammdatentabellen existieren:")
print(f"    * {PRODUCT_CSV}.{PK_PRODUCT_COL}")
print(f"    * {ORG_CSV}.{PK_ORG_COL}")
print("=" * 80)

print("\n=== INPUT-UMFANG ===")
print(f"Produkte (Stammdaten):        {len(df_product):>10} Zeilen")
print(f"Organisationen (Stammdaten):  {len(df_org):>10} Zeilen")
print(f"Links (m:n):                  {len(df_link):>10} Zeilen")

# -----------------------------------------------------------------------------
# 1) FK integrity checks (Link -> Parents)
# -----------------------------------------------------------------------------
invalid_products = fk_product[~fk_product.isin(set_pk_product)]
invalid_orgs = fk_org[~fk_org.isin(set_pk_org)]

print("\n=== CHECK 1: FOREIGN-KEY MATCH (LINK -> STAMMDATEN) ===")
print(f"Ungültige {FK_PRODUCT_COL} in {LINK_CSV} (kein Match in {PRODUCT_CSV}.{PK_PRODUCT_COL}): {len(invalid_products)}")
print(f"Ungültige {FK_ORG_COL} in {LINK_CSV} (kein Match in {ORG_CSV}.{PK_ORG_COL}): {len(invalid_orgs)}")

# -----------------------------------------------------------------------------
# 1b) Bad link rows (mind. ein ungültiger FK)  <-- MINIMAL ergänzt
# -----------------------------------------------------------------------------
link_prod = df_link[FK_PRODUCT_COL].astype(str).str.strip()
link_org = df_link[FK_ORG_COL].astype(str).str.strip()

mask_bad = (~link_prod.isin(set_pk_product)) | (~link_org.isin(set_pk_org))
bad_rows = df_link[mask_bad].copy()

# -----------------------------------------------------------------------------
# 2) Orphans (Parents ohne Link)
# -----------------------------------------------------------------------------
orphan_products = pk_product[~pk_product.isin(set(fk_product))]
orphan_orgs = pk_org[~pk_org.isin(set(fk_org))]

print("\n=== CHECK 2: ORPHANS (STAMMDATEN OHNE LINK) ===")
print(f"Produkte in {PRODUCT_CSV} ohne Eintrag in {LINK_CSV}: {len(orphan_products)}")
print(f"Organisationen in {ORG_CSV} ohne Eintrag in {LINK_CSV}: {len(orphan_orgs)}")

# -----------------------------------------------------------------------------
# 3) Duplicate links (identische m:n-Paare mehrfach)
# -----------------------------------------------------------------------------
dupes_mask = df_link.duplicated(subset=[FK_PRODUCT_COL, FK_ORG_COL], keep=False)
dup_links = df_link[dupes_mask].copy()

print("\n=== CHECK 3: DUPLIKATE LINKS (GLEICHES PAAR MEHRFACH) ===")
print(f"Doppelte (product_id, organisation_id)-Paare (Zeilen): {int(dupes_mask.sum())}")

# Optional: Top-Duplikate als nachvollziehbare Tabelle
if len(dup_links) > 0:
    dup_pairs = (
        dup_links.assign(n=1)
                 .groupby([FK_PRODUCT_COL, FK_ORG_COL])["n"]
                 .sum()
                 .sort_values(ascending=False)
                 .head(10)
                 .reset_index()
                 .rename(columns={"n": "occurrences"})
    )

# -----------------------------------------------------------------------------
# 5) Summary
# -----------------------------------------------------------------------------
report = {
    "rows_Product": len(df_product),
    "rows_Organisation": len(df_org),
    "rows_ProductOrganisation": len(df_link),
    "invalid_product_fks": int(len(invalid_products)),
    "invalid_org_fks": int(len(invalid_orgs)),
    "invalid_link_rows": int(len(bad_rows)),
    "orphan_products": int(len(orphan_products)),
    "orphan_orgs": int(len(orphan_orgs)),
    "duplicate_links_rows": int(dupes_mask.sum()),
}

print("\n=== SUMMARY (KURZ) ===")
summary_df = (
    pd.Series(report, name="value")
      .to_frame()
      .reset_index()
      .rename(columns={"index": "metric"})
)
print(summary_df.to_string(index=False))
print("=" * 80 + "\n")
