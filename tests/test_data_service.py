# we will going to test our functions using pytest which lets to run all function at once and check the working 
import pandas as pd
from app.services.data_service import (get_missing_values,
    get_duplicate_count,
    fill_missing_values,)
    


#assert condition

#If condition evaluates to True → nothing happens, code continues normally.
#If condition evaluates to False → Python immediately raises an error (AssertionError) and stops.
# simple it always works with true 
def test_get_missing_values():
    """Missing value counts should match what we manually put into the DataFrame."""
    df = pd.DataFrame({
        "Age": [22, None, 30],
        "Name": ["Alice", "Bob", "Carol"],
    })
    result = get_missing_values(df)
    assert result["Age"] == 1
    assert result["Name"] == 0


def test_get_duplicate_count_no_duplicates():
    """A DataFrame with all unique rows should report zero duplicates."""
    df = pd.DataFrame({"Age": [22, 25, 30]})
    assert get_duplicate_count(df) == 0


def test_get_duplicate_count_with_duplicates():
    """A DataFrame with one repeated row should report exactly one duplicate."""
    df = pd.DataFrame({"Age": [22, 22, 30]})
    assert get_duplicate_count(df) == 1


def test_fill_missing_values_mean():
    """Filling with mean should replace NaN with the column's average of existing values."""
    df = pd.DataFrame({"Age": [20, 30, None]})
    filled_df = fill_missing_values(df, "Age", "mean")
    assert filled_df["Age"].isnull().sum() == 0
    assert filled_df["Age"][2] == 25.0


