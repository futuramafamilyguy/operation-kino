from database import Base
from models import *

from database import engine


Base.metadata.create_all(bind=engine)
