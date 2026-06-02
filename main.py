from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import transfers 

app = FastAPI(
    title="Crypto-Sentinel API",
    version="1.0.0",
    description="API — Tim EXPRESSO, Universitas Kuningan"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

app.include_router(transfers.router, prefix="/api/v1")

# app.include_router(accounts.router, prefix="/api/v1/banking")
# app.include_router(attack_sim.router, prefix="/api/v1")

@app.get("/health")
def health():
    return {"status": "OK", "service": "core-banking", "version": "1.0.0"}