import pandas as pd
import csv

# Choose one
DATANAME = "data/raw/code280126.csv"
COLS =  9

DATANAME = "data/raw/AllProducts280126.csv"
COLS =  16


with open(DATANAME, "r") as f:
    for i, line in enumerate(f, 1):
        if len(line.split(";")) != COLS:  
            print(f"Line {i} has {len(line.split(','))} columns")

df = pd.read_csv(DATANAME,
    header=0,
    na_values=["NULL"],
    sep=';'
)

print(df.head(10))

df.to_csv("data/processed/test.csv")
