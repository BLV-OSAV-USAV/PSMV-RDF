import duckdb

def process_organisation(db_path: str = 'data/processed/psmv-data.duckdb'):
    con = duckdb.connect(db_path)

    con.execute("""
        CREATE OR REPLACE TABLE OrganisationCode AS
        SELECT 
            o.*,
            c.city_name
        FROM Organisation o
        LEFT JOIN (
            SELECT code_id, MAX(value) AS city_name 
            FROM Code 
            GROUP BY code_id
        ) c ON o.city_id = c.code_id
    """)

    row_count = con.execute("SELECT COUNT(*) FROM OrganisationCode").fetchone()[0]
    print(f"[i] OrganisationCode created with {row_count} rows.")

    con.close()

if __name__ == "__main__":
    process_organisation()