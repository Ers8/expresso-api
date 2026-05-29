from sqlalchemy.orm import Session
from models.db_models import Account, engine

def seed():
    with Session(engine) as db:
        # Cek dulu apakah sudah ada data
        existing = db.query(Account).first()
        if existing:
            print("Data sudah ada, skip seeding.")
            return

        accounts = [
            # Akun normal (untuk demo transaksi aman)
            Account(account_id="0123456789", owner_name="Billy Jonathan",
                    balance=10_000_000, risk_profile="LOW"),

            # Akun crypto exchange (tujuan transfer mencurigakan)
            Account(account_id="9876543210", owner_name="Crypto Exchange Int",
                    balance=0, risk_profile="HIGH"),

            # Mule account (target smurfing attack)
            Account(account_id="1111222233", owner_name="Mule Account A",
                    balance=0, risk_profile="HIGH"),

            # Akun anggota tim untuk demo
            Account(account_id="1122334455", owner_name="Rifki Firmansyah",
                    balance=5_000_000, risk_profile="LOW"),
            Account(account_id="5544332211", owner_name="Desta Erlangga",
                    balance=7_500_000, risk_profile="LOW"),
            Account(account_id="9988776655", owner_name="Aam Setiana",
                    balance=3_000_000, risk_profile="LOW"),
        ]

        db.add_all(accounts)
        db.commit()
        print(f"Seed berhasil! {len(accounts)} akun ditambahkan.")

if __name__ == "__main__":
    seed()