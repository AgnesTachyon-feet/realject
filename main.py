from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from config import Base, engine
from routes.auth_page import router as auth_router


Base.metadata.create_all(bind=engine)

app = FastAPI(title="Family Task Manager - Minimal+Family")

@app.get("/")
def root():
    return RedirectResponse("/login", status_code=307)

app.include_router(auth_router)

