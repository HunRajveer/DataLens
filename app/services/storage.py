import uuid
# it is called universal unique identifiers 
import pandas as pd

# this is we wea are creating a storage space but it will vanish once server shutoff also a limitation , we need to do same stuff
dataset_storage: dict[str, pd.DataFrame] = {}


def save_dataset(df: pd.DataFrame) -> str:
    """Stores a DataFrame in memory and returns a unique dataset ID."""
    # use to generate random long object and then we convert it into str just of easy seraching 
    dataset_id = str(uuid.uuid4())
    dataset_storage[dataset_id] = df
    return dataset_id


def get_dataset(dataset_id: str) -> pd.DataFrame:
    """Retrieves a stored DataFrame by its dataset ID."""
    if dataset_id not in dataset_storage:
        raise ValueError(f"No dataset found with id: {dataset_id}")
    return dataset_storage[dataset_id]