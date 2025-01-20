from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from app.routers import migrate_saphana_to_snowflake


app = FastAPI(title="SAP HANA to Snowflake Migration")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"],
)

app.include_router(migrate_saphana_to_snowflake.router,
                   prefix="/api/migration", tags=["Migration"])


@app.get("/")
def root():
    return {"message": "Welcome to SAP HANA to Snowflake migration tool"}

def main():
    uvicorn.run("app.__main__:app", host="0.0.0.0", reload=False, workers=4)

if __name__ == "__main__":
    main()
