from sqlalchemy import create_engine, Column, String
from sqlalchemy import BigInteger, Boolean, Float, Text, TIMESTAMP, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import declarative_base
from dotenv import load_dotenv
import os

load_dotenv()

Base = declarative_base()
engine = create_engine(os.getenv("DATABASE_URL"))

class Account(Base):
    __tablename__ = "accounts"
    account_id    = Column(String(20), primary_key=True)
    owner_name    = Column(String(100), nullable=False)
    balance       = Column(BigInteger, default=0)
    risk_profile  = Column(String(10), default='LOW')
    is_active     = Column(Boolean, default=True)
    is_blocked    = Column(Boolean, default=False)
    last_activity = Column(TIMESTAMP)
    created_at    = Column(TIMESTAMP, server_default=func.now())

class Transaction(Base):
    __tablename__ = "transactions"
    transaction_id    = Column(String(30), primary_key=True)
    sender_account    = Column(String(20), nullable=False)
    receiver_account  = Column(String(20), nullable=False)
    amount            = Column(BigInteger, nullable=False)
    purpose_code      = Column(String(10))
    description       = Column(Text)
    destination_type  = Column(String(20))
    ip_address        = Column(String(45))
    country_code      = Column(String(5))
    latitude          = Column(Float)
    longitude         = Column(Float)
    timestamp         = Column(TIMESTAMP, nullable=False)
    sentinel_score    = Column(Float)
    sentinel_decision = Column(String(10))
    status            = Column(String(15), default='PENDING')

class SentinelAlert(Base):
    __tablename__ = "sentinel_alerts"
    alert_id        = Column(BigInteger, primary_key=True, autoincrement=True)
    transaction_id  = Column(String(30))
    risk_score      = Column(Float)
    indicators_json = Column(JSONB)
    shap_values_json= Column(JSONB)
    cluster_id      = Column(String(30))
    resolved        = Column(Boolean, default=False)
    created_at      = Column(TIMESTAMP, server_default=func.now())
    
class STRDraft(Base):
    __tablename__ = "str_drafts"
    str_id        = Column(String(30), primary_key=True)
    alert_id      = Column(BigInteger)
    summary_text  = Column(Text)
    risk_factors  = Column(JSONB)
    status        = Column(String(20), default='DRAFT')  # DRAFT | REVIEWED | SENT
    analyst_id    = Column(String(50))
    created_at    = Column(TIMESTAMP, server_default=func.now())

if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
    print("Tabel berhasil dibuat!")