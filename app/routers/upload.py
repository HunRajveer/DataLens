from fastapi import APIRouter, UploadFile, File,HTTPException
# HTTPEXCEPTION is FastAPI's way of manually returning a proper error response (status code + message) instead of letting something crash 
#UploadFile it will allow us to handle difffert kind of files 
# File is a helper tool which tell to FastAPI "this piece of incoming data is a file, not normal text
# APIRouter will allow us to create a mini version of fastAPI where we can use every properties of FastAPI 
# APIRouters allow us to manage multiple routes efficiently
import io
from app.models.upload_models import UploadResponse
from app.services.data_service import read_csv_file , get_missing_values,get_basic_statistics,get_data_types,drop_missing_values,fill_missing_values,get_duplicate_count,remove_duplicates,select_columns,generate_histogram,generate_boxplot,generate_scatterplot,generate_correlation_heatmap,generate_linechart,generate_piechart,generate_barchart,groupby_aggregate,get_correlation_matrix,get_value_counts,get_top_n_records,dataframe_to_csv_bytes,dataframe_to_excel_bytes
from fastapi.responses import StreamingResponse
#FastAPI class specifically for streaming file-like content back as a response, instead of auto-converting a dict to JSON.
#UploadResponse pydentic class form upload_models 
from  app.services.storage import save_dataset,get_dataset
from app.core.config import logger


router = APIRouter(prefix="/upload", tags=["Upload"])

#Before sending a response back to the user, check that it actually matches the UploadResponse shape.
@router.post("/", response_model=UploadResponse)
async def upload_csv(file: UploadFile = File(None), dataset_id: str = None) -> UploadResponse:
    """Receives a CSV, reads it into a DataFrame, stores it, and returns basic info plus a dataset ID."""
    df = await read_csv_file(file)
    dataset_id = save_dataset(df)
    # this will showcase datatime 
    logger.info(f"Dataset uploaded: {file.filename} ({df.shape[0]} rows, {df.shape[1]} columns) -> id={dataset_id}")

    return UploadResponse(
        filename=file.filename,
        rows=df.shape[0],
        columns=df.shape[1],
        column_names=df.columns.tolist(),
        dataset_id=dataset_id,
    )
@router.post("/missing-values")
async def missing_values(
    file: UploadFile = File(None), # means optional to give new file again and again 
    dataset_id: str = None,
) -> dict[str, int]:
    """Returns how many missing values exist in each column. Accepts either a file upload or a dataset_id."""
    # if file id is given then fatch it from storage.py 
    if dataset_id:
        df = get_dataset(dataset_id)
    # if id is not given then just read a file     
    elif file:
        df = await read_csv_file(file)
    else:
        raise HTTPException(status_code=400, detail="Provide either a file or a dataset_id")

    result = get_missing_values(df)
    return result

@router.post("/data-types")
async def data_types(file: UploadFile = File(None), dataset_id: str = None) -> dict[str, str]:
    """Returns the data type of each column in the uploaded CSV."""
    df = await read_csv_file(file)
    return get_data_types(df)


@router.post("/statistics")
async def statistics(file: UploadFile = File(None), dataset_id: str = None) -> dict:
    """Returns basic statistics for numeric columns in the uploaded CSV."""
    df = await read_csv_file(file)
    return get_basic_statistics(df)   

# column: str | None = None means "this can either be text, or nothing at all." = None sets the default, so if the user doesn't specify a column, this stays None
@router.post("/drop-missing")
async def drop_missing(file: UploadFile = File(None), dataset_id: str = None, column: str | None = None) -> dict:
    """Drops rows with missing values, optionally limited to one column."""
    df = await read_csv_file(file)
    cleaned_df = drop_missing_values(df, column)
    return {
        "original_rows": df.shape[0],
        "remaining_rows": cleaned_df.shape[0],
        "rows_dropped": df.shape[0] - cleaned_df.shape[0],
    }
@router.post("/fill-missing")
async def fill_missing(file: UploadFile = File(None), dataset_id: str = None, column: str = "Age", strategy: str = "mean") -> dict:
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
async def duplicates(file: UploadFile = File(None), dataset_id: str = None, columns: str | None = None) -> dict:
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
async def select_columns_endpoint(file: UploadFile = File(None), dataset_id: str = None, columns: str = "") -> dict:
    """Returns a preview of the dataset limited to the specified comma-separated columns."""
    df = await read_csv_file(file)
    column_list = columns.split(",")

    selected_df = select_columns(df, column_list)

    return {
        "selected_columns": column_list,
        "preview": selected_df.head(7).to_dict(orient="records"),
    }    
@router.post("/histogram")
async def histogram(file: UploadFile = File(None), dataset_id: str = None, column: str = "Age") -> dict:
    """Generates a histogram for the specified numeric column."""
    df = await read_csv_file(file)
    image_base64 = generate_histogram(df, column)

    return {"column": column, "chart_base64": image_base64}    


@router.post("/boxplot")
async def boxplot(file: UploadFile = File(None), dataset_id: str = None, column: str = "Fare") -> dict:
    """Generates a boxplot for the specified numeric column."""
    df = await read_csv_file(file)
    image_base64 = generate_boxplot(df, column)

    return {"column": column, "chart_base64": image_base64}
@router.post("/scatterplot")
async def scatterplot(file: UploadFile = File(None), dataset_id: str = None, x_column: str = "Age", y_column: str = "Fare") -> dict:
    """Generates a scatter plot between two numeric columns."""
    df = await read_csv_file(file)
    image_base64 = generate_scatterplot(df, x_column, y_column)

    return {"x_column": x_column, "y_column": y_column, "chart_base64": image_base64}  

@router.post("/correlation-heatmap")
async def correlation_heatmap(file: UploadFile = File(None), dataset_id: str = None) -> dict:
    """Generates a correlation heatmap for all numeric columns in the dataset."""
    df = await read_csv_file(file)
    image_base64 = generate_correlation_heatmap(df)

    return {"chart_base64": image_base64}


@router.post("/piechart")
async def piechart(file: UploadFile = File(None), dataset_id: str = None, column: str = "Embarked") -> dict:
    """Generates a pie chart for a categorical column."""
    df = await read_csv_file(file)
    image_base64 = generate_piechart(df, column)
    return {"column": column, "chart_base64": image_base64}


@router.post("/barchart")
async def barchart(file: UploadFile = File(None), dataset_id: str = None, column: str = "Pclass") -> dict:
    """Generates a bar chart for a categorical column."""
    df = await read_csv_file(file)
    image_base64 = generate_barchart(df, column)
    return {"column": column, "chart_base64": image_base64}


@router.post("/linechart")
async def linechart(file: UploadFile = File(None), dataset_id: str = None, column: str = "Fare") -> dict:
    """Generates a line chart for a sorted numeric column."""
    df = await read_csv_file(file)
    image_base64 = generate_linechart(df, column)
    return {"column": column, "chart_base64": image_base64}
@router.post("/groupby")
async def groupby(
    file: UploadFile = File(None), dataset_id: str = None,
    group_by_column: str = "Pclass",
    agg_column: str = "Fare",
    agg_function: str = "mean",
) -> dict:
    """Groups by one column and aggregates another using mean, sum, count, median, min, or max."""
    df = await read_csv_file(file)
    result = groupby_aggregate(df, group_by_column, agg_column, agg_function)

    return {
        "group_by_column": group_by_column,
        "agg_column": agg_column,
        "agg_function": agg_function,
        "result": result,
    }    
@router.post("/correlation-matrix")
async def correlation_matrix(file: UploadFile = File(None), dataset_id: str = None) -> dict:
    """Returns the correlation matrix for all numeric columns as raw numbers."""
    df = await read_csv_file(file)
    result = get_correlation_matrix(df)
    return {"correlation_matrix": result} 
@router.post("/value-counts")
async def value_counts(file: UploadFile = File(None), dataset_id: str = None, column: str = "Embarked") -> dict:
    """Returns the count of each unique value in a column."""
    df = await read_csv_file(file)
    result = get_value_counts(df, column)
    return {"column": column, "value_counts": result} 
@router.post("/top-records")
async def top_records(
    file: UploadFile = File(None), dataset_id: str = None,
    column: str = "Fare",
    n: int = 5,
    ascending: bool = False,
) -> dict:
    """Returns the top N records sorted by a column (descending by default)."""
    df = await read_csv_file(file)
    result = get_top_n_records(df, column, n, ascending)

    return {"column": column, "n": n, "ascending": ascending, "records": result}


@router.post("/export-csv")
async def export_csv(file: UploadFile = File(None), dataset_id: str = None):
    """Exports the (optionally cleaned) dataset as a downloadable CSV file."""
    df = await read_csv_file(file)
    csv_bytes = dataframe_to_csv_bytes(df)
    logger.info(f"CSV export requested for dataset_id={dataset_id}")
# unlike using normal return which aim was to convert DICT or text into json naturally , we need somthing different(file) so for that we inform API that treat it as FILE not JSON , so we are using  StreamingResponse
    return StreamingResponse(
        # we are just rapping bytes into file formate so API could read line by line 
        io.BytesIO(csv_bytes),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=cleaned_data.csv"},
    )  
@router.post("/export-excel")
async def export_excel(file: UploadFile = File(None), dataset_id: str = None):
    """Exports the dataset as a downloadable Excel file."""
    df = await read_csv_file(file)
    excel_bytes = dataframe_to_excel_bytes(df)

    return StreamingResponse(
        io.BytesIO(excel_bytes),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=cleaned_data.xlsx"},
    )


     

