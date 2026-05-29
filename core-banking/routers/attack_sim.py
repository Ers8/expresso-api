# from fastapi import APIRouter, BackgroundTasks
# import asyncio, random, httpx

# router = APIRouter()

# @router.post("/attack/simulate")
# async def simulate_attack(background_tasks: BackgroundTasks):
#     background_tasks.add_task(run_smurfing_attack)
#     return {"message": "Attack simulation dimulai", "total_transactions": 100}

# async def run_smurfing_attack():
#     print("[ATTACK] Memulai smurfing simulation...")
#     async with httpx.AsyncClient(timeout=10.0) as client:
#         tasks = []
#         for i in range(100):
#             payload = {
#                 "sender_account": f"DUMMY-{i:04d}",
#                 "receiver_account": "1111222233",
#                 "amount": random.randint(4_900_000, 4_999_999),
#                 "purpose_code": "SALA",
#                 "description": "Transfer rutin",
#                 "destination_type": "DOMESTIC",
#                 "device_info": {
#                     "device_id": f"dev-{i}",
#                     "ip_address": "1.2.3.4",
#                     "country": "ID",
#                     "latitude": -6.2,
#                     "longitude": 106.8
#                 },
#                 "session_token": "dummy"
#             }
#             tasks.append(
#                 client.post("http://localhost:8002/api/v1/banking/transfer", json=payload)
#             )
#         results = await asyncio.gather(*tasks, return_exceptions=True)
#         blocked = sum(1 for r in results if hasattr(r, 'json') and r.json().get("status") == "BLOCKED")
#         print(f"[ATTACK] Selesai. Diblokir: {blocked}/100")