import duckdb

def process_substance_code():
    con = duckdb.connect('data/processed/psmv-data.duckdb')

    sql_script = """
    CREATE OR REPLACE VIEW code_typed AS
    SELECT *,
        LOWER(TRIM(code_id)) AS norm_id,
        CASE
            WHEN TRY_CAST(code_id AS INTEGER) IS NOT NULL THEN 'legacy'
            ELSE 'uuid'
        END AS id_type
    FROM Code
    WHERE text_key = 'Substance';

    CREATE OR REPLACE VIEW pivot_vals AS
    SELECT
        norm_id AS nk_codetable_substance_id,
        id_type,
        MAX(CASE WHEN language = 'en' THEN value END) AS EN,
        MAX(CASE WHEN language = 'de' THEN value END) AS DE,
        MAX(CASE WHEN language = 'fr' THEN value END) AS FR,
        MAX(CASE WHEN language = 'it' THEN value END) AS IT
    FROM code_typed
    GROUP BY norm_id, id_type;

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
        ON LOWER(TRIM(i.nk_codetable_substance_id)) = c.norm_id
    LEFT JOIN pivot_vals p
        ON c.norm_id = p.nk_codetable_substance_id;
    """

    con.execute(sql_script)

    row_count = con.execute(
        "SELECT COUNT(*) FROM ProductIngredientCode"
    ).fetchone()[0]

    print(f"[i] ProductIngredientCode table created successfully with {row_count} rows.")

    con.close()


if __name__ == "__main__":
    process_substance_code()