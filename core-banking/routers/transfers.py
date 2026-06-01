from fastapi import APIRouter, HTTPException, Form, Request
from sqlalchemy.orm import Session
from models.db_models import Account, Transaction, engine
from datetime import datetime, timezone
from bri_client import transfer_bri, transfer_interbank_bri
import uuid

router = APIRouter()

# ================================================================
# 1. ENDPOINT TRANSFER (POST - PRODUCTION)
# ================================================================

@router.post("/bri/transfer")
async def bri_transfer(
    request: Request,
    sender_account: str = Form(..., description="Rekening Pengirim (misal: 0123456789)"),
    receiver_account: str = Form(..., description="Rekening Penerima (misal: 9876543210)"),
    amount: int = Form(..., description="Nominal Transfer"),
    latitude: float = Form(-6.2, description="Latitude (Nanti diisi otomatis oleh Frontend)"),
    longitude: float = Form(106.8, description="Longitude (Nanti diisi otomatis oleh Frontend)")
):
    """Transfer via Form Input. IP Address ditangkap otomatis oleh sistem backend."""

    if amount < 50000:
        raise HTTPException(
            status_code=400,
            detail="Nominal transfer minimal adalah Rp50.000"
        )

    ip_address = request.headers.get("X-Forwarded-For", request.client.host)
    if ip_address and "," in ip_address:
        ip_address = ip_address.split(",")[0].strip()
    if not ip_address:
        ip_address = "127.0.0.1"

    tx_id            = "TXN-" + datetime.now(timezone.utc).strftime("%Y%m%d") + "-" + str(uuid.uuid4())[:6].upper()
    purpose_code     = "SALA"
    description      = "Transfer via API Gateway"
    destination_type = "DOMESTIC"
    country_code     = "ID"

    with Session(engine) as db:
        sender   = db.get(Account, sender_account)
        receiver = db.get(Account, receiver_account)

        if not sender:
            raise HTTPException(status_code=404, detail="Akun pengirim tidak ditemukan")
        if not receiver:
            raise HTTPException(status_code=404, detail="Akun penerima tidak ditemukan")
        if sender.is_blocked:
            raise HTTPException(status_code=403, detail=f"Akun {sender.owner_name} diblokir")
        if sender.balance < amount:
            raise HTTPException(
                status_code=400,
                detail=f"Saldo tidak mencukupi. Saldo: Rp{sender.balance:,} | Dibutuhkan: Rp{amount:,}"
            )

        balance_before = sender.balance

        tx = Transaction(
            transaction_id    = tx_id,
            sender_account    = sender_account,
            receiver_account  = receiver_account,
            amount            = amount,
            purpose_code      = purpose_code,
            description       = description,
            destination_type  = destination_type,
            ip_address        = ip_address,
            country_code      = country_code,
            latitude          = latitude,
            longitude         = longitude,
            timestamp         = datetime.now(timezone.utc),
            sentinel_score    = None,
            sentinel_decision = "PENDING",
            status            = "PENDING"
        )
        db.add(tx)
        db.commit()

        try:
            bri_response = await transfer_bri(
                sender   = sender_account,
                receiver = receiver_account,
                amount   = amount,
                ref_id   = tx_id
            )

            response_code = bri_response.get("responseCode", "")
            if not response_code.startswith("2"):
                raise Exception(
                    f"BRI menolak — Code: {response_code}, "
                    f"Message: {bri_response.get('responseMessage')}"
                )

            sender.balance   -= amount
            receiver.balance += amount
            tx.status         = "SUCCESS"
            db.commit()

            return {
                "status":             "SUCCESS",
                "transaction_id":     tx_id,
                "ip_address_detected": ip_address,
                "transfer_info": {
                    "sender":         sender.owner_name,
                    "receiver":       receiver.owner_name,
                    "amount":         f"Rp{amount:,}",
                    "balance_before": f"Rp{balance_before:,}",
                    "balance_after":  f"Rp{sender.balance:,}",
                },
                "bri_response": bri_response
            }

        except Exception as e:
            tx.status = "FAILED"
            db.commit()
            raise HTTPException(status_code=502, detail=str(e))


# ================================================================
# 2. ENDPOINT TRANSFER (GET - KHUSUS TESTING URL)
# ================================================================

@router.get("/bri/transfer-via-url")
async def bri_transfer_via_url(
    request: Request,
    sender: str = "0123456789",
    receiver: str = "9876543210",
    amount: int = 100000
):
    """Transfer instan via URL Browser (HANYA UNTUK TESTING).
       Contoh: /api/v1/bri/transfer-via-url?sender=0123456789&receiver=9876543210&amount=100000
    """

    if amount < 50000:
        raise HTTPException(
            status_code=400,
            detail="Nominal transfer minimal adalah Rp50.000"
        )

    ip_address = request.headers.get("X-Forwarded-For", request.client.host)
    if ip_address and "," in ip_address:
        ip_address = ip_address.split(",")[0].strip()
    if not ip_address:
        ip_address = "127.0.0.1"

    tx_id            = "TXN-" + datetime.now(timezone.utc).strftime("%Y%m%d") + "-" + str(uuid.uuid4())[:6].upper()
    purpose_code     = "SALA"
    description      = "Test Transfer via URL Browser"
    destination_type = "DOMESTIC"
    country_code     = "ID"
    latitude         = -6.2
    longitude        = 106.8

    with Session(engine) as db:
        sender_acc   = db.get(Account, sender)
        receiver_acc = db.get(Account, receiver)

        if not sender_acc:
            raise HTTPException(status_code=404, detail="Akun pengirim tidak ditemukan")
        if not receiver_acc:
            raise HTTPException(status_code=404, detail="Akun penerima tidak ditemukan")
        if sender_acc.is_blocked:
            raise HTTPException(status_code=403, detail=f"Akun {sender_acc.owner_name} diblokir")
        if sender_acc.balance < amount:
            raise HTTPException(
                status_code=400,
                detail=f"Saldo tidak mencukupi. Saldo: Rp{sender_acc.balance:,} | Dibutuhkan: Rp{amount:,}"
            )

        balance_before = sender_acc.balance

        tx = Transaction(
            transaction_id    = tx_id,
            sender_account    = sender,
            receiver_account  = receiver,
            amount            = amount,
            purpose_code      = purpose_code,
            description       = description,
            destination_type  = destination_type,
            ip_address        = ip_address,
            country_code      = country_code,
            latitude          = latitude,
            longitude         = longitude,
            timestamp         = datetime.now(timezone.utc),
            sentinel_score    = None,
            sentinel_decision = "PENDING",
            status            = "PENDING"
        )
        db.add(tx)
        db.commit()

        try:
            bri_response = await transfer_bri(
                sender   = sender,
                receiver = receiver,
                amount   = amount,
                ref_id   = tx_id
            )

            response_code = bri_response.get("responseCode", "")
            if not response_code.startswith("2"):
                raise Exception(
                    f"BRI menolak — Code: {response_code}, "
                    f"Message: {bri_response.get('responseMessage')}"
                )

            sender_acc.balance   -= amount
            receiver_acc.balance += amount
            tx.status             = "SUCCESS"
            db.commit()

            return {
                "status":              "SUCCESS",
                "transaction_id":      tx_id,
                "ip_address_detected": ip_address,
                "transfer_info": {
                    "sender":         sender_acc.owner_name,
                    "receiver":       receiver_acc.owner_name,
                    "amount":         f"Rp{amount:,}",
                    "balance_before": f"Rp{balance_before:,}",
                    "balance_after":  f"Rp{sender_acc.balance:,}",
                },
                "bri_response":   bri_response,
                "transaction_log": {
                    "transaction_id":  tx_id,
                    "purpose_code":    purpose_code,
                    "description":     description,
                    "destination_type": destination_type,
                    "ip_address":      ip_address,
                    "country_code":    country_code,
                    "latitude":        latitude,
                    "longitude":       longitude,
                    "timestamp":       datetime.now(timezone.utc).isoformat(),
                    "status":          "SUCCESS"
                }
            }

        except Exception as e:
            tx.status = "FAILED"
            db.commit()
            raise HTTPException(status_code=502, detail=str(e))
        
# ================================================================
# 3. ENDPOINT TRANSFER INTERBANK (BEDA BANK)
# ================================================================
@router.post("/bri/transfer-interbank")
async def bri_transfer_interbank(
    request: Request,
    sender_account: str = Form(..., description="Rekening Pengirim (Internal). Contoh: 0123456789"),
    receiver_account: str = Form(..., description="Rekening Tujuan (Bank Lain)"),
    bank_code: str = Form(..., description="Kode Bank Tujuan (contoh: 014 untuk BCA, 008 untuk Mandiri)"),
    amount: int = Form(..., description="Nominal Transfer"),
    latitude: float = Form(-6.2, description="Latitude"),
    longitude: float = Form(106.8, description="Longitude")
):
    """
    ### Panduan Testing Sandbox
    Untuk menghindari error **"Akun tidak ditemukan"**, pastikan `sender_account` dan `receiver_account` sudah terdaftar di Database lokal:
    
    * **`0123456789`**
    * **`1122334455`**
    * **`5544332211`**
    * **`9876543210`**
    """

    if amount < 50000:
        raise HTTPException(status_code=400, detail="Nominal transfer minimal Rp50.000")

    ip_address = request.headers.get("X-Forwarded-For", request.client.host)
    if ip_address and "," in ip_address:
        ip_address = ip_address.split(",")[0].strip()
    if not ip_address:
        ip_address = "127.0.0.1"

    tx_id = "TXN-" + datetime.now(timezone.utc).strftime("%Y%m%d") + "-" + str(uuid.uuid4())[:6].upper()
    
    with Session(engine) as db:
        # 1. CEK KEDUA AKUN DI DATABASE LOKAL
        sender = db.get(Account, sender_account)
        receiver = db.get(Account, receiver_account)
        
        if not sender:
            raise HTTPException(status_code=404, detail="Akun pengirim tidak ditemukan di database.")
            
        if not receiver:
            raise HTTPException(
                status_code=404, 
                detail=f"Akun tujuan {receiver_account} tidak terdaftar di sistem database. Silakan daftarkan dulu untuk testing."
            )
            
        if sender.is_blocked:
            raise HTTPException(status_code=403, detail=f"Akun {sender.owner_name} diblokir")
            
        if sender.balance < amount:
            raise HTTPException(
                status_code=400, 
                detail=f"Saldo tidak mencukupi. Saldo: Rp{sender.balance:,}"
            )

        balance_before = sender.balance

        # REKAM TRANSAKSI KE DATABASE
        tx = Transaction(
            transaction_id    = tx_id,
            sender_account    = sender_account,
            receiver_account  = receiver_account,
            amount            = amount,
            purpose_code      = "SALA",
            description       = f"Transfer Interbank ke Bank {bank_code}",
            destination_type  = "EXTERNAL_BANK",
            ip_address        = ip_address,
            country_code      = "ID",
            latitude          = latitude,
            longitude         = longitude,
            timestamp         = datetime.now(timezone.utc),
            sentinel_score    = None,
            sentinel_decision = "PENDING",
            status            = "PENDING"
        )
        db.add(tx)
        db.commit()

        try:
            bri_response = await transfer_interbank_bri(
                sender        = sender_account,
                receiver      = receiver_account,
                receiver_name = receiver.owner_name, 
                bank_code     = bank_code,
                amount        = amount,
                ref_id        = tx_id
            )

            # Memastikan respons sukses dari API bank
            response_code = bri_response.get("responseCode", "")
            if not response_code.startswith("2"):
                raise Exception(
                    f"BRI menolak — Code: {response_code}, "
                    f"Message: {bri_response.get('responseMessage')}"
                )

            # POTONG SALDO PENGIRIM
            sender.balance -= amount
            
            tx.status = "SUCCESS"
            db.commit()

            return {
                "status": "SUCCESS",
                "transaction_id": tx_id,
                "transfer_info": {
                    "sender": sender.owner_name,
                    "receiver_bank": bri_response.get("beneficiaryBankName", bank_code),
                    "receiver_account": receiver_account,
                    "receiver_name": receiver.owner_name, 
                    "amount": f"Rp{amount:,}",
                    "balance_after": f"Rp{sender.balance:,}",
                },
                "bri_response": bri_response
            }

        except Exception as e:
            tx.status = "FAILED"
            db.commit()
            raise HTTPException(status_code=502, detail=str(e))
