from datetime import datetime
from sqlalchemy import (
    BigInteger, Boolean, Column, DateTime, ForeignKey,
    Integer, Numeric, String, Text, UniqueConstraint
)
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"

    id            = Column(Integer, primary_key=True, autoincrement=True)
    telegram_id   = Column(BigInteger, unique=True, nullable=False)
    phone_number  = Column(String(20))
    full_name     = Column(String(255))
    username      = Column(String(100))
    is_registered = Column(Boolean, default=False)
    registered_at = Column(DateTime, default=datetime.utcnow)


class Purchase(Base):
    __tablename__ = "purchases"

    id           = Column(Integer, primary_key=True, autoincrement=True)
    telegram_id  = Column(BigInteger, ForeignKey("users.telegram_id"), nullable=False)
    # 'retry' | 'attestation_onatili' | 'attestation_adabiyot'
    product_type = Column(String(50), nullable=False)
    # 'onatili:mavzu:fonetika:easy' kabi kalit
    retry_key    = Column(String(200))
    amount       = Column(Integer, nullable=False)
    check_photo  = Column(String(200))
    status       = Column(String(20), default="pending")   # pending|confirmed|rejected
    submitted_at = Column(DateTime, default=datetime.utcnow)
    confirmed_at = Column(DateTime)
    confirmed_by = Column(BigInteger)


class UserAccess(Base):
    """Har bir test turi uchun bepul urinish holati"""
    __tablename__ = "user_access"
    __table_args__ = (UniqueConstraint("telegram_id", "access_key"),)

    id          = Column(Integer, primary_key=True, autoincrement=True)
    telegram_id = Column(BigInteger, ForeignKey("users.telegram_id"), nullable=False)
    access_key  = Column(String(200), nullable=False)
    free_used   = Column(Boolean, default=False)


class AttestationAccess(Base):
    """Atestatsiya sotib olinganmi"""
    __tablename__ = "attestation_access"
    __table_args__ = (UniqueConstraint("telegram_id", "subject"),)

    id           = Column(Integer, primary_key=True, autoincrement=True)
    telegram_id  = Column(BigInteger, ForeignKey("users.telegram_id"), nullable=False)
    subject      = Column(String(50), nullable=False)   # 'onatili' | 'adabiyot'
    format       = Column(String(20))                   # 'miniapp' | 'pdf'
    purchased_at = Column(DateTime, default=datetime.utcnow)


class Question(Base):
    __tablename__ = "questions"

    id             = Column(Integer, primary_key=True, autoincrement=True)
    subject        = Column(String(50), nullable=False)   # 'onatili' | 'adabiyot'
    # 'mavzu'|'aralash'|'sinf'|'gazallar'|'attestation'
    category       = Column(String(50), nullable=False)
    # mavzu: 'fonetika'... | sinf: '5'..'11' | boshqalar: None
    subcategory    = Column(String(50))
    difficulty     = Column(String(20))                   # easy|medium|hard|None(attestation)
    is_attestation = Column(Boolean, default=False)
    order_num      = Column(Integer)                      # faqat attestation uchun
    question_text  = Column(Text, nullable=False)
    option_a       = Column(Text, nullable=False)
    option_b       = Column(Text, nullable=False)
    option_c       = Column(Text, nullable=False)
    option_d       = Column(Text, nullable=False)
    correct_answer = Column(String(1), nullable=False)    # 'A'|'B'|'C'|'D'
    image_file_id  = Column(String(200))
    created_at     = Column(DateTime, default=datetime.utcnow)


class TestResult(Base):
    __tablename__ = "test_results"

    id             = Column(Integer, primary_key=True, autoincrement=True)
    telegram_id    = Column(BigInteger, ForeignKey("users.telegram_id"), nullable=False)
    subject        = Column(String(50))
    category       = Column(String(50))
    subcategory    = Column(String(50))
    difficulty     = Column(String(20))
    is_attestation = Column(Boolean, default=False)
    total          = Column(Integer, default=35)
    correct        = Column(Integer, default=0)
    wrong          = Column(Integer, default=0)
    skipped        = Column(Integer, default=0)
    score          = Column(Numeric(5, 2), default=0)
    attempt_number = Column(Integer, default=1)
    started_at     = Column(DateTime)
    finished_at    = Column(DateTime, default=datetime.utcnow)
