import os
import sys
import pandas as pd
import yaml


def process_data():
    """
    Processes raw data files.
    """

    data_name = "data/raw/AllProducts280126.csv" # change if real export name is known
    mapping_col_table = "data/mapping/mapping_colums.yaml"
    mapping_value_table = "data/mapping/mapping_values.yaml"

    # Read data as df
    df = pd.read_csv(data_name, header=0, na_values=["NULL"],sep=';')

    # Load YAML mapping
    with open(mapping_col_table, "r") as f:
        mapping_col_dict = yaml.safe_load(f)

    with open(mapping_value_table, "r") as f:
        mapping_value_dict = yaml.safe_load(f)
   
    # Map cols based on mapping_col_dict 
    df = df.rename(columns=mapping_col_dict)

    # Map values based on  mapping_value_dict
    for col, mapping in mapping_value_dict.items():
        if col in df.columns:
            df[col] = df[col].map(mapping).fillna(df[col])

    # Save processed file
    df.to_csv("data/processed/AllProducts_Renamed.csv", index=False)


if __name__ == "__main__":
    process_data()
