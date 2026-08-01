import io
import pandas as pd
from fastapi import UploadFile
import matplotlib
#By default, matplotlib assumes it's running on a machine with a screen, ready to pop open a window (plt.show()). A server has no screen. "Agg" tells matplotlib "just render to memory/files, don't try to open any window." because hear we are working with APIs
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import seaborn as sns
#base64 — Python's built-in module for doing the binary-to-text conversion (we are encoding  img/png into raw text of str using base64 and then sore in into JSON because Json dont compatible with image ,we are storing them as str of text and then re-encode while building frontend using streamlit )
import base64

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

# just "how often does each value range occur") and only needs one numeric column
def generate_histogram(df, column):
    """Generates a histogram for a numeric column and returns it as a base64 string."""
    plt.figure(figsize=(8, 5))
    sns.histplot(df[column].dropna(), kde=True)
    plt.title(f"Distribution of {column}")
    plt.xlabel(column)
    plt.ylabel("Count")
    # we are creeating the empty memory just to store encoded image insted of storing in actual file/disk
    buffer = io.BytesIO()
    # plt.savefig normally store imager into disk but hear we are passing actual empty container
    plt.savefig(buffer, format="png")
    plt.close()
#buffer.seek(0) — after writing to the buffer, its internal "cursor" is sitting at the end of the data. .seek(0) rewinds it back to the beginning, so when we read it next, we get the full image, not nothing.
    buffer.seek(0)
    # read the encoded file and then convert it to base64 out-put is bytes but we need str
    # .decode("utf-8") — the base64 encoding step gives us bytes, but we want an actual Python string (text) to put into JSON. .decode("utf-8") converts those bytes into a normal readable string.
    image_base64 = base64.b64encode(buffer.read()).decode("utf-8")

    return image_base64

# box-plot shows spread, median, and outliers of a numeric column, visually, in one compact shape. 
#.dropna() here specifically because plotting a column with missing values (NaN) can cause errors or misleading gaps   
def generate_boxplot(df, column):
    """Generates a boxplot for a numeric column and returns it as a base64 string."""
    plt.figure(figsize=(8, 5))
    sns.boxplot(x=df[column].dropna())
    plt.title(f"Boxplot of {column}")
    plt.xlabel(column)

    buffer = io.BytesIO()
    plt.savefig(buffer, format="png")
    plt.close()

    buffer.seek(0)
    image_base64 = base64.b64encode(buffer.read()).decode("utf-8")

    return image_base64
# scatter is used ffor comparing two cols , hear we are not using dropna() because scatter will automatically ignore those values which is incomplete means X= NAN and y=INT        
def generate_scatterplot(df, x_column, y_column):
    """Generates a scatter plot between two numeric columns and returns it as a base64 string."""
    plt.figure(figsize=(8, 5))
    sns.scatterplot(x=df[x_column], y=df[y_column])
    plt.title(f"{x_column} vs {y_column}")
    plt.xlabel(x_column)
    plt.ylabel(y_column)

    buffer = io.BytesIO()
    plt.savefig(buffer, format="png")
    plt.close()

    buffer.seek(0)
    image_base64 = base64.b64encode(buffer.read()).decode("utf-8")

    return image_base64

def generate_correlation_heatmap(df):
    """Generates a correlation heatmap for all numeric columns and returns it as a base64 string."""
    numeric_df = df.select_dtypes(include="number")
    correlation_matrix = numeric_df.corr()

    plt.figure(figsize=(10, 8))
    sns.heatmap(correlation_matrix, annot=True, cmap="coolwarm", fmt=".2f")
    plt.title("Correlation Heatmap")

    buffer = io.BytesIO()
    plt.savefig(buffer, format="png")
    plt.close()

    buffer.seek(0)
    image_base64 = base64.b64encode(buffer.read()).decode("utf-8")

    return image_base64
def generate_piechart(df, column):
    """Generates a pie chart showing proportions of a categorical column."""
    value_counts = df[column].value_counts()

    plt.figure(figsize=(8, 8))
    plt.pie(value_counts, labels=value_counts.index, autopct="%1.1f%%")
    plt.title(f"Proportion of {column}")

    buffer = io.BytesIO()
    plt.savefig(buffer, format="png")
    plt.close()

    buffer.seek(0)
    image_base64 = base64.b64encode(buffer.read()).decode("utf-8")
    return image_base64


def generate_barchart(df, column):
    """Generates a bar chart showing counts per category."""
    value_counts = df[column].value_counts()

    plt.figure(figsize=(8, 5))
    sns.barplot(x=value_counts.index, y=value_counts.values)
    plt.title(f"Count of {column}")
    plt.xlabel(column)
    plt.ylabel("Count")

    buffer = io.BytesIO()
    plt.savefig(buffer, format="png")
    plt.close()

    buffer.seek(0)
    image_base64 = base64.b64encode(buffer.read()).decode("utf-8")
    return image_base64


def generate_linechart(df, column):
    """Generates a line chart showing a sorted numeric column's trend."""
    sorted_values = df[column].dropna().sort_values().reset_index(drop=True)

    plt.figure(figsize=(8, 5))
    plt.plot(sorted_values)
    plt.title(f"Sorted Trend of {column}")
    plt.xlabel("Index (sorted)")
    plt.ylabel(column)

    buffer = io.BytesIO()
    plt.savefig(buffer, format="png")
    plt.close()

    buffer.seek(0)
    image_base64 = base64.b64encode(buffer.read()).decode("utf-8")
    return image_base64        