import duckdb

def process_indication_code():
    con = duckdb.connect('data/processed/psmv-data.duckdb')

    tables = {
        "IndicationCulture":     "culture_id",
        "IndicationCultureForm": "culture_form_id",
        "IndicationMeasure":     "indication_measure_id",
        "IndicationTimeMeasure": "indication_time_measure_id",
        "IndicationObligation":  "indication_obligation_id",
        "IndicationPest":        "indication_pest_id",
    }

    for table, id_col in tables.items():
        sql_script = f"""
        CREATE OR REPLACE VIEW pivot_vals AS
        SELECT
            i.{id_col},
            MAX(CASE WHEN c.language = 'en' THEN c.value END) AS EN,
            MAX(CASE WHEN c.language = 'de' THEN c.value END) AS DE,
            MAX(CASE WHEN c.language = 'fr' THEN c.value END) AS FR,
            MAX(CASE WHEN c.language = 'it' THEN c.value END) AS IT,
            MAX(c.code_value)              AS code_value,
            MAX(c.IUPAC_name)              AS IUPAC_name,
            MAX(c.text_key)                AS text_key,
            MAX(c.bbch_stage_from)         AS bbch_stage_from,
            MAX(c.bbch_stage_to)           AS bbch_stage_to,
            MAX(c.min_interval_between_uses) AS min_interval_between_uses,
            MAX(c.max_applications)        AS max_applications,
            MAX(c.unit_max_applications)   AS unit_max_applications,
            MAX(c.infofito_ref)            AS infofito_ref
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
            p.IUPAC_name,
            p.text_key,
            p.bbch_stage_from,
            p.bbch_stage_to,
            p.min_interval_between_uses,
            p.max_applications,
            p.unit_max_applications,
            p.infofito_ref
        FROM {table} i
        LEFT JOIN pivot_vals p ON i.{id_col} = p.{id_col};
        """

        con.execute(sql_script)

        row_count = con.execute(f"SELECT COUNT(*) FROM {table}Code").fetchone()[0]
        print(f"[i] {table}Code created successfully with {row_count} rows.")

    con.close()

if __name__ == "__main__":
    process_indication_code()