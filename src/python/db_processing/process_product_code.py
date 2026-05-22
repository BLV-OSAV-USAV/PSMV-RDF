import duckdb

def process_product_code(db_path: str = 'data/processed/psmv-data.duckdb'):
    con = duckdb.connect(db_path)

    con.execute("""
    CREATE OR REPLACE TABLE ProductGHS AS
    SELECT 
        p.product_ref_or_id,
        p.code_id,
        c.text_key,
        c.code_value,
        c.EN,
        c.DE,
        c.FR,
        c.IT
    FROM (
        SELECT product_ref_or_id, code_id FROM ProductCodeR
        WHERE product_ref_or_id IS NOT NULL AND code_id IS NOT NULL

        UNION ALL

        SELECT product_ref_or_id, code_id FROM ProductCodeS
        WHERE product_ref_or_id IS NOT NULL AND code_id IS NOT NULL

        UNION ALL

        SELECT product_ref_or_id, code_id FROM ProductDangerSymbol
        WHERE product_ref_or_id IS NOT NULL AND code_id IS NOT NULL

        UNION ALL

        SELECT product_ref_or_id, code_id FROM ProductSignalWords
        WHERE product_ref_or_id IS NOT NULL AND code_id IS NOT NULL
    ) p
    LEFT JOIN (
        SELECT 
            code_id,
            text_key,
            MAX(code_value) AS code_value,
            MAX(CASE WHEN language = 'en' THEN value END) AS EN,
            MAX(CASE WHEN language = 'de' THEN value END) AS DE,
            MAX(CASE WHEN language = 'fr' THEN value END) AS FR,
            MAX(CASE WHEN language = 'it' THEN value END) AS IT
        FROM Code
        GROUP BY code_id, text_key
    ) c
    ON p.code_id = c.code_id
    """)

    count = con.execute("SELECT COUNT(*) FROM ProductGHS").fetchone()[0]
    print(f"[i] ProductGHS created with {count} rows.")

    con.close()


if __name__ == "__main__":
    process_product_code()