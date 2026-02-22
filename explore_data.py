import pandas as pd
import os

files = ['Emergency_Service_Routing_Cleaned.csv', 'Fire-Incidents_Final_Cleaned.csv', 'table-2-cleaned.csv']

for f in files:
    print(f'\n{"="*50}')
    print(f'File: {f}')
    print("="*50)
    df = pd.read_csv(f'data/{f}')
    print('Shape:', df.shape)
    print('Columns:', df.columns.tolist())
    print('First row:')
    print(df.iloc[0])
    print('Missing values:')
    print(df.isnull().sum())
