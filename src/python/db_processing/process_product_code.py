import duckdb

def process_product_code(db_path: str = 'data/processed/psmv-data.duckdb'):
    tables = {
        "ProductCodeR":        "code_id",
        "ProductCodeS":        "code_id",
        "ProductDangerSymbol": "code_id",
        "ProductSignalWords":  "code_id",
    }

    con = duckdb.connect(db_path)

    for table, id_col in tables.items():
        sql_script = f"""
        CREATE OR REPLACE VIEW pivot_vals AS
        SELECT
            i.{id_col},
            MAX(CASE WHEN c.language = 'en' THEN c.value END) AS EN,
            MAX(CASE WHEN c.language = 'de' THEN c.value END) AS DE,
            MAX(CASE WHEN c.language = 'fr' THEN c.value END) AS FR,
            MAX(CASE WHEN c.language = 'it' THEN c.value END) AS IT,
            MAX(c.code_value)   AS code_value,
            MAX(c.text_key)     AS text_key
        FROM {table} i
        LEFT JOIN Code c ON i.{id_col} = c.code_id
        GROUP BY i.{id_col};

        CREATE OR REPLACE TABLE {table}Code AS
        SELECT
            i.*,
            p.EN,
            p.DE,
            p.FR,
            p.IT,
            p.code_value,
            p.text_key
        FROM {table} i
        LEFT JOIN pivot_vals p ON i.{id_col} = p.{id_col};
        """

        con.execute(sql_script)

        row_count = con.execute(f"SELECT COUNT(*) FROM {table}Code").fetchone()[0]
        print(f"[i] {table}Code created with {row_count} rows.")

    # Unify all 4 tables into a single GHS lookup table
    con.execute("""
        CREATE OR REPLACE TABLE ProductGHS AS
        SELECT product_id, code_id FROM ProductCodeRCode        WHERE code_id IS NOT NULL AND code_id != ''
        UNION ALL
        SELECT product_id, code_id FROM ProductCodeSCode        WHERE code_id IS NOT NULL AND code_id != ''
        UNION ALL
        SELECT product_id, code_id FROM ProductDangerSymbolCode WHERE code_id IS NOT NULL AND code_id != ''
        UNION ALL
        SELECT product_id, code_id FROM ProductSignalWordsCode  WHERE code_id IS NOT NULL AND code_id != ''
    """)
    row_count = con.execute("SELECT COUNT(*) FROM ProductGHS").fetchone()[0]
    print(f"[i] ProductGHS created with {row_count} rows.")

    con.close()

if __name__ == "__main__":
    process_product_code()