import os 
import sys
import pandas as pd
import yaml
import csv
import duckdb

def process_data(
    datasets_path="data/mapping/mapping_datasets.yaml",
    col_mapping_path="data/mapping/mapping_columns.yaml",
    value_mapping_path="data/mapping/mapping_values.yaml",
    out_dir="data/processed"
):
    """
    Processes raw data files based on YAML mapping configurations.
    Reads each dataset defined in the datasets mapping, applies column
    and value mappings, and writes the result as CSV to the output directory.
    Args:
        datasets_path: Path to the YAML file defining available datasets.
        col_mapping_path: Path to the YAML file with column name mappings.
        value_mapping_path: Path to the YAML file with value mappings.
        out_dir: Directory where the psmv-data.duckdb is saved.
    """
    # Ensure output folder exists
    os.makedirs(out_dir, exist_ok=True)

    con = duckdb.connect(os.path.join(out_dir, "psmv-data.duckdb"))

    # Load mappings
    with open(datasets_path, "r") as f:
        datasets = yaml.safe_load(f).get("datasets", {})
        selected = list(datasets.keys())
    print(f"[+] Loaded dataset config from {datasets_path} ({len(selected)} datasets)")

    with open(col_mapping_path, "r") as f:
        mapping_col_dict = yaml.safe_load(f) or {}
    print(f"[+] Loaded column mappings from {col_mapping_path}")

    with open(value_mapping_path, "r") as f:
        mapping_value_dict = yaml.safe_load(f) or {}
    print(f"[+] Loaded value mappings from {value_mapping_path}")

    print(f"[i] Processing {len(selected)} dataset(s): {', '.join(selected)}")

    # Process each dataset
    errors = []
    for dataset_key in selected:
        cfg = datasets[dataset_key]
        try:
            data_name = cfg["input"]
            sep = cfg.get("delimiter", ",") 
            encoding = cfg.get("encoding", "utf-8-sig")
            quotechar = '"'

            print(f"\n[+] Processing dataset: {dataset_key}")
            print(f"[i] Input: {data_name} (sep={repr(sep)}, encoding={encoding})")

            # Read data
            df = pd.read_csv(
                data_name,
                header=0,
                na_values=["NULL"],
                sep=sep,
                quotechar=quotechar,
                encoding=encoding,
                engine="python",
                compression="infer"
            )
            print(f"[i] Read {len(df):,} rows, {len(df.columns)} columns")

            # Strip headers
            df.columns = df.columns.str.strip('"')

            # Validate columns
            expected_cols = set(mapping_col_dict.get(dataset_key, {}).keys())
            actual_cols = set(df.columns)
            missing = expected_cols - actual_cols
            extra = actual_cols - expected_cols

            if len(missing) >= 1:
                raise ValueError(f"There are missing columns: {missing}")
            elif len(extra) >= 1:
                print(f"[!] Warning: unmapped columns will be dropped: {extra}")

            # Dataset specific column-mapping
            df = df.rename(columns=mapping_col_dict.get(dataset_key, {}))
            print(f"[+] Applied column mappings ({len(mapping_col_dict.get(dataset_key, {}))} renamed)")

            # Dataset specific value-mapping
            value_map = mapping_value_dict.get(dataset_key, {})
            for col, mapping in value_map.items():
                if col in df.columns and isinstance(mapping, dict):
                    df[col] = df[col].map(mapping).fillna(df[col])
            print(f"[+] Applied value mappings ({len(value_map)} column(s) mapped)")

            # Write output
            con.execute(f"CREATE OR REPLACE TABLE {dataset_key} AS SELECT * FROM df")
            print(f"[+] Saved table '{dataset_key}' ({len(df):,} rows)")

        except Exception as e:
            msg = f"ERROR in {dataset_key}: {e}"
            print(f"[!] {msg}")
            errors.append(msg)

    # Close DB connection
    con.close()

    # Exit if errors
    print(f"\n[i] Finished processing {len(selected) - len(errors)}/{len(selected)} dataset(s) successfully")
    if errors:
        print(f"[!] {len(errors)} error(s) encountered:")
        for msg in errors:
            print(f"  - {msg}")
        sys.exit(1)

if __name__ == "__main__":
    process_data()
    
