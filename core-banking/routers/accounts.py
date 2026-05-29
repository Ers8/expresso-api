# from fastapi import APIRouter, HTTPException
# from sqlalchemy.orm import Session
# from models.db_models import Account, Transaction, engine
# from bri_client import get_bri_token_snap, transfer_bri
# from datetime import datetime

# router = APIRouter()


# # ================================================================
# # AKUN & DASHBOARD
# # ================================================================

# @router.get("/account/{account_id}")
# def get_account(account_id: str):
#     with Session(engine) as db:
#         acc = db.get(Account, account_id)
#         if not acc:
#             raise HTTPException(status_code=404, detail="Akun tidak ditemukan")
#         return {
#             "account_id":   acc.account_id,
#             "owner_name":   acc.owner_name,
#             "balance":      acc.balance,
#             "risk_profile": acc.risk_profile,
#             "is_blocked":   acc.is_blocked,
#             "is_active":    acc.is_active
#         }


# @router.get("/dashboard/alerts")
# def get_alerts(limit: int = 20, status: str = None):
#     with Session(engine) as db:
#         query = db.query(Transaction)
#         if status:
#             query = query.filter(Transaction.status == status)
#         txs = query.order_by(Transaction.timestamp.desc()).limit(limit).all()
#         return [
#             {
#                 "transaction_id": t.transaction_id,
#                 "sender":         t.sender_account,
#                 "receiver":       t.receiver_account,
#                 "amount":         t.amount,
#                 "risk_score":     t.sentinel_score,
#                 "decision":       t.sentinel_decision,
#                 "status":         t.status,
#                 "timestamp":      str(t.timestamp),
#                 "country":        t.country_code,
#             }
#             for t in txs
#         ]


# # ================================================================
# # HISTORY TRANSAKSI
# # ================================================================

# @router.get("/history/{account_id}")
# def get_transaction_history(account_id: str, limit: int = 10, status: str = None):
#     with Session(engine) as db:
#         acc = db.get(Account, account_id)
#         if not acc:
#             raise HTTPException(status_code=404, detail="Akun tidak ditemukan")

#         from sqlalchemy import or_
#         query = db.query(Transaction).filter(
#             or_(
#                 Transaction.sender_account   == account_id,
#                 Transaction.receiver_account == account_id
#             )
#         )
#         if status:
#             query = query.filter(Transaction.status == status)

#         txs = query.order_by(Transaction.timestamp.desc()).limit(limit).all()

#         history = []
#         for t in txs:
#             if t.sender_account == account_id:
#                 direction      = "DEBIT"
#                 counterpart_id = t.receiver_account
#             else:
#                 direction      = "CREDIT"
#                 counterpart_id = t.sender_account

#             counterpart      = db.get(Account, counterpart_id)
#             counterpart_name = counterpart.owner_name if counterpart else counterpart_id

#             history.append({
#                 "transaction_id":    t.transaction_id,
#                 "direction":         direction,
#                 "counterpart_id":    counterpart_id,
#                 "counterpart_name":  counterpart_name,
#                 "amount":            t.amount,
#                 "status":            t.status,
#                 "purpose_code":      t.purpose_code,
#                 "description":       t.description,
#                 "sentinel_decision": t.sentinel_decision,
#                 "timestamp":         str(t.timestamp),
#             })

#         return {
#             "account_id":   account_id,
#             "owner_name":   acc.owner_name,
#             "balance":      acc.balance,
#             "total_shown":  len(history),
#             "transactions": history
#         }


# @router.get("/history/all/transactions")
# def get_all_transactions(limit: int = 20, status: str = None):
#     with Session(engine) as db:
#         query = db.query(Transaction)
#         if status:
#             query = query.filter(Transaction.status == status)
#         txs = query.order_by(Transaction.timestamp.desc()).limit(limit).all()
#         return {
#             "total_shown": len(txs),
#             "transactions": [
#                 {
#                     "transaction_id":    t.transaction_id,
#                     "sender_account":    t.sender_account,
#                     "receiver_account":  t.receiver_account,
#                     "amount":            t.amount,
#                     "destination_type":  t.destination_type,
#                     "status":            t.status,
#                     "sentinel_decision": t.sentinel_decision,
#                     "timestamp":         str(t.timestamp),
#                 }
#                 for t in txs
#             ]
#         }


# # ================================================================
# # BRI SANDBOX
# # ================================================================

# @router.get("/bri/token-snap-test")
# async def test_bri_token_snap():
#     """Test token SNAP B2B"""
#     try:
#         token = await get_bri_token_snap()
#         return {
#             "status":        "SUCCESS",
#             "type":          "SNAP B2B",
#             "token_preview": token[:30] + "..."
#         }
#     except Exception as e:
#         return {"status": "FAILED", "message": str(e)}


# @router.post("/bri/transfer-test")
# async def bri_transfer_test(
#     sender: str = "0123456789",
#     receiver: str = "9876543210",
#     amount: int = 100000
# ):
#     """Test transfer intrabank langsung ke BRI (tanpa update DB)"""
#     try:
#         result = await transfer_bri(sender, receiver, amount, "test")
#         return {"status": "SUCCESS", "data": result}
#     except Exception as e:
#         return {"status": "FAILED", "message": str(e)}


# @router.post("/bri/transfer-from-db")
# async def bri_transfer_from_db(
#     sender_account_id: str = "0123456789",
#     receiver_account_id: str = "9876543210",
#     amount: int = 100000
# ):
#     """Transfer dengan validasi & update saldo dari DB"""
#     with Session(engine) as db:
#         sender   = db.get(Account, sender_account_id)
#         receiver = db.get(Account, receiver_account_id)

#         if not sender:
#             raise HTTPException(status_code=404, detail=f"Akun pengirim tidak ditemukan")
#         if not receiver:
#             raise HTTPException(status_code=404, detail=f"Akun penerima tidak ditemukan")
#         if sender.is_blocked:
#             raise HTTPException(status_code=403, detail=f"Akun {sender.owner_name} diblokir")
#         if sender.balance < amount:
#             raise HTTPException(
#                 status_code=400,
#                 detail=f"Saldo {sender.owner_name} tidak mencukupi. "
#                        f"Saldo: Rp{sender.balance:,} | Dibutuhkan: Rp{amount:,}"
#             )

#         balance_before = sender.balance

#         try:
#             bri_response = await transfer_bri(
#                 sender   = sender_account_id,
#                 receiver = receiver_account_id,
#                 amount   = amount,
#                 ref_id   = "db"
#             )

#             response_code = bri_response.get("responseCode", "")
#             if not response_code.startswith("2"):
#                 raise Exception(
#                     f"BRI menolak — Code: {response_code}, "
#                     f"Message: {bri_response.get('responseMessage')}"
#                 )

#             sender.balance   -= amount
#             receiver.balance += amount
#             db.commit()

#             return {
#                 "status": "SUCCESS",
#                 "transfer_info": {
#                     "sender":         sender.owner_name,
#                     "receiver":       receiver.owner_name,
#                     "amount":         f"Rp{amount:,}",
#                     "balance_before": f"Rp{balance_before:,}",
#                     "balance_after":  f"Rp{sender.balance:,}",
#                 },
#                 "bri_response": bri_response
#             }

#         except HTTPException:
#             raise
#         except Exception as e:
#             raise HTTPException(status_code=502, detail=str(e))