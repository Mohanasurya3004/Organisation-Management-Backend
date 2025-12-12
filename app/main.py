from fastapi import FastAPI
from app.routes.org import router as org_router
from app.routes.admin import router as admin_router

app = FastAPI(title="Organization Management Backend")

app.include_router(org_router)
app.include_router(admin_router)

@app.get("/")
def root():
    return {"status": "Backend running"}
