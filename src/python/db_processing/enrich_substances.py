import yaml
import duckdb
import pandas as pd


def load_substances_mapping(
    yaml_path: str = "data/mapping/mapping_substances.yaml",
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

    result = df[["schemaname"]].drop_duplicates()

    for col in list_cols:
        if col in df.columns:
            exploded = (
                df[["schemaname", col]]
                .explode(col)
                .dropna(subset=[col])
            )
            result = result.merge(exploded, on="schemaname", how="left")

    for col in list_cols:
        if col not in result.columns:
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
    con.close()
    print(f"Inserted {len(result)} rows into '{db_path}' (table: substances_mapping).")


if __name__ == "__main__":
    load_substances_mapping()