from fastapi import FastAPI
from app.database.connection import engine
from app.database.base import Base

# importar models para criar tabelas
from app.models import Cliente

app = FastAPI(title="Sistema de Cobrança Metropolitan")

Base.metadata.create_all(bind=engine)

@app.get("/")
def health_check():
    return {"status": "API rodando"}