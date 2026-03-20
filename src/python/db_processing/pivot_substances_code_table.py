import duckdb

def process_substance_code():
    """
    Creates ProductIngredientCode table with multilingual substance names
    by merging ProductIngredient and Code tables in DuckDB.
    """
    con = duckdb.connect('data/processed/psmv-data.duckdb')

    sql_script = """
    CREATE OR REPLACE VIEW merged AS
    SELECT
        i.*,
        c.value,
        c.language
    FROM ProductIngredient i
    LEFT JOIN Code c
        ON i.nk_codetable_substance_id = c.code_id
        AND i.IUPAC_name = c.IUPAC_name;

    CREATE OR REPLACE VIEW pivot_vals AS
    SELECT
        nk_codetable_substance_id,
        MAX(CASE WHEN language = 'en' THEN value END) AS EN,
        MAX(CASE WHEN language = 'de' THEN value END) AS DE,
        MAX(CASE WHEN language = 'fr' THEN value END) AS FR,
        MAX(CASE WHEN language = 'it' THEN value END) AS IT
    FROM merged
    GROUP BY nk_codetable_substance_id;

    CREATE OR REPLACE TABLE ProductIngredientCode AS
    SELECT
        i.*,
        p.EN,
        p.DE,
        p.FR,
        p.IT
    FROM ProductIngredient i
    LEFT JOIN pivot_vals p
        ON i.nk_codetable_substance_id = p.nk_codetable_substance_id;
    """

    con.execute(sql_script)

    # Get number of rows in the final table
    row_count = con.execute("SELECT COUNT(*) FROM ProductIngredientCode").fetchone()[0]
    
    print(f"[i] ProductIngredientCode table created successfully with {row_count} rows.")

    con.close()

if __name__ == "__main__":
    process_substance_code()
