from pydantic import BaseModel


class UploadResponse(BaseModel):
    """Defines the exact shape of data returned after a successful CSV upload."""
    filename: str
    rows: int
    columns: int
    column_names: list[str]
    dataset_id: str