
from fastapi import FastAPI
import models
from database import engine
from router import auth,Todoss,admin
app = FastAPI()



models.Base.metadata.create_all(bind=engine)

app.include_router(auth.router)
app.include_router(Todoss.router)
app.include_router(admin.router)
