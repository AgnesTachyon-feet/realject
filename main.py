# main.py
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from config import Base, engine

from routes.auth_page import router as auth_router
from routes.parent_page import router as parent_router
from routes.kid_page import router as kid_router

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(auth_router)
app.include_router(parent_router)
app.include_router(kid_router)

Base.metadata.create_all(bind=engine)

@app.get("/", include_in_schema=False)
def root():
    from fastapi.responses import RedirectResponse
    return RedirectResponse("/login", status_code=307)
