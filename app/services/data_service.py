import io
import pandas as pd
from fastapi import UploadFile


async def read_csv_file(file: UploadFile) -> pd.DataFrame:
    """Reads an uploaded CSV file into a pandas DataFrame."""
    contents = await file.read()
    df = pd.read_csv(io.BytesIO(contents))
    return df
#we dont use async because it just do normal math operation
#FastAPI doesn't know how to turn a pandas Series into JSON directly, so .to_dict()    
def get_missing_values(df: pd.DataFrame) -> dict[str, int]:
    """Returns the count of missing values for each column."""
    missing_counts = df.isnull().sum()
    return missing_counts.to_dict() 
#df.dtypes doesn't return plain text — it returns special pandas type objects so API can't understand the it so we convert it in to str 
def get_data_types(df: pd.DataFrame) -> dict[str, str]:
    """Returns the data type of each column as a string."""
    return df.dtypes.astype(str).to_dict()

# to understand statistical information of each cols 
#describe() naturally has a row and column structure, .to_dict() here gives you a nested dictionary — a dictionary of dictionaries.
def get_basic_statistics(df: pd.DataFrame) -> dict:
    """Returns summary statistics for numeric columns."""
    return df.describe().to_dict()     