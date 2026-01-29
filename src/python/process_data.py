import os
import sys
import pandas as pd


def process_data():
    """
    Processes raw data files.
    """

    data_name = "data/raw/AllProducts280126.csv"
    mapping_table = "data/mapping/mapped_columns.csv"

    # Read data
    df = pd.read_csv(data_name,
        header=0,
        na_values=["NULL"],
        sep=';'
    )

    # Read mapping table
    mapping_df = pd.read_csv(mapping_table,
        header=0,
        sep=','
    )

    # Map cols
    df = df.rename(columns=dict(zip(mapping_df.source, mapping_df.target)))

    print(df.head(10))

    # Save processed file
    df.to_csv("data/processed/AllProducts280126_mapped.csv", index=False)


if __name__ == "__main__":
    process_data()
