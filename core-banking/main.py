from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import traceback, sys

# ── IMPORT ROUTERS ────────────────────────────────────────
from routers import transfers
from debug_routes import router as debug_router

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

# ── ROUTERS ───────────────────────────────────────────────
app.include_router(transfers.router, prefix="/api/v1")
app.include_router(debug_router,     prefix="/api/v1")   # ← debug sementara

# app.include_router(accounts.router,    prefix="/api/v1")  # aktifkan kalau sudah stabil
# app.include_router(attack_sim.router,  prefix="/api/v1")

# ── HEALTH CHECK ─────────────────────────────────────────
@app.get("/health")
def health():
    return {
        "status":  "OK",
        "service": "core-banking",
        "version": "1.0.0",
        "python":  sys.version,
    }

# ── GLOBAL EXCEPTION HANDLER ─────────────────────────────
# Tangkap semua unhandled error dan tampilkan di response
# (jangan lupa hapus di production!)
from fastapi import Request
from fastapi.responses import JSONResponse

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "error":     str(exc),
            "type":      type(exc).__name__,
            "traceback": traceback.format_exc().splitlines(),
            "path":      str(request.url),
        }
    )