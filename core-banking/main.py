from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# 1. IMPORT TRANSFERS SAJA
from routers import transfers 

app = FastAPI(
    title="Crypto-Sentinel Core Banking API",
    version="1.0.0",
    description="Mock Core Banking — Tim EXPRESSO, Universitas Kuningan"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

# 2. NYALAKAN ROUTER TRANSFERS
app.include_router(transfers.router, prefix="/api/v1")

# 3. PASTIKAN ACCOUNTS & ATTACK_SIM MATI
# app.include_router(accounts.router, prefix="/api/v1/banking")
# app.include_router(attack_sim.router, prefix="/api/v1")

@app.get("/health")
def health():
    return {"status": "OK", "service": "core-banking", "version": "1.0.0"}