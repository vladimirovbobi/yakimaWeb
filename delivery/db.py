"""SQLAlchemy models mirroring the Django apps/delivery/ schema.

Single source of truth for migrations is Django; this module just declares
the read/write shape this service uses. Keep field names in sync.
"""
from __future__ import annotations

import datetime as dt
from collections.abc import AsyncIterator

from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, relationship

from config import get_settings


class Base(DeclarativeBase):
    pass


class DeliveryPackage(Base):
    __tablename__ = "delivery_packages"

    id           = Column(BigInteger, primary_key=True)
    lead_id      = Column(BigInteger, nullable=False, index=True)
    vendor_id    = Column(BigInteger, nullable=False, index=True)
    buyer_id     = Column(BigInteger, nullable=False, index=True)
    name         = Column(String(240), nullable=False, default="Delivery")
    note         = Column(Text, nullable=False, default="")
    status       = Column(String(16), nullable=False, default="open")
    finalized_at = Column(DateTime(timezone=True), nullable=True)
    created_at   = Column(DateTime(timezone=True), nullable=False, default=dt.datetime.utcnow)
    updated_at   = Column(DateTime(timezone=True), nullable=False, default=dt.datetime.utcnow,
                          onupdate=dt.datetime.utcnow)

    files = relationship("DeliveryFile", back_populates="package", cascade="all, delete-orphan")


class DeliveryFile(Base):
    __tablename__ = "delivery_files"

    id           = Column(BigInteger, primary_key=True)
    package_id   = Column(BigInteger, ForeignKey("delivery_packages.id", ondelete="CASCADE"),
                          nullable=False, index=True)
    filename     = Column(String(240), nullable=False)
    content_type = Column(String(80), nullable=False)
    size_bytes   = Column(BigInteger, nullable=False)
    sha256       = Column(String(64), nullable=False, default="")
    storage_path = Column(String(512), nullable=False)
    scan_status  = Column(String(16), nullable=False, default="pending")  # pending|clean|infected|skipped
    created_at   = Column(DateTime(timezone=True), nullable=False, default=dt.datetime.utcnow)

    package = relationship("DeliveryPackage", back_populates="files")


class DeliveryAccessLog(Base):
    __tablename__ = "delivery_access_log"

    id          = Column(BigInteger, primary_key=True)
    package_id  = Column(BigInteger, ForeignKey("delivery_packages.id", ondelete="CASCADE"),
                         nullable=False, index=True)
    file_id     = Column(BigInteger, ForeignKey("delivery_files.id", ondelete="SET NULL"),
                         nullable=True, index=True)
    user_id     = Column(BigInteger, nullable=False, index=True)
    action      = Column(String(24), nullable=False)  # manifest|download|finalize
    ip_addr     = Column(String(64), nullable=False, default="")
    user_agent  = Column(String(240), nullable=False, default="")
    created_at  = Column(DateTime(timezone=True), nullable=False, default=dt.datetime.utcnow,
                         index=True)


_engine = None
_sessionmaker = None


def get_engine():
    global _engine
    if _engine is None:
        _engine = create_async_engine(
            get_settings().database_url,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,
        )
    return _engine


def get_sessionmaker() -> async_sessionmaker[AsyncSession]:
    global _sessionmaker
    if _sessionmaker is None:
        _sessionmaker = async_sessionmaker(get_engine(), expire_on_commit=False)
    return _sessionmaker


async def get_session() -> AsyncIterator[AsyncSession]:
    async with get_sessionmaker()() as session:
        yield session
