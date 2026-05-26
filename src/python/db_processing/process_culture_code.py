import duckdb

def process_culture_code(db_path: str = 'data/processed/psmv-data.duckdb'):
    con = duckdb.connect(db_path)

    con.execute("""
        CREATE OR REPLACE TABLE CultureCode AS
        SELECT 
            code_id,
            MAX(parent_id) AS parent_id,
            MAX(CASE WHEN language = 'en' THEN value END) AS EN,
            MAX(CASE WHEN language = 'de' THEN value END) AS DE,
            MAX(CASE WHEN language = 'fr' THEN value END) AS FR,
            MAX(CASE WHEN language = 'it' THEN value END) AS IT
        FROM Code
        WHERE text_key = 'Culture'
        GROUP BY code_id
    """)

    row_count = con.execute("SELECT COUNT(*) FROM CultureCode").fetchone()[0]
    print(f"[i] CultureCode created with {row_count} rows.")

    con.close()

if __name__ == "__main__":
    process_culture_code()