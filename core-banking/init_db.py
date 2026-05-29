import os
from dotenv import load_dotenv

# Memastikan file .env terbaca sebelum koneksi dilakukan
load_dotenv()

# Import Base dan engine dari struktur kodemu
from models.db_models import Base, engine

def init_database():
    print("Menghubungkan ke Supabase...")
    
    try:
        # Perintah ini akan menerjemahkan class model kamu menjadi tabel PostgreSQL
        Base.metadata.create_all(bind=engine)
        print("✅ Sukses! Tabel 'accounts' dan 'transactions' berhasil dibuat.")
        print("Silakan refresh halaman web Supabase kamu.")
    except Exception as e:
        print(f"❌ Gagal membuat tabel. Pastikan URL Supabase di .env sudah benar.")
        print(f"Detail error: {e}")

if __name__ == "__main__":
    init_database()