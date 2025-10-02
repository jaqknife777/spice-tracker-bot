"""
Database module using SQLAlchemy ORM for transparent database abstraction.
Supports both PostgreSQL and SQLite through DATABASE_URL configuration.
"""
import os
import asyncio
import time
from datetime import datetime, timedelta, timezone
from contextlib import asynccontextmanager
from typing import Optional, List, Dict, Any

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool, StaticPool
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, Float, Boolean, DateTime, Text, ForeignKey, select, update, delete, func, Index
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

from utils.logger import logger


def _get_naive_utc_now():
    """Returns the current UTC datetime as a naive datetime object."""
    return datetime.now(timezone.utc).astimezone(timezone.utc).replace(tzinfo=None)


class Base(DeclarativeBase):
    """Base class for all database models."""
    def to_dict(self) -> Dict[str, Any]:
        """Converts the model instance to a dictionary."""
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class User(Base):
    """User model."""
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    username: Mapped[str] = mapped_column(String(100), nullable=False)
    total_melange: Mapped[int] = mapped_column(Integer, default=0)
    paid_melange: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_get_naive_utc_now)
    last_updated: Mapped[datetime] = mapped_column(DateTime, default=_get_naive_utc_now, onupdate=_get_naive_utc_now)

    # Relationships
    deposits: Mapped[List["Deposit"]] = relationship("Deposit", back_populates="user")
    expedition_participants: Mapped[List["ExpeditionParticipant"]] = relationship("ExpeditionParticipant", back_populates="user")
    melange_payments: Mapped[List["MelangePayment"]] = relationship("MelangePayment", back_populates="user")

    # Indices
    __table_args__ = (
        Index('ix_users_user_id', 'user_id'),
        Index('ix_users_leaderboard', 'total_melange', 'username'),
    )


class Deposit(Base):
    """Deposit model."""
    __tablename__ = "deposits"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(50), ForeignKey("users.user_id"), nullable=False)
    username: Mapped[str] = mapped_column(String(100), nullable=False)
    sand_amount: Mapped[int] = mapped_column(Integer, nullable=False)
    type: Mapped[str] = mapped_column(String(20), default="solo")
    expedition_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("expeditions.id"))
    melange_amount: Mapped[Optional[int]] = mapped_column(Integer)
    conversion_rate: Mapped[Optional[float]] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_get_naive_utc_now)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="deposits")
    expedition: Mapped[Optional["Expedition"]] = relationship("Expedition", back_populates="deposits")

    # Indices
    __table_args__ = (
        Index('ix_deposits_user_id', 'user_id'),
        Index('ix_deposits_user_created', 'user_id', 'created_at'),
        Index('ix_deposits_expedition_id', 'expedition_id'),
    )


class Expedition(Base):
    """Expedition model."""
    __tablename__ = "expeditions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    initiator_id: Mapped[str] = mapped_column(String(50), ForeignKey("users.user_id"), nullable=False)
    initiator_username: Mapped[str] = mapped_column(String(100), nullable=False)
    total_sand: Mapped[int] = mapped_column(Integer, nullable=False)
    sand_per_melange: Mapped[Optional[int]] = mapped_column(Integer)
    guild_cut_percentage: Mapped[float] = mapped_column(Float, default=10.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_get_naive_utc_now)

    # Relationships
    initiator: Mapped["User"] = relationship("User", foreign_keys=[initiator_id])
    participants: Mapped[List["ExpeditionParticipant"]] = relationship("ExpeditionParticipant", back_populates="expedition")
    deposits: Mapped[List["Deposit"]] = relationship("Deposit", back_populates="expedition")


class ExpeditionParticipant(Base):
    """Expedition participant model."""
    __tablename__ = "expedition_participants"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    expedition_id: Mapped[int] = mapped_column(Integer, ForeignKey("expeditions.id"), nullable=False)
    user_id: Mapped[str] = mapped_column(String(50), ForeignKey("users.user_id"), nullable=False)
    username: Mapped[str] = mapped_column(String(100), nullable=False)
    sand_amount: Mapped[int] = mapped_column(Integer, nullable=False)
    melange_amount: Mapped[int] = mapped_column(Integer, nullable=False)
    is_harvester: Mapped[bool] = mapped_column(Boolean, default=False)

    # Relationships
    expedition: Mapped["Expedition"] = relationship("Expedition", back_populates="participants")
    user: Mapped["User"] = relationship("User", back_populates="expedition_participants")

    # Indices
    __table_args__ = (
        Index('ix_expedition_participants_expedition_id', 'expedition_id'),
        Index('ix_expedition_participants_user_id', 'user_id'),
    )


class GuildTreasury(Base):
    """Guild treasury model."""
    __tablename__ = "guild_treasury"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    total_sand: Mapped[int] = mapped_column(Integer, default=0)
    total_melange: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_get_naive_utc_now)
    last_updated: Mapped[datetime] = mapped_column(DateTime, default=_get_naive_utc_now, onupdate=_get_naive_utc_now)

    # Indices
    __table_args__ = (
        Index('ix_guild_treasury_id_desc', 'id'),
    )


class GuildTransaction(Base):
    """Guild transaction model."""
    __tablename__ = "guild_transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    transaction_type: Mapped[str] = mapped_column(String(50), nullable=False)
    sand_amount: Mapped[int] = mapped_column(Integer, nullable=False)
    melange_amount: Mapped[int] = mapped_column(Integer, default=0)
    expedition_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("expeditions.id"))
    admin_user_id: Mapped[str] = mapped_column(String(50), nullable=False)
    admin_username: Mapped[str] = mapped_column(String(100), nullable=False)
    target_user_id: Mapped[Optional[str]] = mapped_column(String(50))
    target_username: Mapped[Optional[str]] = mapped_column(String(100))
    description: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_get_naive_utc_now)

    # Indices
    __table_args__ = (
        Index('ix_guild_transactions_expedition_id', 'expedition_id'),
        Index('ix_guild_transactions_admin', 'admin_user_id'),
        Index('ix_guild_transactions_target_user', 'target_user_id'),
    )


class MelangePayment(Base):
    """Melange payment model."""
    __tablename__ = "melange_payments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(50), ForeignKey("users.user_id"), nullable=False)
    username: Mapped[str] = mapped_column(String(100), nullable=False)
    melange_amount: Mapped[int] = mapped_column(Integer, nullable=False)
    admin_user_id: Mapped[Optional[str]] = mapped_column(String(50))
    admin_username: Mapped[Optional[str]] = mapped_column(String(100))
    description: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_get_naive_utc_now)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="melange_payments")

    # Indices
    __table_args__ = (
        Index('ix_melange_payments_user_id', 'user_id'),
        Index('ix_melange_payments_admin', 'admin_user_id'),
    )


class GlobalSetting(Base):
    """Global setting model."""
    __tablename__ = "global_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    setting_key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    setting_value: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_get_naive_utc_now)
    last_updated: Mapped[datetime] = mapped_column(DateTime, default=_get_naive_utc_now, onupdate=_get_naive_utc_now)

    # Indices
    __table_args__ = (
        Index('ix_global_settings_setting_key', 'setting_key'),
    )


class Database:
    """Database class using SQLAlchemy ORM for transparent database abstraction."""

    def __init__(self, database_url=None, for_testing=False):
        self.database_url = database_url or os.getenv('DATABASE_URL')
        if not self.database_url:
            raise ValueError("DATABASE_URL environment variable is required")

        # Detect database type using URL scheme
        from urllib.parse import urlparse
        parsed_url = urlparse(self.database_url)
        self.is_sqlite = parsed_url.scheme.startswith('sqlite')

        engine_kwargs = {
            "echo": False,
            "future": True,
        }

        if for_testing and self.is_sqlite:
            engine_kwargs["poolclass"] = StaticPool
            engine_kwargs["connect_args"] = {"check_same_thread": False}
        else:
            engine_kwargs["poolclass"] = NullPool
            engine_kwargs["pool_pre_ping"] = True

        # Create async engine
        self.engine = create_async_engine(self.database_url, **engine_kwargs)

        # Create session factory
        self.session_factory = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )

        # Detect database type using URL scheme
        from urllib.parse import urlparse
        parsed_url = urlparse(self.database_url)
        self.is_sqlite = parsed_url.scheme.startswith('sqlite')

        # Connection pool settings
        self.max_retries = 3
        self.retry_delay = 1.0

    @asynccontextmanager
    async def _get_connection(self):
        """Legacy method for backward compatibility with tests."""
        async with self._get_session() as session:
            yield session

    @asynccontextmanager
    async def _get_session(self):
        """Context manager for database sessions with retry logic.
        Retries only session creation failures; exceptions from within the context propagate.
        """
        last_error = None

        for attempt in range(self.max_retries):
            start_time = time.time()
            session = None
            try:
                # Attempt to create a session
                session = self.session_factory()
                connection_time = time.time() - start_time
                logger.database_operation(
                    operation="session_created",
                    table="session_pool",
                    success=True,
                    attempt=attempt + 1,
                    connection_time=f"{connection_time:.3f}s"
                )
            except Exception as e:
                # Failed to create session; log and retry
                last_error = e
                connection_time = time.time() - start_time
                logger.database_operation(
                    operation="session_failed",
                    table="session_pool",
                    success=False,
                    attempt=attempt + 1,
                    connection_time=f"{connection_time:.3f}s",
                    error=str(e)
                )
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay * (attempt + 1))
                    continue
                else:
                    raise last_error

            try:
                # Hand control to the caller
                yield session
                return
            finally:
                if session:
                    try:
                        await asyncio.wait_for(session.close(), timeout=5.0)
                    except (asyncio.TimeoutError, Exception) as close_error:
                        logger.warning(f"Session close timeout/failure: {close_error}")

    @asynccontextmanager
    async def transaction(self):
        """Context manager for atomic database transactions."""
        async with self._get_session() as session:
            try:
                yield session
                await session.commit()
            except Exception as e:
                await session.rollback()
                logger.error(f"Transaction failed, rolling back: {e}")
                raise

    async def _log_operation(self, operation: str, table: str, start_time: float, success: bool = True, **kwargs):
        """Log database operation performance metrics"""
        execution_time = time.time() - start_time
        logger.database_operation(
            operation=operation,
            table=table,
            success=success,
            execution_time=f"{execution_time:.3f}s",
            **kwargs
        )
        return execution_time

    async def initialize(self):
        """Initialize database - create tables for SQLite, test connectivity for PostgreSQL"""
        start_time = time.time()
        try:
            async with self.engine.begin() as conn:
                if self.is_sqlite:
                    # Create all tables for SQLite
                    await conn.run_sync(Base.metadata.create_all)
                else:
                    # Test connectivity for PostgreSQL (tables should exist from migrations)
                    await conn.execute(select(1))

            init_time = time.time() - start_time
            await self._log_operation("connectivity_check", "database", start_time, success=True, init_time=f"{init_time:.3f}s")
            print(f'✅ Database connected in {init_time:.3f}s')

        except Exception as e:
            init_time = time.time() - start_time
            await self._log_operation("connectivity_check", "database", start_time, success=False, init_time=f"{init_time:.3f}s", error=str(e))
            print(f'❌ Database connection failed in {init_time:.3f}s: {e}')
            raise e

    async def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user data by user ID"""
        start_time = time.time()
        async with self._get_session() as session:
            try:
                result = await session.execute(
                    select(User).where(User.user_id == user_id)
                )
                user = result.scalar_one_or_none()

                if user:
                    await self._log_operation("select", "users", start_time, success=True, user_id=user_id, found=True)
                    return user.to_dict()
                else:
                    await self._log_operation("select", "users", start_time, success=True, user_id=user_id, found=False)
                    return None
            except Exception as e:
                await self._log_operation("select", "users", start_time, success=False, user_id=user_id, error=str(e))
                raise e

    async def _upsert_user(self, session: AsyncSession, user_id: str, username: str):
        """Creates or updates a user within an existing session."""
        insert_func = sqlite_insert if self.is_sqlite else pg_insert

        stmt = insert_func(User).values(
            user_id=user_id,
            username=username,
            last_updated=_get_naive_utc_now()
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=['user_id'],
            set_=dict(
                username=stmt.excluded.username,
                last_updated=stmt.excluded.last_updated
            )
        )
        await session.execute(stmt)

    async def upsert_user(self, user_id: str, username: str):
        """Create or update user"""
        start_time = time.time()
        try:
            async with self.transaction() as session:
                await self._upsert_user(session, user_id, username)
            await self._log_operation("upsert", "users", start_time, success=True, user_id=user_id, username=username)
        except Exception as e:
            await self._log_operation("upsert", "users", start_time, success=False, user_id=user_id, username=username, error=str(e))
            raise e

    async def add_deposit(self, user_id: str, username: str, sand_amount: int, deposit_type: str = 'solo', expedition_id: Optional[int] = None, melange_amount: Optional[int] = None, conversion_rate: Optional[float] = None):
        """Add a new sand deposit for a user"""
        start_time = time.time()
        try:
            async with self.transaction() as session:
                # Ensure user exists
                await self._upsert_user(session, user_id, username)

                # Add deposit record
                deposit = Deposit(
                    user_id=user_id,
                    username=username,
                    sand_amount=sand_amount,
                    type=deposit_type,
                    expedition_id=expedition_id,
                    melange_amount=melange_amount,
                    conversion_rate=conversion_rate
                )
                session.add(deposit)

            await self._log_operation("insert", "deposits", start_time, success=True,
                                    user_id=user_id, sand_amount=sand_amount, deposit_type=deposit_type, expedition_id=expedition_id)
        except Exception as e:
            await self._log_operation("insert", "deposits", start_time, success=False,
                                    user_id=user_id, sand_amount=sand_amount, deposit_type=deposit_type, expedition_id=expedition_id, error=str(e))
            raise e

    async def get_user_deposits(self, user_id: str, page: int = 1, per_page: int = 10) -> List[Dict[str, Any]]:
        """Get a paginated list of deposits for a user."""
        start_time = time.time()
        async with self._get_session() as session:
            try:
                offset = (page - 1) * per_page
                query = (
                    select(Deposit)
                    .where(Deposit.user_id == user_id)
                    .order_by(Deposit.created_at.desc())
                    .offset(offset)
                    .limit(per_page)
                )
                result = await session.execute(query)
                deposits = result.scalars().all()
                deposit_list = [d.to_dict() for d in deposits]

                await self._log_operation("select", "deposits", start_time, success=True,
                                        user_id=user_id, result_count=len(deposit_list))
                return deposit_list
            except Exception as e:
                await self._log_operation("select", "deposits", start_time, success=False,
                                        user_id=user_id, error=str(e))
                raise e

    async def get_user_deposits_count(self, user_id: str) -> int:
        """Get the total number of deposits for a user."""
        start_time = time.time()
        async with self._get_session() as session:
            try:
                query = select(func.count()).select_from(Deposit).where(Deposit.user_id == user_id)
                result = await session.execute(query)
                count = result.scalar_one()
                await self._log_operation("count", "deposits", start_time, success=True, user_id=user_id, count=count)
                return count
            except Exception as e:
                await self._log_operation("count", "deposits", start_time, success=False, user_id=user_id, error=str(e))
                raise e

    async def get_guild_transactions_paginated(self, page: int = 1, per_page: int = 10) -> List[Dict[str, Any]]:
        """Get a paginated list of all guild transactions."""
        start_time = time.time()
        async with self._get_session() as session:
            try:
                offset = (page - 1) * per_page
                query = (
                    select(GuildTransaction)
                    .order_by(GuildTransaction.created_at.desc())
                    .offset(offset)
                    .limit(per_page)
                )
                result = await session.execute(query)
                transactions = result.scalars().all()
                transaction_list = [t.to_dict() for t in transactions]

                await self._log_operation("select_paginated", "guild_transactions", start_time, success=True,
                                        result_count=len(transaction_list))
                return transaction_list
            except Exception as e:
                await self._log_operation("select_paginated", "guild_transactions", start_time, success=False, error=str(e))
                raise e

    async def get_guild_transactions_count(self) -> int:
        """Get the total number of guild transactions."""
        start_time = time.time()
        async with self._get_session() as session:
            try:
                query = select(func.count()).select_from(GuildTransaction)
                result = await session.execute(query)
                count = result.scalar_one()
                await self._log_operation("count", "guild_transactions", start_time, success=True, count=count)
                return count
            except Exception as e:
                await self._log_operation("count", "guild_transactions", start_time, success=False, error=str(e))
                raise e

    async def get_melange_payouts(self, page: int = 1, per_page: int = 10) -> List[Dict[str, Any]]:
        """Get a paginated list of all melange payouts."""
        start_time = time.time()
        async with self._get_session() as session:
            try:
                offset = (page - 1) * per_page
                query = (
                    select(MelangePayment)
                    .order_by(MelangePayment.created_at.desc())
                    .offset(offset)
                    .limit(per_page)
                )
                result = await session.execute(query)
                payouts = result.scalars().all()
                payout_list = [p.to_dict() for p in payouts]

                await self._log_operation("select_paginated", "melange_payments", start_time, success=True,
                                        result_count=len(payout_list))
                return payout_list
            except Exception as e:
                await self._log_operation("select_paginated", "melange_payments", start_time, success=False, error=str(e))
                raise e

    async def get_melange_payouts_count(self) -> int:
        """Get the total number of melange payouts."""
        start_time = time.time()
        async with self._get_session() as session:
            try:
                query = select(func.count()).select_from(MelangePayment)
                result = await session.execute(query)
                count = result.scalar_one()
                await self._log_operation("count", "melange_payments", start_time, success=True, count=count)
                return count
            except Exception as e:
                await self._log_operation("count", "melange_payments", start_time, success=False, error=str(e))
                raise e

    async def create_expedition(self, initiator_id: str, initiator_username: str, total_sand: int,
                              sand_per_melange: Optional[int] = None, guild_cut_percentage: float = 10.0) -> int:
        """Create a new expedition record"""
        start_time = time.time()
        try:
            async with self.transaction() as session:
                expedition = Expedition(
                    initiator_id=initiator_id,
                    initiator_username=initiator_username,
                    total_sand=total_sand,
                    sand_per_melange=sand_per_melange,
                    guild_cut_percentage=guild_cut_percentage
                )
                session.add(expedition)
                await session.flush()  # Use flush to get the ID before commit
                await session.refresh(expedition)
                expedition_id = expedition.id

            await self._log_operation("insert", "expeditions", start_time, success=True,
                                    initiator_id=initiator_id, total_sand=total_sand, expedition_id=expedition_id, guild_cut_percentage=guild_cut_percentage)
            return expedition_id
        except Exception as e:
            await self._log_operation("insert", "expeditions", start_time, success=False,
                                    initiator_id=initiator_id, total_sand=total_sand, error=str(e))
            raise e

    async def get_guild_treasury(self) -> Dict[str, Any]:
        """Get guild treasury information"""
        start_time = time.time()
        try:
            async with self.transaction() as session:
                result = await session.execute(
                    select(GuildTreasury).order_by(GuildTreasury.id.desc()).limit(1)
                )
                treasury = result.scalar_one_or_none()

                if not treasury:
                    # Create initial treasury record if none exists
                    treasury = GuildTreasury()
                    session.add(treasury)
                    await session.flush()
                    await session.refresh(treasury)

                treasury_dict = treasury.to_dict()

            await self._log_operation("select", "guild_treasury", start_time, success=True)
            return treasury_dict
        except Exception as e:
            await self._log_operation("select", "guild_treasury", start_time, success=False, error=str(e))
            raise e

    async def update_guild_treasury(self, sand_amount: int, melange_amount: int = 0):
        """Add sand and melange to guild treasury"""
        start_time = time.time()
        try:
            async with self.transaction() as session:
                # Get or create treasury record
                result = await session.execute(
                    select(GuildTreasury).order_by(GuildTreasury.id.desc()).limit(1)
                )
                treasury = result.scalar_one_or_none()

                if treasury:
                    treasury.total_sand += sand_amount
                    treasury.total_melange += melange_amount
                    treasury.last_updated = _get_naive_utc_now()
                else:
                    treasury = GuildTreasury(
                        total_sand=sand_amount,
                        total_melange=melange_amount
                    )
                    session.add(treasury)

            await self._log_operation("update", "guild_treasury", start_time, success=True,
                                    sand_amount=sand_amount, melange_amount=melange_amount)
            return True
        except Exception as e:
            await self._log_operation("update", "guild_treasury", start_time, success=False,
                                    sand_amount=sand_amount, melange_amount=melange_amount, error=str(e))
            raise e

    # Add other methods as needed...
    # For brevity, I'll add a few more key methods

    async def update_user_melange(self, user_id: str, melange_amount: int):
        """Update user melange amount"""
        start_time = time.time()
        try:
            async with self.transaction() as session:
                await session.execute(
                    update(User)
                    .where(User.user_id == user_id)
                    .values(
                        total_melange=User.total_melange + melange_amount,
                        last_updated=_get_naive_utc_now()
                    )
                )
            await self._log_operation("update", "users", start_time, success=True,
                                    user_id=user_id, melange_amount=melange_amount)
        except Exception as e:
            await self._log_operation("update", "users", start_time, success=False,
                                    user_id=user_id, melange_amount=melange_amount, error=str(e))
            raise e

    async def get_leaderboard(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get leaderboard data from users table"""
        start_time = time.time()
        async with self._get_session() as session:
            try:
                result = await session.execute(
                    select(User)
                    .order_by(User.total_melange.desc(), User.username.asc())
                    .limit(limit)
                )
                users = result.scalars().all()
                leaderboard = [u.to_dict() for u in users]

                await self._log_operation("select", "users", start_time, success=True,
                                        limit=limit, result_count=len(leaderboard))
                return leaderboard
            except Exception as e:
                await self._log_operation("select", "users", start_time, success=False,
                                        limit=limit, error=str(e))
                raise e

    async def reset_all_stats(self):
        """Reset all user statistics and deposits"""
        start_time = time.time()
        try:
            async with self.transaction() as session:
                # Delete in correct order to respect foreign key constraints
                await session.execute(delete(MelangePayment))
                await session.execute(delete(GuildTransaction))
                await session.execute(delete(ExpeditionParticipant))
                await session.execute(delete(Deposit))
                await session.execute(delete(Expedition))
                await session.execute(delete(User))
                await session.execute(delete(GuildTreasury))
                await session.execute(delete(GlobalSetting))

            await self._log_operation("delete_all", "all_tables", start_time, success=True)
            return True
        except Exception as e:
            await self._log_operation("delete_all", "all_tables", start_time, success=False,
                                    error=str(e))
            raise e

    # Add compatibility methods for existing code
    async def get_user_stats(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user statistics including timing information"""
        start_time = time.time()
        async with self._get_session() as session:
            try:
                user = await self.get_user(user_id)
                if not user:
                    return None

                # Get total sand amount
                result = await session.execute(
                    select(func.sum(Deposit.sand_amount))
                    .where(Deposit.user_id == user_id)
                )
                paid_sand = result.scalar() or 0

                stats = {
                    'total_sand': paid_sand,
                    'paid_sand': paid_sand,
                    'total_melange': user['total_melange'],
                    'timing': {'add_deposit_time': 0.1}  # Mock timing for compatibility
                }

                await self._log_operation("select", "user_stats", start_time, success=True, user_id=user_id)
                return stats
            except Exception as e:
                await self._log_operation("select", "user_stats", start_time, success=False, user_id=user_id, error=str(e))
                raise e

    async def get_user_paid_sand(self, user_id: str) -> int:
        """Get total sand from all deposits for a user"""
        start_time = time.time()
        async with self._get_session() as session:
            try:
                result = await session.execute(
                    select(func.coalesce(func.sum(Deposit.sand_amount), 0))
                    .where(Deposit.user_id == user_id)
                )
                total_sand = result.scalar() or 0

                await self._log_operation("select_sum", "deposits", start_time, success=True,
                                        user_id=user_id, total_sand=total_sand)
                return total_sand
            except Exception as e:
                await self._log_operation("select_sum", "deposits", start_time, success=False,
                                        user_id=user_id, error=str(e))
                raise e

    async def get_user_pending_melange(self, user_id: str) -> Dict[str, int]:
        """Get pending melange amount for a user"""
        start_time = time.time()
        async with self._get_session() as session:
            try:
                user = await self.get_user(user_id)
                if user:
                    result = {
                        'total_melange': user['total_melange'],
                        'paid_melange': user['paid_melange'],
                        'pending_melange': user['total_melange'] - user['paid_melange']
                    }
                else:
                    result = {'total_melange': 0, 'paid_melange': 0, 'pending_melange': 0}

                await self._log_operation("select", "users", start_time, success=True,
                                        user_id=user_id, pending_melange=result['pending_melange'])
                return result
            except Exception as e:
                await self._log_operation("select", "users", start_time, success=False,
                                        user_id=user_id, error=str(e))
                raise e

    async def get_guild_transactions_by_expedition_id(self, expedition_id: int) -> List[Dict[str, Any]]:
        """Get all transactions for a specific expedition."""
        start_time = time.time()
        async with self._get_session() as session:
            try:
                result = await session.execute(
                    select(GuildTransaction).where(GuildTransaction.expedition_id == expedition_id)
                )
                transactions = result.scalars().all()
                transaction_list = [t.to_dict() for t in transactions]
                await self._log_operation("select", "guild_transactions", start_time, success=True,
                                        expedition_id=expedition_id, count=len(transaction_list))
                return transaction_list
            except Exception as e:
                await self._log_operation("select", "guild_transactions", start_time, success=False,
                                        expedition_id=expedition_id, error=str(e))
                raise e

    async def get_all_expeditions(self) -> List[Dict[str, Any]]:
        """Get all expeditions."""
        start_time = time.time()
        async with self._get_session() as session:
            try:
                result = await session.execute(select(Expedition))
                expeditions = result.scalars().all()
                expedition_list = [e.to_dict() for e in expeditions]
                await self._log_operation("select", "expeditions", start_time, success=True,
                                        count=len(expedition_list))
                return expedition_list
            except Exception as e:
                await self._log_operation("select", "expeditions", start_time, success=False, error=str(e))
                raise e

    # Add more methods as needed for full compatibility...
    # For now, I'll add placeholder methods that raise NotImplementedError
    # These can be implemented as needed

    async def add_expedition_participant(self, expedition_id: int, user_id: str, username: str,
                                       sand_amount: int, melange_amount: int, is_harvester: bool = False):
        """Add a participant to an expedition"""
        start_time = time.time()
        try:
            async with self.transaction() as session:
                participant = ExpeditionParticipant(
                    expedition_id=expedition_id,
                    user_id=user_id,
                    username=username,
                    sand_amount=sand_amount,
                    melange_amount=melange_amount,
                    is_harvester=is_harvester
                )
                session.add(participant)
            await self._log_operation("insert", "expedition_participants", start_time, success=True,
                                    expedition_id=expedition_id, user_id=user_id)
        except Exception as e:
            await self._log_operation("insert", "expedition_participants", start_time, success=False,
                                    expedition_id=expedition_id, user_id=user_id, error=str(e))
            raise e

    async def add_expedition_deposit(self, user_id: str, username: str, sand_amount: int, expedition_id: int):
        """Add a deposit record for an expedition participant"""
        start_time = time.time()
        try:
            async with self.transaction() as session:
                # Create the deposit record
                deposit = Deposit(
                    user_id=user_id,
                    username=username,
                    sand_amount=sand_amount,
                    type='expedition',
                    expedition_id=expedition_id
                )
                session.add(deposit)
                await session.flush() # To get deposit id
                deposit_id = deposit.id


                # Update user's total melange
                result = await session.execute(
                    select(User).where(User.user_id == user_id)
                )
                user = result.scalar_one_or_none()

                if user:
                    # Calculate melange amount based on current conversion rate
                    from utils.helpers import get_sand_per_melange_with_bonus
                    conversion_rate = await get_sand_per_melange_with_bonus()
                    melange_amount = int(sand_amount / conversion_rate)
                    user.total_melange += melange_amount

            await self._log_operation("insert", "deposits", start_time, success=True,
                                    user_id=user_id, sand_amount=sand_amount, expedition_id=expedition_id)
            return deposit_id

        except Exception as e:
            await self._log_operation("insert", "deposits", start_time, success=False,
                                    user_id=user_id, error=str(e))
            raise e

    async def get_expedition_participants(self, expedition_id: int):
        """Get all participants for a specific expedition with expedition details"""
        start_time = time.time()
        async with self._get_session() as session:
            try:
                # Get expedition details
                expedition_result = await session.execute(
                    select(Expedition).where(Expedition.id == expedition_id)
                )
                expedition = expedition_result.scalar_one_or_none()

                if not expedition:
                    await self._log_operation("select", "expeditions", start_time, success=False,
                                            expedition_id=expedition_id, error="Expedition not found")
                    return None

                # Get participants
                participants_result = await session.execute(
                    select(ExpeditionParticipant)
                    .where(ExpeditionParticipant.expedition_id == expedition_id)
                    .order_by(ExpeditionParticipant.id)
                )
                participants = participants_result.scalars().all()

                expedition_data = expedition.to_dict()
                participants_data = [p.to_dict() for p in participants]

                await self._log_operation("select", "expedition_participants", start_time, success=True,
                                        expedition_id=expedition_id, count=len(participants_data))

                return {
                    'expedition': expedition_data,
                    'participants': participants_data
                }

            except Exception as e:
                await self._log_operation("select", "expedition_participants", start_time, success=False,
                                        expedition_id=expedition_id, error=str(e))
                raise e

    async def get_user_expedition_deposits(self, user_id: str, include_paid: bool = True):
        """Get expedition deposits for a specific user"""
        raise NotImplementedError("Method needs to be implemented")

    async def pay_user_melange(self, user_id: str, username: str, melange_amount: int,
                             admin_user_id: Optional[str] = None, admin_username: Optional[str] = None):
        """Pay melange to a user and record the payment"""
        start_time = time.time()
        try:
            async with self.transaction() as session:
                # Get the user
                result = await session.execute(
                    select(User).where(User.user_id == user_id)
                )
                user = result.scalar_one_or_none()

                if not user:
                    await self._log_operation("select", "users", start_time, success=False,
                                            user_id=user_id, error="User not found")
                    return 0

                # Update user's paid melange
                user.paid_melange += melange_amount

                # Record the payment
                payment = MelangePayment(
                    user_id=user_id,
                    username=username,
                    melange_amount=melange_amount,
                    admin_user_id=admin_user_id,
                    admin_username=admin_username,
                    description=f"Payment of {melange_amount} melange"
                )
                session.add(payment)
            await self._log_operation("update", "users", start_time, success=True,
                                    user_id=user_id, melange_amount=melange_amount)
            return melange_amount
        except Exception as e:
            await self._log_operation("update", "users", start_time, success=False,
                                    user_id=user_id, error=str(e))
            raise e

    async def pay_all_pending_melange(self, admin_user_id: Optional[str] = None, admin_username: Optional[str] = None):
        """Pay all users their pending melange"""
        start_time = time.time()
        try:
            count = 0
            total_paid = 0
            paid_users_details = []
            async with self.transaction() as session:
                # Get all users
                result = await session.execute(select(User))
                users = result.scalars().all()

                for user in users:
                    pending = user.total_melange - user.paid_melange
                    if pending > 0:
                        # Update user's paid melange
                        user.paid_melange += pending

                        # Record the payment
                        payment = MelangePayment(
                            user_id=user.user_id,
                            username=user.username,
                            melange_amount=pending,
                            admin_user_id=admin_user_id,
                            admin_username=admin_username,
                            description=f"Bulk payment of {pending} melange"
                        )
                        session.add(payment)

                        count += 1
                        total_paid += pending
                        paid_users_details.append({'username': user.username, 'amount_paid': pending})

            await self._log_operation("update", "users", start_time, success=True,
                                    count=count, total_paid=total_paid)
            return {'total_paid': total_paid, 'users_paid': count, 'paid_users': paid_users_details}

        except Exception as e:
            await self._log_operation("update", "users", start_time, success=False,
                                    error=str(e))
            raise e

    async def get_all_users_with_pending_melange(self):
        """Get all users with pending melange payments"""
        start_time = time.time()
        async with self._get_session() as session:
            try:
                result = await session.execute(select(User))
                users = result.scalars().all()

                pending_users = []
                for user in users:
                    pending = user.total_melange - user.paid_melange
                    if pending > 0:
                        user_dict = user.to_dict()
                        user_dict['pending_melange'] = pending
                        pending_users.append(user_dict)

                await self._log_operation("select", "users", start_time, success=True,
                                        count=len(pending_users))
                return pending_users

            except Exception as e:
                await self._log_operation("select", "users", start_time, success=False,
                                        error=str(e))
                raise e

    async def cleanup_old_deposits(self, days: int = 30):
        """Remove deposits older than specified days"""
        raise NotImplementedError("Method needs to be implemented")

    async def get_all_unpaid_deposits(self):
        """Get all unpaid deposits across all users"""
        raise NotImplementedError("Method needs to be implemented")

    async def get_global_setting(self, setting_key: str) -> Optional[str]:
        """Get a global setting value by key."""
        start_time = time.time()
        async with self._get_session() as session:
            try:
                result = await session.execute(
                    select(GlobalSetting.setting_value)
                    .where(GlobalSetting.setting_key == setting_key)
                )
                setting = result.scalar_one_or_none()
                await self._log_operation("select", "global_settings", start_time, success=True, key=setting_key)
                return setting
            except Exception as e:
                await self._log_operation("select", "global_settings", start_time, success=False, key=setting_key, error=str(e))
                return None

    async def set_global_setting(self, setting_key: str, setting_value: str, description: Optional[str] = None):
        """Set a global setting."""
        start_time = time.time()
        try:
            async with self.transaction() as session:
                insert_func = sqlite_insert if self.is_sqlite else pg_insert
                stmt = insert_func(GlobalSetting).values(
                    setting_key=setting_key,
                    setting_value=setting_value,
                    description=description
                )
                update_data = {
                    'setting_value': stmt.excluded.setting_value,
                    'last_updated': _get_naive_utc_now()
                }
                if description is not None:
                    update_data['description'] = description

                stmt = stmt.on_conflict_do_update(
                    index_elements=['setting_key'],
                    set_=update_data
                )
                await session.execute(stmt)
            await self._log_operation("upsert", "global_settings", start_time, success=True, key=setting_key)
            return True
        except Exception as e:
            await self._log_operation("upsert", "global_settings", start_time, success=False, key=setting_key, error=str(e))
            raise e

    async def get_all_global_settings(self) -> Dict[str, str]:
        """Get all global settings as a dictionary."""
        start_time = time.time()
        async with self._get_session() as session:
            try:
                result = await session.execute(
                    select(GlobalSetting.setting_key, GlobalSetting.setting_value)
                )
                settings = {key: value for key, value in result}
                await self._log_operation("select_all", "global_settings", start_time, success=True, count=len(settings))
                return settings
            except Exception as e:
                await self._log_operation("select_all", "global_settings", start_time, success=False, error=str(e))
                return {}

    async def add_guild_transaction(self, transaction_type: str, sand_amount: int, melange_amount: int,
                                  expedition_id: Optional[int], admin_user_id: str, admin_username: str,
                                  target_user_id: Optional[str] = None, target_username: Optional[str] = None,
                                  description: Optional[str] = None):
        """Add a guild transaction record."""
        start_time = time.time()
        try:
            async with self.transaction() as session:
                transaction = GuildTransaction(
                    transaction_type=transaction_type,
                    sand_amount=sand_amount,
                    melange_amount=melange_amount,
                    expedition_id=expedition_id,
                    admin_user_id=admin_user_id,
                    admin_username=admin_username,
                    target_user_id=target_user_id,
                    target_username=target_username,
                    description=description
                )
                session.add(transaction)
            await self._log_operation("insert", "guild_transactions", start_time, success=True,
                                    type=transaction_type, admin=admin_user_id)
        except Exception as e:
            await self._log_operation("insert", "guild_transactions", start_time, success=False,
                                    type=transaction_type, admin=admin_user_id, error=str(e))
            raise e

    async def guild_withdraw(self, admin_user_id: str, admin_username: str, target_user_id: str,
                           target_username: str, melange_amount: int) -> int:
        """Withdraw melange from guild treasury, give to user, and return the new treasury balance."""
        start_time = time.time()
        try:
            async with self.transaction() as session:
                # 1. Get guild treasury
                result = await session.execute(
                    select(GuildTreasury).order_by(GuildTreasury.id.desc()).limit(1)
                )
                treasury = result.scalar_one_or_none()

                if not treasury or treasury.total_melange < melange_amount:
                    raise ValueError("Insufficient guild treasury funds.")

                # 2. Get user
                result = await session.execute(
                    select(User).where(User.user_id == target_user_id)
                )
                user = result.scalar_one_or_none()

                if not user:
                    # Create user if not exists
                    await self._upsert_user(session, target_user_id, target_username)
                    result = await session.execute(
                        select(User).where(User.user_id == target_user_id)
                    )
                    user = result.scalar_one()

                # 3. Update balances
                treasury.total_melange -= melange_amount
                user.total_melange += melange_amount

                # 4. Log guild transaction
                guild_tx = GuildTransaction(
                    transaction_type="guild_withdraw",
                    sand_amount=0,
                    melange_amount=melange_amount,
                    admin_user_id=admin_user_id,
                    admin_username=admin_username,
                    target_user_id=target_user_id,
                    target_username=target_username,
                    description=f"Admin {admin_username} withdrew {melange_amount} melange for {target_username}"
                )
                session.add(guild_tx)

                # 5. Log deposit for user
                deposit = Deposit(
                    user_id=target_user_id,
                    username=target_username,
                    sand_amount=0,
                    melange_amount=melange_amount,
                    type="Guild"
                )
                session.add(deposit)

                # Capture the new balance before the transaction commits
                new_treasury_balance = treasury.total_melange

            await self._log_operation("guild_withdraw", "guild_treasury, users, deposits, guild_transactions", start_time, success=True,
                                    admin_user_id=admin_user_id, target_user_id=target_user_id, melange_amount=melange_amount)
            return new_treasury_balance
        except Exception as e:
            await self._log_operation("guild_withdraw", "guild_treasury, users, deposits, guild_transactions", start_time, success=False,
                                    admin_user_id=admin_user_id, target_user_id=target_user_id, melange_amount=melange_amount, error=str(e))
            raise e

    # Compatibility aliases
    async def get_top_refiners(self, limit: int = 10):
        """Get top refiners by melange amount"""
        return await self.get_leaderboard(limit)

    async def get_all_unpaid_users(self):
        """Get all users with unpaid melange"""
        return await self.get_all_users_with_pending_melange()

    async def reset_all_statistics(self):
        """Alias for reset_all_stats for compatibility"""
        return await self.reset_all_stats()
