# main.py
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from config import Base, engine
from fastapi.responses import RedirectResponse
from routes.auth_page import router as auth_router
from routes.parent_page import router as parent_router
from routes.kid_page import router as kid_router
from routes.parent_tasks import router as parent_tasks_router
from routes.kid_tasks import router as kid_tasks_router
from routes.parent_history import router as parent_history_router
from routes.kid_history import router as kid_history_router

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(auth_router)
app.include_router(parent_router)
app.include_router(kid_router)
app.include_router(parent_tasks_router)
app.include_router(kid_tasks_router)
app.include_router(parent_history_router)
app.include_router(kid_history_router)

Base.metadata.create_all(bind=engine)

@app.get("/", include_in_schema=False)
def root():

    return RedirectResponse("/login", status_code=307)
