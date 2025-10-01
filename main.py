from fastapi import FastAPI
from config import engine

import tables.users as user_tables
import tables.task as task_tables
import tables.submission as submission_tables
import routes.task as task_routes
import routes.users as user_routes
import routes.submission as submission_routes


user_tables.Base.metadata.create_all(bind=engine)
task_tables.Base.metadata.create_all(bind=engine)
submission_tables.Base.metadata.create_all(bind=engine)
app = FastAPI()

app.include_router(user_routes.router)
app.include_router(task_routes.router)
app.include_router(submission_routes.router)

@app.get("/")
async def roof():
   return "Hello World"