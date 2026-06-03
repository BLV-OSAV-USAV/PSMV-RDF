import duckdb

def process_indication_product():
    con = duckdb.connect('data/processed/psmv-data.duckdb')

    con.execute("""
    CREATE OR REPLACE TABLE ProductIndicationExpanded AS
    SELECT 
        P.product_id,
        LOWER(TRIM(P.product_ref_or_id)) AS product_ref_or_id,
        LOWER(TRIM(PI.indication))       AS indication
    FROM Product P
    LEFT JOIN ProductIndication PI
        ON LOWER(TRIM(PI.product_ref_or_id)) = LOWER(TRIM(P.product_ref_or_id));
    """)
    
    row_count = con.execute("SELECT COUNT(*) FROM ProductIndicationExpanded").fetchone()[0]
    print(f"[i] ProductIndicationExpanded created with {row_count} rows.")

    con.close()

if __name__ == "__main__":
    process_indication_product()