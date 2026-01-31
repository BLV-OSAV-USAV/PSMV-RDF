import os
import sys
import pandas as pd
import yaml

def process_data():
    """
    Processes raw data files.
    """

    mapping_datasets = "data/mapping/mapping_datasets.yaml"
    mapping_col_table = "data/mapping/mapping_colums.yaml"
    mapping_value_table = "data/mapping/mapping_values.yaml"

    out_dir = "data/processed"

    # Load mappings

    with open(mapping_datasets, "r") as f:
        datasets = yaml.safe_load(f).get("datasets", {})
        selected = list(datasets.keys())

    with open(mapping_col_table, "r") as f:
        mapping_col_dict = yaml.safe_load(f) or {}

    with open(mapping_value_table, "r") as f:
        mapping_value_dict = yaml.safe_load(f) or {}


    # Process each dataset

    errors = []
    for dataset_key in selected:
        cfg = datasets[dataset_key]

        try:
            data_name = cfg["input"]
            sep = cfg.get("delimiter", ";")
            encoding = cfg.get("encoding", "utf-8")

            print(f"\n=== Processing {dataset_key} ===")
            print(f"Input: {data_name}")

            # Read data
            df = pd.read_csv(
                data_name,
                header=0,
                na_values=["NULL"],
                sep=sep,
                encoding=encoding,
                low_memory=False,
            )

            # dataset-spezifisches Column-Mapping
            df = df.rename(columns=mapping_col_dict.get(dataset_key, mapping_col_dict))

            # dataset-spezifisches Value-Mapping
            value_map = mapping_value_dict.get(dataset_key, mapping_value_dict)
            for col, mapping in value_map.items():
                if col in df.columns and isinstance(mapping, dict):
                    df[col] = df[col].map(mapping).fillna(df[col])

            # Write output
            out_path = os.path.join(out_dir, f"{dataset_key}.csv")
            df.to_csv(out_path, index=False)
            print(f"Written: {out_path} ({len(df):,} rows)")

        except Exception as e:
            msg = f"ERROR in {dataset_key}: {e}"
            print(msg)
            errors.append(msg)   

if __name__ == "__main__":
    process_data()
