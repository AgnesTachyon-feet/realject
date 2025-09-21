from sqlalchemy import Column, Integer, String, Boolean, DateTime
from config import Base
import datetime

class task(Base):
    __tablename = 'task'
    id = Column(int, primary_key=True)
    title = Column(str)
    description = Column(str)
    create_date = Column(datetime, default = datetime.datetime.now())