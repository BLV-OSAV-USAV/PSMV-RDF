import duckdb

def process_substance_code():
    con = duckdb.connect('data/processed/psmv-data.duckdb')

    sql_script = """
    CREATE OR REPLACE VIEW code_typed AS
    SELECT *,
        CASE
            WHEN TRY_CAST(code_id AS INTEGER) IS NOT NULL THEN 'legacy'
            ELSE 'uuid'
        END AS id_type
    FROM Code
    WHERE text_key = 'Substance';

    CREATE OR REPLACE VIEW pivot_vals AS
    SELECT
        code_id AS nk_codetable_substance_id,
        id_type,
        MAX(CASE WHEN language = 'en' THEN value END) AS EN,
        MAX(CASE WHEN language = 'de' THEN value END) AS DE,
        MAX(CASE WHEN language = 'fr' THEN value END) AS FR,
        MAX(CASE WHEN language = 'it' THEN value END) AS IT
    FROM code_typed
    GROUP BY code_id, id_type;

    CREATE OR REPLACE TABLE ProductIngredientCode AS
    SELECT
        i.*,
        c.id_type,
        p.EN,
        p.DE,
        p.FR,
        p.IT
    FROM ProductIngredient i
    LEFT JOIN code_typed c
        ON LOWER(i.nk_codetable_substance_id) = LOWER(c.code_id)
    LEFT JOIN pivot_vals p
        ON c.code_id = p.nk_codetable_substance_id;
    """

    con.execute(sql_script)

    row_count = con.execute(
        "SELECT COUNT(*) FROM ProductIngredientCode"
    ).fetchone()[0]

    print(f"[i] ProductIngredientCode table created successfully with {row_count} rows.")

    con.close()


if __name__ == "__main__":
    process_substance_code()