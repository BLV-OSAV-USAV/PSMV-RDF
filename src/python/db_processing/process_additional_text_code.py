import duckdb

def process_additional_text_code():
    con = duckdb.connect('data/processed/psmv-data.duckdb')

    sql_script = """
    CREATE OR REPLACE TABLE AdditionalTextCode AS
    WITH latest AS (
        SELECT
            LOWER(TRIM(code_id)) AS code_id,
            text_key,
            language,
            NULLIF(TRIM(value), '') AS value
        FROM Code
        WHERE text_key IN (
            'CultureAdditionalText',
            'PestAdditionalText',
            'IngredientAdditionalText'
        )
        QUALIFY ROW_NUMBER() OVER (
            PARTITION BY LOWER(TRIM(code_id)), text_key, language
            ORDER BY version DESC
        ) = 1
    )
    SELECT
        code_id,
        text_key,
        MAX(CASE WHEN language = 'en' THEN value END) AS EN,
        MAX(CASE WHEN language = 'de' THEN value END) AS DE,
        MAX(CASE WHEN language = 'fr' THEN value END) AS FR,
        MAX(CASE WHEN language = 'it' THEN value END) AS IT
    FROM latest
    GROUP BY code_id, text_key;
    """

    con.execute(sql_script)

    counts = con.execute("""
        SELECT text_key, COUNT(*) AS n
        FROM AdditionalTextCode
        GROUP BY text_key
        ORDER BY text_key
    """).fetchall()

    for text_key, n in counts:
        print(f"[i] AdditionalTextCode: {n} {text_key} codes.")

    con.close()


if __name__ == "__main__":
    process_additional_text_code()