from fastapi import FastAPI
from app.routers import upload
#This line goes into your app/routers folder, opens upload.py, and makes everything inside it available here
app = FastAPI(title="DataLens API")
# .include_router(...) is a method  that says: "take everything defined in this router, and attach it to the main app."
app.include_router(upload.router)

@app.get("/")
# async def just means "this function is allowed to pause and wait efficiently
async def root() -> dict[str, str]:
    """Health check endpoint to confirm the API is running."""
    return {"message": "DataLens API is running"}