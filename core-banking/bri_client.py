import httpx
import base64
import os
import hashlib
import hmac
import json
from dotenv import load_dotenv
from datetime import datetime, timezone, timedelta
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

load_dotenv()

BRI_BASE_URL  = os.getenv("BRI_BASE_URL")
BRI_CLIENT_ID = os.getenv("BRI_CLIENT_ID")
BRI_SECRET    = os.getenv("BRI_CLIENT_SECRET")

# ─── MAPPING AKUN LOKAL → BRI SANDBOX ────────────────────
BRI_SANDBOX_ACCOUNTS = {
    "0123456789": "888801000003301",
    "1122334455": "888801000157610",
    "5544332211": "888801000003301",
    "9988776655": "888801000003301",
    "9876543210": "888801000157508",
    "1111222233": "888801000157508",
}

def get_bri_account(local_account: str) -> str:
    return BRI_SANDBOX_ACCOUNTS.get(local_account, "888801000157508")


# ─── TIMESTAMP ───────────────────────────────────────────

WIB = timezone(timedelta(hours=7))

def get_timestamp() -> str:
    now = datetime.now(WIB)
    return now.strftime("%Y-%m-%dT%H:%M:%S.000+07:00")

def get_timestamp_plain() -> str:
    now = datetime.now(WIB)
    return now.strftime("%Y-%m-%dT%H:%M:%S+07:00")


# ─── PRIVATE KEY (DIUBAH UNTUK VERCEL) ───────────────────

def load_private_key():
    # Mengambil isi teks kunci langsung dari Environment Variables
    private_key_pem = os.getenv("BRI_PRIVATE_KEY")
    
    if not private_key_pem:
        raise ValueError("Variabel BRI_PRIVATE_KEY belum diset di Vercel atau .env")
    
    # Mengembalikan format baris baru jika Vercel membacanya sebagai literal '\n'
    private_key_pem = private_key_pem.replace('\\n', '\n')
    
    # Memuat kunci menggunakan cryptography
    return serialization.load_pem_private_key(
        private_key_pem.encode("utf-8"), 
        password=None
    )


# ─── TOKEN ───────────────────────────────────────────────

async def get_bri_token_snap() -> str:
    timestamp      = get_timestamp()
    string_to_sign = f"{BRI_CLIENT_ID}|{timestamp}"

    private_key     = load_private_key()
    signature_bytes = private_key.sign(
        string_to_sign.encode("utf-8"),
        padding.PKCS1v15(),
        hashes.SHA256()
    )
    signature_b64 = base64.b64encode(signature_bytes).decode("utf-8")

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{BRI_BASE_URL}/snap/v1.0/access-token/b2b",
            json={"grantType": "client_credentials"},
            headers={
                "Content-Type":  "application/json",
                "X-CLIENT-KEY":  BRI_CLIENT_ID,
                "X-TIMESTAMP":   timestamp,
                "X-SIGNATURE":   signature_b64,
            }
        )
        data = resp.json()
        print(f"[BRI SNAP Token] {data}")
        if "accessToken" not in data:
            raise Exception(f"Gagal dapat token SNAP: {data}")
        return data["accessToken"]


# ─── SIGNATURE API ───────────────────────────────────────

def make_api_signature(method: str, path: str, token: str,
                       body: dict, timestamp: str) -> str:
    body_str       = json.dumps(body, separators=(',', ':'))
    body_hash      = hashlib.sha256(body_str.encode()).hexdigest().lower()
    string_to_sign = f"{method}:{path}:{token}:{body_hash}:{timestamp}"
    print(f"[BRI Signature] stringToSign: {string_to_sign}")

    signature = hmac.new(
        BRI_SECRET.encode("utf-8"),
        string_to_sign.encode("utf-8"),
        hashlib.sha512
    ).hexdigest()
    return signature


# ─── TRANSFER INTRABANK ──────────────────────────────────

async def transfer_bri(sender: str, receiver: str,
                       amount: int, ref_id: str) -> dict:
    token        = await get_bri_token_snap()
    bri_sender   = get_bri_account(sender)
    bri_receiver = get_bri_account(receiver)
    timestamp    = get_timestamp_plain()
    external_id  = datetime.now().strftime("%Y%m%d%H%M%S%f")[:20]
    path         = "/intrabank/snap/v2.0/transfer-intrabank"

    body = {
        "partnerReferenceNo":   datetime.now().strftime("%Y%m%d%H%M%S%f")[:20],
        "amount": {
            "value":    f"{amount}.00",
            "currency": "IDR"
        },
        "beneficiaryAccountNo": bri_receiver,
        "customerReference":    datetime.now().strftime("%Y%m%d%H%M%S")[:20],
        "feeType":              "BEN",
        "remark":               "Crypto-Sentinel Transfer",
        "sourceAccountNo":      bri_sender,
        "transactionDate":      timestamp,
        "additionalInfo": {
            "deviceId": "crypto-sentinel",
            "channel":  "API"
        }
    }

    signature = make_api_signature("POST", path, token, body, timestamp)

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{BRI_BASE_URL}{path}",
            json=body,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type":  "application/json",
                "X-TIMESTAMP":   timestamp,
                "X-SIGNATURE":   signature,
                "X-PARTNER-ID":  BRI_CLIENT_ID,
                "X-EXTERNAL-ID": external_id,
                "CHANNEL-ID":    "95221",
            }
        )
        result = resp.json()
        result["local_sender"]   = sender
        result["local_receiver"] = receiver
        result["bri_sender"]     = bri_sender
        result["bri_receiver"]   = bri_receiver
        return result