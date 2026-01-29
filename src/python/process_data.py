import os
import sys
import pandas as pd


def process_data():
    """
    Processes raw data files.
    """

    data_name = "data/raw/AllProducts280126.csv"
    mapping_table = "data/mapping/mapping.csv"

    # Read data
    d = pd.read_csv(data_name,
        header=0,
        na_values=["NULL"],
        sep=';'
    )

    # Read mapping table
    mapping_df = pd.read_csv(mapping_table,
        header=0,
        sep=','
    )

    for col in mapping_df["column"].unique():
            mapping = (
                mapping_df[mapping_df["column"] == col].set_index("old_value")["new_value"].to_dict()
            )
    
    
    df = df.rename(columns=dict(zip(mapping.source, mapping.target)))


    print(df.head(10))



if __name__ == "__main__":
    process_data()
