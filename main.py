from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from config import Base, engine
# import ตารางทั้งหมด เพื่อให้สร้างเองตอน start
from tables import users, tasks, submissions, rewards
from tables import notifications, reward_redeems, logs

from routes.pages import auth_page, parent_page, kid_page

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Parent–Kid ToDoList v9 + Notifications + Logs")

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

app.include_router(auth_page.router)
app.include_router(parent_page.router)
app.include_router(kid_page.router)

@app.get("/")
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "role": None})
