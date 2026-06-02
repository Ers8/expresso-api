import os
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from dotenv import load_dotenv
from models.db_models import Base, Account, Transaction, SentinelAlert, STRDraft

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL tidak ditemukan di file .env")

engine = create_engine(DATABASE_URL)

def seed_data():
    # Pastikan tabel sudah terbuat
    Base.metadata.create_all(bind=engine)
    
    with Session(engine) as db:
        print("Memeriksa data akun dummy...")
        
        dummy_accounts = [
            Account(
                account_id="1234567890",
                owner_name="Billy Jonathan",
                balance=125750000,
                risk_profile="LOW",
                is_active=True,
                is_blocked=False
            ),
            Account(
                account_id="0123456789",
                owner_name="Pengirim Dummy 1",
                balance=10000000,
                risk_profile="LOW",
                is_active=True,
                is_blocked=False
            ),
            Account(
                account_id="1122334455",
                owner_name="Penerima Dummy 1",
                balance=5000000,
                risk_profile="LOW",
                is_active=True,
                is_blocked=False
            ),
            Account(
                account_id="5544332211",
                owner_name="Pengirim Dummy 2",
                balance=8000000,
                risk_profile="LOW",
                is_active=True,
                is_blocked=False
            ),
            Account(
                account_id="9876543210",
                owner_name="Penerima Dummy 2",
                balance=3000000,
                risk_profile="LOW",
                is_active=True,
                is_blocked=False
            )
        ]
        
        inserted_count = 0
        for acc in dummy_accounts:
            existing = db.get(Account, acc.account_id)
            if not existing:
                db.add(acc)
                inserted_count += 1
                print(f"Menambahkan akun: {acc.owner_name} ({acc.account_id})")
        
        if inserted_count > 0:
            db.commit()
            print(f"Seeding selesai! {inserted_count} akun baru berhasil ditambahkan.")
        else:
            print("Semua akun dummy sudah terdaftar di database.")

if __name__ == "__main__":
    seed_data()
