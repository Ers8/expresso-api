"""
debug_routes.py — Tambahkan sementara ke main.py untuk diagnose error di Vercel.
Hapus setelah masalah ketemu.
"""
from fastapi import APIRouter
import os, sys, traceback

router = APIRouter()

@router.get("/debug/env")
def debug_env():
    """Cek apakah semua env vars sudah terbaca di Vercel"""
    return {
        "BRI_CLIENT_ID":     "SET" if os.getenv("BRI_CLIENT_ID") else "MISSING ❌",
        "BRI_CLIENT_SECRET": "SET" if os.getenv("BRI_CLIENT_SECRET") else "MISSING ❌",
        "BRI_PRIVATE_KEY":   "SET" if os.getenv("BRI_PRIVATE_KEY") else "MISSING ❌",
        "BRI_BASE_URL":      os.getenv("BRI_BASE_URL", "MISSING ❌"),
        "DATABASE_URL":      "SET" if os.getenv("DATABASE_URL") else "MISSING ❌",
        "SENTINEL_AI_URL":   os.getenv("SENTINEL_AI_URL", "MISSING ❌"),
        "python_version":    sys.version,
    }


@router.get("/debug/private-key")
def debug_private_key():
    """Cek apakah private key bisa di-parse"""
    try:
        from bri_client import load_private_key
        load_private_key()
        return {"status": "OK ✅", "message": "Private key berhasil di-load"}
    except Exception as e:
        return {
            "status":    "FAILED ❌",
            "error":     str(e),
            "traceback": traceback.format_exc()
        }


@router.get("/debug/token")
async def debug_token():
    """Cek apakah bisa dapat token dari BRI"""
    try:
        from bri_client import get_bri_token_snap
        token = await get_bri_token_snap()
        return {"status": "OK ✅", "token_preview": token[:20] + "..."}
    except Exception as e:
        return {
            "status":    "FAILED ❌",
            "error":     str(e),
            "traceback": traceback.format_exc()
        }


@router.get("/debug/db")
def debug_db():
    """Cek apakah koneksi database berhasil"""
    try:
        from models.db_models import engine
        with engine.connect() as conn:
            conn.execute(__import__("sqlalchemy").text("SELECT 1"))
        return {"status": "OK ✅", "message": "Database terhubung"}
    except Exception as e:
        return {
            "status":    "FAILED ❌",
            "error":     str(e),
            "traceback": traceback.format_exc()
        }


@router.get("/debug/imports")
def debug_imports():
    """Cek apakah semua module bisa di-import"""
    results = {}
    modules = [
        "httpx",
        "cryptography",
        "sqlalchemy",
        "dotenv",
        "bri_client",
        "models.db_models",
    ]
    for mod in modules:
        try:
            __import__(mod)
            results[mod] = "OK ✅"
        except Exception as e:
            results[mod] = f"FAILED ❌ — {str(e)}"
    return results