from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from app.routers import migrate_saphana_to_snowflake


app = FastAPI(title="SAP HANA to Snowflake Migration")

app.include_router(migrate_saphana_to_snowflake.router,
                   prefix="/api/migration", tags=["Migration"])


@app.get("/")
def root():
    return {"message": "Welcome to SAP HANA to Snowflake migration tool"}
