import yaml
import duckdb
import pandas as pd


def load_substances_mapping(
    yaml_path: str = "data/mapping/mapping_substances_enriched.yaml",
    db_path: str = "data/processed/psmv-data.duckdb",
) -> None:
    with open(yaml_path) as f:
        data = yaml.safe_load(f)

    df = pd.DataFrame(data["substances"])

    list_cols = [
        "hasChebiIdentity",
        "hasPubChemCompoundIdentity",
        "hasPubChemSubstanceIdentity",
        "isDefinedByBiologicalTaxon",
    ]

    # Build one row per schemaname, joining multi-values with a separator
    result = df[["schemaname"]].drop_duplicates().copy()

    for col in list_cols:
        if col in df.columns:
            aggregated = (
                df[["schemaname", col]]
                .explode(col)
                .dropna(subset=[col])
                .groupby("schemaname")[col]
                .agg(lambda x: "|".join(x.astype(str).unique()))
                .reset_index()
            )
            result = result.merge(aggregated, on="schemaname", how="left")
        else:
            result[col] = None

    con = duckdb.connect(db_path)

    con.execute("""
        CREATE TABLE IF NOT EXISTS substances_mapping (
            schemaname                    TEXT,
            hasChebiIdentity              TEXT,
            hasPubChemCompoundIdentity    TEXT,
            hasPubChemSubstanceIdentity   TEXT,
            isDefinedByBiologicalTaxon    TEXT
        );
    """)

    con.register("df_substances", result)

    con.execute("""
        INSERT INTO substances_mapping
        SELECT schemaname,
               hasChebiIdentity,
               hasPubChemCompoundIdentity,
               hasPubChemSubstanceIdentity,
               isDefinedByBiologicalTaxon
        FROM df_substances
    """)
    
    before = con.execute("SELECT COUNT(*) FROM ProductIngredientCode").fetchone()[0]

    con.execute("""
        CREATE OR REPLACE TABLE ProductIngredientCode AS
        SELECT p.*,
               s.hasChebiIdentity,
               s.hasPubChemCompoundIdentity,
               s.hasPubChemSubstanceIdentity,
               s.isDefinedByBiologicalTaxon
        FROM ProductIngredientCode p
        LEFT JOIN (
            SELECT DISTINCT
                LOWER(TRIM(schemaname)) AS schemaname_key,
                hasChebiIdentity,
                hasPubChemCompoundIdentity,
                hasPubChemSubstanceIdentity,
                isDefinedByBiologicalTaxon
            FROM substances_mapping
        ) s
          ON LOWER(TRIM(p.DE)) = s.schemaname_key
    """)
    
    after = con.execute("SELECT COUNT(*) FROM ProductIngredientCode").fetchone()[0]


    con.close()
    print(f"[i] Inserted {len(result)} rows into '{db_path}' (table: substances_mapping).")
    print(f"[i] ProductIngredientCode: {before} rows before → {after} rows after replacement.")

if __name__ == "__main__":
    load_substances_mapping()

