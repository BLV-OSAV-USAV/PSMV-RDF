import duckdb

def process_indication_links(db_path: str = 'data/processed/psmv-data.duckdb'):
    tables = {
        "ProductIndicationLink":    "SELECT DISTINCT product_ref_or_id, product_indication FROM Product WHERE product_ref_or_id IS NOT NULL AND product_indication IS NOT NULL",
        "IndicationCultureLink":   "SELECT DISTINCT indication, culture_id FROM IndicationCulture WHERE indication IS NOT NULL AND culture_id IS NOT NULL",
        "IndicationPestLink":      "SELECT DISTINCT indication, indication_pest_id FROM IndicationPest WHERE indication IS NOT NULL AND indication_pest_id IS NOT NULL",
        "IndicationObligationLink":"SELECT DISTINCT indication, indication_obligation_id FROM IndicationObligation WHERE indication IS NOT NULL AND indication_obligation_id IS NOT NULL",
        "ApplicationAreaLink":     "SELECT DISTINCT indication, application_area_id FROM ApplicationArea WHERE indication IS NOT NULL AND application_area_id IS NOT NULL",
        "ApplicationCommentLink":  "SELECT DISTINCT indication, application_comment_id FROM ApplicationComment WHERE indication IS NOT NULL AND application_comment_id IS NOT NULL",
    }

    con = duckdb.connect(db_path)

    for target, query in tables.items():
        try:
            con.execute(f"CREATE OR REPLACE TABLE {target} AS {query}")
            row_count = con.execute(f"SELECT COUNT(*) FROM {target}").fetchone()[0]
            print(f"[i] {target} created with {row_count} rows.")
        except Exception as e:
            print(f"[!] Warning: Could not create {target}: {e}")

    con.close()

if __name__ == "__main__":
    process_indication_links()