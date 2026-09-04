import duckdb

def process_product_formulation(db_path: str = 'data/processed/psmv-data.duckdb'):
    con = duckdb.connect(db_path)

    con.execute("""
        CREATE OR REPLACE TABLE ProductFormulation AS
        SELECT 
            LOWER(TRIM(p.product_ref_or_id)) AS product_ref_or_id,
            LOWER(TRIM(p.code_id)) AS code_id,
            p.short_name,
            MAX(c.code_value) AS code_value,
            MAX(CASE WHEN c.language = 'en' THEN c.value END) AS EN,
            MAX(CASE WHEN c.language = 'de' THEN c.value END) AS DE,
            MAX(CASE WHEN c.language = 'fr' THEN c.value END) AS FR,
            MAX(CASE WHEN c.language = 'it' THEN c.value END) AS IT
        FROM ProductFormulationCode p
        LEFT JOIN Code c
          ON LOWER(TRIM(p.code_id)) = LOWER(TRIM(c.code_id))
        WHERE p.product_ref_or_id IS NOT NULL 
          AND p.code_id IS NOT NULL
        GROUP BY 1, 2, 3
    """)

    row_count = con.execute("SELECT COUNT(*) FROM ProductFormulation").fetchone()[0]
    print(f"[i] ProductFormulation created with {row_count} rows.")

    con.close()


def process_formulation_code(db_path: str = 'data/processed/psmv-data.duckdb'):
    con = duckdb.connect(db_path)

    con.execute("""
        CREATE OR REPLACE TABLE FormulationCode AS
        SELECT 
            LOWER(TRIM(c.code_id)) AS code_id,
            MAX(c.code_value) AS code_value,
            MAX(CASE WHEN c.language = 'en' THEN c.value END) AS EN,
            MAX(CASE WHEN c.language = 'de' THEN c.value END) AS DE,
            MAX(CASE WHEN c.language = 'fr' THEN c.value END) AS FR,
            MAX(CASE WHEN c.language = 'it' THEN c.value END) AS IT
        FROM Code c
        WHERE LOWER(TRIM(c.code_id)) IN (
            SELECT DISTINCT LOWER(TRIM(code_id))
            FROM ProductFormulationCode
            WHERE code_id IS NOT NULL
        )
        GROUP BY LOWER(TRIM(c.code_id))
    """)

    row_count = con.execute("SELECT COUNT(*) FROM FormulationCode").fetchone()[0]
    missing = con.execute("""
        SELECT COUNT(*) FROM FormulationCode
        WHERE DE IS NULL OR FR IS NULL
    """).fetchone()[0]

    print(f"[i] FormulationCode created with {row_count} rows.")
    if missing:
        print(f"[!] {missing} codes are missing a DE or FR label.")

    con.close()


if __name__ == "__main__":
    process_product_formulation()
    process_formulation_code()