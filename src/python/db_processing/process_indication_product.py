import duckdb

def process_indication_product():
    con = duckdb.connect('data/processed/psmv-data.duckdb')

    con.execute("""
    CREATE OR REPLACE TABLE ProductIndicationExpanded AS
    SELECT 
        P.product_id,
        P.product_ref_or_id,
        AC.indication
    FROM Product P
    LEFT JOIN ApplicationComment AC
        ON AC.application_comment_id = AC.application_comment_id;
    """)
    
    row_count = con.execute("SELECT COUNT(*) FROM ProductIndicationExpanded").fetchone()[0]
    print(f"[i] ProductIndicationExpanded created with {row_count} rows.")
    print(con.execute("SELECT * FROM ProductIndicationExpanded LIMIT 10").df())

    con.close()

if __name__ == "__main__":
    process_indication_product()