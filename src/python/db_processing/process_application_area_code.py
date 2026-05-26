import duckdb

def process_application_area_code(db_path: str = 'data/processed/psmv-data.duckdb'):
    con = duckdb.connect(db_path)

    con.execute("""
        CREATE OR REPLACE TABLE ApplicationAreaCode AS
        SELECT 
            code_id,
            MAX(CASE WHEN language = 'en' THEN value END) AS EN,
            MAX(CASE WHEN language = 'de' THEN value END) AS DE,
            MAX(CASE WHEN language = 'fr' THEN value END) AS FR,
            MAX(CASE WHEN language = 'it' THEN value END) AS IT,
            MAX(min_interval_between_uses) AS min_interval_between_uses
        FROM Code
        WHERE text_key = 'ApplicationComment'
    GROUP BY code_id
    """)

    row_count = con.execute("SELECT COUNT(*) FROM ApplicationAreaCode").fetchone()[0]
    print(f"[i] ApplicationAreaCode created with {row_count} rows.")

    con.close()

if __name__ == "__main__":
    process_application_area_code()