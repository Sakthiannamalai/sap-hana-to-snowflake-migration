from fastapi import FastAPI
import uvicorn

from app.config.env_loader import PORT
from app.routers import migrate_saphana_to_snowflake


app = FastAPI(title="SAP HANA to Snowflake Migration")

app.include_router(migrate_saphana_to_snowflake.router,
                   prefix="/api/migration", tags=["Migration"])


@app.get("/")
def root():
    return {"message": "Welcome to SAP HANA to Snowflake migration tool"}

def main():
    uvicorn.run("app.__main__:app",port=PORT, host="0.0.0.0", reload=False, workers=4)

if __name__ == "__main__":
    main()
