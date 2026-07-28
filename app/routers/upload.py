from fastapi import APIRouter, UploadFile, File
#UploadFile it will allow us to handle difffert kind of files 
# File is a helper tool which tell to FastAPI "this piece of incoming data is a file, not normal text
# APIRouter will allow us to create a mini version of fastAPI where we can use every properties of FastAPI 
# APIRouters allow us to manage multiple routes efficiently

from app.models.upload_models import UploadResponse
from app.services.data_service import read_csv_file , get_missing_values,get_basic_statistics,get_data_types
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