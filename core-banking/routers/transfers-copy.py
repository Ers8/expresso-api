from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from models.db_models import Account, Transaction, engine
from websocket.feed import broadcast_alert
from datetime import datetime, timezone
from bri_client import transfer_bri
import uuid

router = APIRouter()


# ================================================================
# MODELS
# ================================================================

class DeviceInfo(BaseModel):
    device_id: str
    ip_address: str
    country: str
    latitude: float = 0.0
    longitude: float = 0.0


class TransferRequest(BaseModel):
    sender_account: str
    receiver_account: str
    amount: int
    currency: str = "IDR"
    purpose_code: str
    description: str
    destination_type: str = "DOMESTIC"
    receiver_bank_code: str = Field(default="002", description="Kode bank tujuan")
    receiver_bank_name: str = Field(default="Bank BRI", description="Nama bank tujuan")
    device_info: DeviceInfo
    session_token: str = ""


# ================================================================
# ENDPOINT TRANSFER
# ================================================================

@router.post("/banking/transfer")
async def transfer(req: TransferRequest):
    tx_id = "TXN-" + datetime.now().strftime("%Y%m%d") + "-" + str(uuid.uuid4())[:6].upper()

    with Session(engine) as db:
        # Validasi akun pengirim
        sender = db.get(Account, req.sender_account)
        if not sender:
            raise HTTPException(status_code=404, detail="Akun pengirim tidak ditemukan")
        if sender.is_blocked:
            raise HTTPException(status_code=403, detail="Akun Anda saat ini ditangguhkan/diblokir")
        if sender.balance < req.amount:
            raise HTTPException(status_code=400, detail="Saldo tabungan tidak mencukupi")

        # Catat transaksi ke DB (status PENDING dulu)
        tx = Transaction(
            transaction_id    = tx_id,
            sender_account    = req.sender_account,
            receiver_account  = req.receiver_account,
            amount            = req.amount,
            purpose_code      = req.purpose_code,
            description       = req.description,
            destination_type  = req.destination_type,
            ip_address        = req.device_info.ip_address,
            country_code      = req.device_info.country,
            latitude          = req.device_info.latitude,
            longitude         = req.device_info.longitude,
            timestamp         = datetime.now(timezone.utc),
            sentinel_score    = None,   # belum ada Sentinel
            sentinel_decision = "PENDING",
            status            = "PENDING"
        )
        db.add(tx)

        # Eksekusi transfer ke BRI Gateway
        try:
            if req.destination_type == "INTERBANK":
                raise HTTPException(
                    status_code=400,
                    detail="Transfer INTERBANK belum tersedia. Gunakan DOMESTIC."
                )

            bri_response = await transfer_bri(
                sender   = req.sender_account,
                receiver = req.receiver_account,
                amount   = req.amount,
                ref_id   = tx_id
            )
        except HTTPException:
            raise
        except Exception as e:
            tx.status = "FAILED"
            db.commit()
            raise HTTPException(status_code=502, detail=f"Gagal memproses ke BRI Gateway: {str(e)}")

        # Update saldo di DB lokal
        sender.balance -= req.amount
        receiver = db.get(Account, req.receiver_account)
        if receiver:
            receiver.balance += req.amount

        tx.status = "SUCCESS"
        db.commit()

        # Broadcast WebSocket ke dashboard
        await broadcast_alert({
            "type":           "SUCCESS",
            "transaction_id": tx_id,
            "amount":         req.amount,
            "risk_score":     None,
            "destination":    req.destination_type,
            "timestamp":      datetime.now().isoformat()
        })

        return {
            "status":               "SUCCESS",
            "transaction_id":       tx_id,
            "destination_type":     req.destination_type,
            "sender_balance_after": sender.balance,
            "bri_api_response":     bri_response,
            "message":              "Transaksi berhasil diproses."
        }