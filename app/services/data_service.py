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
# subset tells pandas only check this column , ignore all others. We wrap column in [ ] because subset expects a list of column names even if you're only checking one.
#return df.dropna() — if no column was specified, fall back to dropping any row with any missing value, anywhere. 
# check col ka liya aur drop rows ko this is the work        
def drop_missing_values(df: pd.DataFrame, column: str | None = None) -> pd.DataFrame:
    """Drops rows with missing values, optionally limited to one column."""
    if column:
        return df.dropna(subset=[column])
    return df.dropna()


def fill_missing_values(df, column, strategy):
    """Fills missing values in a column using mean, median, or mode."""
    if strategy == "mean":
        value = df[column].mean()
    elif strategy == "median":
        value = df[column].median()
    elif strategy == "mode":
        value = df[column].mode()[0] # if tie then first value from list
    # if anyone type "avg" instead of mean then throw error     
    else:
        raise ValueError("strategy must be 'mean', 'median', or 'mode'")

    df[column] = df[column].fillna(value)
    return df
# count duplicates 
# duplicated() is used to marks the first apprience as false and second apperience as true 
# we use subset just to check ensure the checking of duplicates in column wise and it take list as input even if we have single columns
# without subset our duplicate count was 0 becasuse it was checking for entire rows and matching columns , so ultimatly id is unique which leads to count=0 that's why we upgraded 
def get_duplicate_count(df, subset=None):
    """Returns how many duplicate rows exist, optionally checking only specific columns."""
    return int(df.duplicated(subset=subset).sum())


def remove_duplicates(df, subset=None):
    """Removes duplicate rows, optionally checking only specific columns."""
    return df.drop_duplicates(subset=subset)
# it will return DF based on selected columns only means customization    
def select_columns(df, columns):
    
    return df[columns]    
