from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from database import create_pool, close_pool
from routes import cliente, contrato, parcela, dashboard, Onboarding


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_pool()
    yield
    await close_pool()


app = FastAPI(
    title="Metropolitan Cobrança API",
    description="Sistema de gestão de contratos consignados e cobrança automática",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(cliente.router,   prefix="/clientes",   tags=["Clientes"])
app.include_router(contrato.router,  prefix="/contratos",  tags=["Contratos"])
app.include_router(parcela.router,   prefix="/parcelas",   tags=["Parcelas"])
app.include_router(dashboard.router,  prefix="/dashboard",  tags=["Dashboard"])
app.include_router(Onboarding.router, prefix="/onboarding", tags=["Onboarding"])

@app.get("/", tags=["Health"])
async def root():
    return {"status": "ok", "app": "Metropolitan Cobrança API v1.0"}