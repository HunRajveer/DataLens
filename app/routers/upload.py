from fastapi import APIRouter, UploadFile, File
#UploadFile it will allow us to handle difffert kind of files 
# File is a helper tool which tell to FastAPI "this piece of incoming data is a file, not normal text
# APIRouter will allow us to create a mini version of fastAPI where we can use every properties of FastAPI 
# APIRouters allow us to manage multiple routes efficiently

from app.models.upload_models import UploadResponse
from app.services.data_service import read_csv_file , get_missing_values,get_basic_statistics,get_data_types,drop_missing_values,fill_missing_values,get_duplicate_count,remove_duplicates,select_columns
#UploadResponse pydentic class form upload_models 
router = APIRouter(prefix="/upload", tags=["Upload"])

#Before sending a response back to the user, check that it actually matches the UploadResponse shape.
@router.post("/",response_model=UploadResponse)
async def upload_csv(file: UploadFile = File(...)) -> UploadResponse:
    """Receives a CSV, reads it into a DataFrame, and returns basic info."""
    df = await read_csv_file(file)
    # hear we don't use dict{} because we are creating an object using our  pydentic class so ()
    return UploadResponse(
        filename=file.filename,
        rows=df.shape[0],
        columns=df.shape[1],
        column_names=df.columns.tolist(),
    )
@router.post("/missing-values")
async def missing_values(file: UploadFile = File(...)) -> dict[str, int]:
    """Returns how many missing values exist in each column of the uploaded CSV."""
    df = await read_csv_file(file)
    result = get_missing_values(df)
    return result

@router.post("/data-types")
async def data_types(file: UploadFile = File(...)) -> dict[str, str]:
    """Returns the data type of each column in the uploaded CSV."""
    df = await read_csv_file(file)
    return get_data_types(df)


@router.post("/statistics")
async def statistics(file: UploadFile = File(...)) -> dict:
    """Returns basic statistics for numeric columns in the uploaded CSV."""
    df = await read_csv_file(file)
    return get_basic_statistics(df)   

# column: str | None = None means "this can either be text, or nothing at all." = None sets the default, so if the user doesn't specify a column, this stays None
@router.post("/drop-missing")
async def drop_missing(file: UploadFile = File(...), column: str | None = None) -> dict:
    """Drops rows with missing values, optionally limited to one column."""
    df = await read_csv_file(file)
    cleaned_df = drop_missing_values(df, column)
    return {
        "original_rows": df.shape[0],
        "remaining_rows": cleaned_df.shape[0],
        "rows_dropped": df.shape[0] - cleaned_df.shape[0],
    }
@router.post("/fill-missing")
async def fill_missing(file: UploadFile = File(...), column: str = "Age", strategy: str = "mean") -> dict:
    """Fills missing values in a column using mean, median, or mode."""
    df = await read_csv_file(file)
    # check missing cols 
    missing_before = df[column].isnull().sum()
    # fill them 
    filled_df = fill_missing_values(df, column, strategy)
    # recheck if is there any value missing after filling
    missing_after = filled_df[column].isnull().sum()

    return {
        "column": column,
        "strategy": strategy,
        "missing_before": int(missing_before),
        "missing_after": int(missing_after),
    }    
#columns: str | None = None — a query parameter, but notice it's a single string, not natively a list. Swagger query strings don't easily support lists, so we accept comma-separated text instead (e.g., Name,Age,Fare) and split it ourselves.
@router.post("/duplicates")
async def duplicates(file: UploadFile = File(...), columns: str | None = None) -> dict:
    """Reports how many duplicate rows exist and how many remain after removing them.
    Optionally pass a comma-separated list of columns to check, e.g. Name,Age,Fare."""
    df = await read_csv_file(file)

    subset = columns.split(",") if columns else None

    duplicate_count = get_duplicate_count(df, subset)
    cleaned_df = remove_duplicates(df, subset)

    return {
        "original_rows": df.shape[0],
        "duplicate_rows_found": duplicate_count,
        "remaining_rows": cleaned_df.shape[0],
        "checked_columns": subset if subset else "all columns",
    }
#The problem: JSON (what your API sends back) doesn't understand "spreadsheets." JSON only understands things like lists [ ] and dictionaries { }. So we need to convert this table into one of those shapes — and .to_dict() is the tool for that conversion. But here's the catch: there's more than one way to convert a table into a dictionary, depending on what structure you want. That's exactly what orient controls — it's telling pandas how to reshape the table.    
@router.post("/select-columns")
async def select_columns_endpoint(file: UploadFile = File(...), columns: str = "") -> dict:
    """Returns a preview of the dataset limited to the specified comma-separated columns."""
    df = await read_csv_file(file)
    column_list = columns.split(",")

    selected_df = select_columns(df, column_list)

    return {
        "selected_columns": column_list,
        "preview": selected_df.head(7).to_dict(orient="records"),
    }    