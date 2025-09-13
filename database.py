import asyncpg
import asyncio
import os
import time
from datetime import datetime, timedelta
from contextlib import asynccontextmanager
from utils.logger import logger

class Database:
    def __init__(self, database_url=None):
        self.database_url = database_url or os.getenv('DATABASE_URL')
        if not self.database_url:
            raise ValueError("DATABASE_URL environment variable is required")

        # Connection pool settings for better reliability
        self.max_retries = 3
        self.retry_delay = 1.0  # Base delay in seconds

    @asynccontextmanager
    async def _get_connection(self):
        """Context manager for database connections with retry logic"""
        conn = None
        last_error = None

        for attempt in range(self.max_retries):
            start_time = time.time()
            try:
                # Configure connection for Supabase compatibility
                conn = await asyncpg.connect(
                    self.database_url,
                    statement_cache_size=0,  # Disable prepared statements for pgbouncer compatibility
                    command_timeout=30,      # Reduce timeout for faster failures
                    timeout=10,              # Connection timeout in seconds
                    server_settings={
                        'application_name': 'spice_tracker_bot'
                    }
                )

                connection_time = time.time() - start_time
                logger.database_operation(
                    operation="connection_established",
                    table="connection_pool",
                    success=True,
                    attempt=attempt + 1,
                    connection_time=f"{connection_time:.3f}s"
                )

                # Successfully connected, yield and then clean up
                try:
                    yield conn
                    return  # Success, exit retry loop
                finally:
                    # Always close connection in finally block
                    if conn and not conn.is_closed():
                        try:
                            await asyncio.wait_for(conn.close(), timeout=5.0)
                        except (asyncio.TimeoutError, Exception) as close_error:
                            logger.warning(f"Connection close timeout/failure: {close_error}")

            except Exception as e:
                last_error = e
                connection_time = time.time() - start_time
                logger.database_operation(
                    operation="connection_failed",
                    table="connection_pool",
                    success=False,
                    attempt=attempt + 1,
                    connection_time=f"{connection_time:.3f}s",
                    error=str(e)
                )

                # Close failed connection if it exists
                if conn and not conn.is_closed():
                    try:
                        await asyncio.wait_for(conn.close(), timeout=2.0)
                    except Exception:
                        pass  # Ignore close errors on failed connections
                    conn = None

                if attempt < self.max_retries - 1:
                    # Wait before retrying
                    await asyncio.sleep(self.retry_delay * (attempt + 1))
                else:
                    # Final attempt failed, re-raise the error
                    raise last_error

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
        """Test database connectivity only - migrations handled by Supabase CLI"""
        start_time = time.time()
        try:
            async with self._get_connection() as conn:
                # Simple connectivity test
                await conn.fetchval('SELECT 1')

            init_time = time.time() - start_time
            await self._log_operation("connectivity_check", "database", start_time, success=True, init_time=f"{init_time:.3f}s")
            print(f'✅ Database connected in {init_time:.3f}s')

        except Exception as e:
            init_time = time.time() - start_time
            await self._log_operation("connectivity_check", "database", start_time, success=False, init_time=f"{init_time:.3f}s", error=str(e))
            print(f'❌ Database connection failed in {init_time:.3f}s: {e}')
            raise e

    async def get_user(self, user_id):
        """Get user data by user ID"""
        start_time = time.time()
        async with self._get_connection() as conn:
            try:
                row = await conn.fetchrow(
                    'SELECT * FROM users WHERE user_id = $1',
                    user_id
                )
                if row:
                    result = {
                        'user_id': row['user_id'],
                        'username': row['username'],
                        'total_melange': row['total_melange'],
                        'paid_melange': row['paid_melange'],
                        'created_at': row.get('created_at', datetime.now()),
                        'last_updated': row.get('last_updated', datetime.now())
                    }
                    await self._log_operation("select", "users", start_time, success=True, user_id=user_id, found=True)
                    return result
                else:
                    await self._log_operation("select", "users", start_time, success=True, user_id=user_id, found=False)
                    return None
            except Exception as e:
                await self._log_operation("select", "users", start_time, success=False, user_id=user_id, error=str(e))
                raise e

    async def upsert_user(self, user_id, username):
        """Create or update user (without sand amount)"""
        start_time = time.time()
        async with self._get_connection() as conn:
            try:
                await conn.execute('''
                    INSERT INTO users (user_id, username, last_updated)
                    VALUES ($1, $2, CURRENT_TIMESTAMP)
                    ON CONFLICT(user_id) DO UPDATE SET
                        username = EXCLUDED.username,
                        last_updated = CURRENT_TIMESTAMP
                ''', user_id, username)
                await self._log_operation("upsert", "users", start_time, success=True, user_id=user_id, username=username)
            except Exception as e:
                await self._log_operation("upsert", "users", start_time, success=False, user_id=user_id, username=username, error=str(e))
                raise e

    async def add_deposit(self, user_id, username, sand_amount, deposit_type='solo', expedition_id=None):
        """Add a new sand deposit for a user (deposits are for record keeping only)"""
        start_time = time.time()
        async with self._get_connection() as conn:
            try:
                # Ensure user exists
                await self.upsert_user(user_id, username)

                # Add deposit record (for history/audit purposes only)
                await conn.execute('''
                    INSERT INTO deposits (user_id, username, sand_amount, type, expedition_id, created_at)
                    VALUES ($1, $2, $3, $4, $5, CURRENT_TIMESTAMP)
                ''', user_id, username, sand_amount, deposit_type, expedition_id)

                await self._log_operation("insert", "deposits", start_time, success=True,
                                        user_id=user_id, sand_amount=sand_amount, deposit_type=deposit_type, expedition_id=expedition_id)
            except Exception as e:
                await self._log_operation("insert", "deposits", start_time, success=False,
                                        user_id=user_id, sand_amount=sand_amount, deposit_type=deposit_type, expedition_id=expedition_id, error=str(e))
                raise e

    async def get_user_deposits(self, user_id):
        """Get all deposits for a user (deposits are just sand logs, payments are tracked at user level)"""
        start_time = time.time()
        async with self._get_connection() as conn:
            try:
                query = '''
                    SELECT id, user_id, username, sand_amount, type, expedition_id, created_at
                    FROM deposits
                    WHERE user_id = $1
                    ORDER BY created_at DESC
                '''

                rows = await conn.fetch(query, user_id)

                deposits = []
                for row in rows:
                    deposits.append({
                        'id': row['id'],
                        'user_id': row['user_id'],
                        'username': row['username'],
                        'sand_amount': row['sand_amount'],
                        'type': row['type'],
                        'expedition_id': row['expedition_id'],
                        'created_at': row.get('created_at', datetime.now())
                    })

                await self._log_operation("select", "deposits", start_time, success=True,
                                        user_id=user_id, result_count=len(deposits))
                return deposits
            except Exception as e:
                await self._log_operation("select", "deposits", start_time, success=False,
                                        user_id=user_id, error=str(e))
                raise e

    async def create_expedition(self, initiator_id, initiator_username, total_sand, sand_per_melange=None, guild_cut_percentage=10.0):
        """Create a new expedition record"""
        start_time = time.time()
        async with self._get_connection() as conn:
            try:
                row = await conn.fetchrow('''
                    INSERT INTO expeditions (initiator_id, initiator_username, total_sand, sand_per_melange, guild_cut_percentage)
                    VALUES ($1, $2, $3, $4, $5)
                    RETURNING id
                ''', initiator_id, initiator_username, total_sand, sand_per_melange, guild_cut_percentage)

                expedition_id = row['id'] if row else None
                await self._log_operation("insert", "expeditions", start_time, success=True,
                                        initiator_id=initiator_id, total_sand=total_sand, expedition_id=expedition_id, guild_cut_percentage=guild_cut_percentage)
                return expedition_id
            except Exception as e:
                await self._log_operation("insert", "expeditions", start_time, success=False,
                                        initiator_id=initiator_id, total_sand=total_sand, error=str(e))
                raise e

    async def get_guild_treasury(self):
        """Get guild treasury information"""
        start_time = time.time()
        async with self._get_connection() as conn:
            try:
                row = await conn.fetchrow('''
                    SELECT total_sand, total_melange, created_at, last_updated
                    FROM guild_treasury
                    ORDER BY id DESC
                    LIMIT 1
                ''')

                if row:
                    treasury = {
                        'total_sand': row['total_sand'],
                        'total_melange': row['total_melange'],
                        'created_at': row.get('created_at', datetime.now()),
                        'last_updated': row.get('last_updated', datetime.now())
                    }
                else:
                    # Create initial treasury record if none exists
                    await conn.execute('''
                        INSERT INTO guild_treasury (total_sand, total_melange)
                        VALUES ($1, $2)
                    ''', 0, 0)
                    treasury = {'total_sand': 0, 'total_melange': 0, 'created_at': None, 'last_updated': None}

                await self._log_operation("select", "guild_treasury", start_time, success=True)
                return treasury
            except Exception as e:
                await self._log_operation("select", "guild_treasury", start_time, success=False, error=str(e))
                raise e

    async def update_guild_treasury(self, sand_amount, melange_amount=0):
        """Add sand and melange to guild treasury"""
        start_time = time.time()
        async with self._get_connection() as conn:
            try:
                async with conn.transaction():
                    # First try to update existing record
                    result = await conn.execute('''
                        UPDATE guild_treasury
                        SET total_sand = total_sand + $1,
                            total_melange = total_melange + $2,
                            last_updated = CURRENT_TIMESTAMP
                    ''', sand_amount, melange_amount)

                    # If no rows were updated, insert initial record
                    if result == 'UPDATE 0':
                        await conn.execute('''
                            INSERT INTO guild_treasury (total_sand, total_melange)
                            VALUES ($1, $2)
                        ''', sand_amount, melange_amount)

                await self._log_operation("update", "guild_treasury", start_time, success=True,
                                        sand_amount=sand_amount, melange_amount=melange_amount)
                return True
            except Exception as e:
                await self._log_operation("update", "guild_treasury", start_time, success=False,
                                        sand_amount=sand_amount, melange_amount=melange_amount, error=str(e))
                raise e

    async def guild_withdraw(self, admin_user_id, admin_username, target_user_id, target_username, sand_amount):
        """Withdraw sand from guild treasury and give to user"""
        start_time = time.time()
        async with self._get_connection() as conn:
            try:
                # Check if guild has enough sand
                treasury = await self.get_guild_treasury()
                if treasury['total_sand'] < sand_amount:
                    raise ValueError(f"Insufficient guild treasury funds. Available: {treasury['total_sand']}, Requested: {sand_amount}")

                # Start transaction
                async with conn.transaction():
                    # Remove sand from guild treasury
                    await conn.execute('''
                        UPDATE guild_treasury
                        SET total_sand = total_sand - $1,
                            last_updated = CURRENT_TIMESTAMP
                        WHERE id = (SELECT MAX(id) FROM guild_treasury)
                    ''', sand_amount)

                    # Add sand to user as deposit
                    await conn.execute('''
                        INSERT INTO deposits (user_id, username, sand_amount, type, paid, created_at, paid_at)
                        VALUES ($1, $2, $3, 'guild_withdrawal', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    ''', target_user_id, target_username, sand_amount)

                    # Record transaction
                    await conn.execute('''
                        INSERT INTO guild_transactions (transaction_type, sand_amount, admin_user_id, admin_username, target_user_id, target_username, description)
                        VALUES ('withdrawal', $1, $2, $3, $4, $5, $6)
                    ''', sand_amount, admin_user_id, admin_username, target_user_id, target_username, f"Guild withdrawal to {target_username}")

                await self._log_operation("update", "guild_treasury", start_time, success=True,
                                        operation="withdrawal", sand_amount=sand_amount, target_user_id=target_user_id)
                return True
            except Exception as e:
                await self._log_operation("update", "guild_treasury", start_time, success=False,
                                        operation="withdrawal", sand_amount=sand_amount, target_user_id=target_user_id, error=str(e))
                raise e

    async def add_expedition_participant(self, expedition_id, user_id, username, sand_amount, melange_amount, is_harvester=False):
        """Add a participant to an expedition"""
        start_time = time.time()
        async with self._get_connection() as conn:
            try:
                await conn.execute('''
                    INSERT INTO expedition_participants (expedition_id, user_id, username, sand_amount, melange_amount, is_harvester)
                    VALUES ($1, $2, $3, $4, $5, $6)
                ''', expedition_id, user_id, username, sand_amount, melange_amount, is_harvester)

                await self._log_operation("insert", "expedition_participants", start_time, success=True,
                                        expedition_id=expedition_id, user_id=user_id, sand_amount=sand_amount, is_harvester=is_harvester)
            except Exception as e:
                await self._log_operation("insert", "expedition_participants", start_time, success=False,
                                        expedition_id=expedition_id, user_id=user_id, sand_amount=sand_amount, is_harvester=is_harvester, error=str(e))
                raise e

    async def add_expedition_deposit(self, user_id, username, sand_amount, expedition_id):
        """Add a deposit record for an expedition participant"""
        start_time = time.time()
        async with self._get_connection() as conn:
            try:
                # Ensure user exists
                await self.upsert_user(user_id, username)

                # Add deposit record with expedition type
                await conn.execute('''
                    INSERT INTO deposits (user_id, username, sand_amount, type, expedition_id, created_at)
                    VALUES ($1, $2, $3, 'expedition', $4, CURRENT_TIMESTAMP)
                ''', user_id, username, sand_amount, expedition_id)

                await self._log_operation("insert", "deposits", start_time, success=True,
                                        user_id=user_id, sand_amount=sand_amount, expedition_id=expedition_id, type="expedition")
            except Exception as e:
                await self._log_operation("insert", "deposits", start_time, success=False,
                                        user_id=user_id, sand_amount=sand_amount, expedition_id=expedition_id, type="expedition", error=str(e))
                raise e

    async def get_expedition_participants(self, expedition_id):
        """Get all participants for a specific expedition with expedition details"""
        start_time = time.time()
        async with self._get_connection() as conn:
            try:
                # Get expedition details first
                expedition_row = await conn.fetchrow('''
                    SELECT initiator_id, initiator_username, total_sand, guild_cut_percentage,
                           sand_per_melange, created_at
                    FROM expeditions
                    WHERE id = $1
                ''', expedition_id)

                if not expedition_row:
                    return None

                # Get participants
                rows = await conn.fetch('''
                    SELECT * FROM expedition_participants
                    WHERE expedition_id = $1
                    ORDER BY is_harvester DESC, username ASC
                ''', expedition_id)

                participants = []
                for row in rows:
                    participants.append({
                        'id': row['id'],
                        'expedition_id': row['expedition_id'],
                        'user_id': row['user_id'],
                        'username': row['username'],
                        'sand_amount': row['sand_amount'],
                        'melange_amount': row['melange_amount'],
                        'is_harvester': bool(row['is_harvester'])
                    })

                # Combine expedition details with participants
                result = {
                    'expedition': {
                        'id': expedition_id,
                        'initiator_id': expedition_row['initiator_id'],
                        'initiator_username': expedition_row['initiator_username'],
                        'total_sand': expedition_row['total_sand'],
                        'guild_cut_percentage': expedition_row['guild_cut_percentage'] or 0,
                        'sand_per_melange': expedition_row['sand_per_melange'],
                        'created_at': expedition_row.get('created_at', datetime.now())
                    },
                    'participants': participants
                }

                await self._log_operation("select", "expedition_participants", start_time, success=True,
                                        expedition_id=expedition_id, result_count=len(participants))
                return result
            except Exception as e:
                await self._log_operation("select", "expedition_participants", start_time, success=False,
                                        expedition_id=expedition_id, error=str(e))
                raise e

    async def get_user_expedition_deposits(self, user_id, include_paid=True):
        """Get expedition deposits for a specific user"""
        start_time = time.time()
        async with self._get_connection() as conn:
            try:
                query = '''
                    SELECT d.*, e.initiator_username, e.total_sand as expedition_total
                    FROM deposits d
                    LEFT JOIN expeditions e ON d.expedition_id = e.id
                    WHERE d.user_id = $1 AND d.type = 'expedition'
                '''
                params = [user_id]

                if not include_paid:
                    query += ' AND d.paid = FALSE'

                query += ' ORDER BY d.created_at DESC'

                rows = await conn.fetch(query, *params)

                deposits = []
                for row in rows:
                    deposits.append({
                        'id': row['id'],
                        'user_id': row['user_id'],
                        'username': row['username'],
                        'sand_amount': row['sand_amount'],
                        'type': row['type'],
                        'expedition_id': row['expedition_id'],
                        'paid': bool(row['paid']),
                        'created_at': row.get('created_at', datetime.now()),
                        'paid_at': row['paid_at'] if row['paid_at'] else None,
                        'initiator_username': row.get('initiator_username'),
                        'expedition_total': row.get('expedition_total')
                    })

                await self._log_operation("select", "deposits_join_expeditions", start_time, success=True,
                                        user_id=user_id, include_paid=include_paid, result_count=len(deposits))
                return deposits
            except Exception as e:
                await self._log_operation("select", "deposits_join_expeditions", start_time, success=False,
                                        user_id=user_id, include_paid=include_paid, error=str(e))
                raise e



    async def get_user_paid_sand(self, user_id):
        """Get total sand from paid deposits for a user"""
        start_time = time.time()
        async with self._get_connection() as conn:
            try:
                row = await conn.fetchrow('''
                    SELECT COALESCE(SUM(sand_amount), 0) as total_sand
                    FROM deposits
                    WHERE user_id = $1 AND paid = TRUE
                ''', user_id)

                total_sand = row['total_sand'] if row else 0
                await self._log_operation("select_sum", "deposits", start_time, success=True,
                                        user_id=user_id, total_sand=total_sand, paid=True)
                return total_sand
            except Exception as e:
                await self._log_operation("select_sum", "deposits", start_time, success=False,
                                        user_id=user_id, paid=True, error=str(e))
                raise e

    async def pay_user_melange(self, user_id, username, melange_amount, admin_user_id=None, admin_username=None):
        """Pay melange to a user and record the payment"""
        start_time = time.time()
        async with self._get_connection() as conn:
            try:
                async with conn.transaction():
                    # Update user's paid_melange
                    await conn.execute('''
                        UPDATE users
                        SET paid_melange = paid_melange + $1,
                            last_updated = CURRENT_TIMESTAMP
                        WHERE user_id = $2
                    ''', melange_amount, user_id)

                    # Record the payment
                    await conn.execute('''
                        INSERT INTO melange_payments (user_id, username, melange_amount, admin_user_id, admin_username, description)
                        VALUES ($1, $2, $3, $4, $5, $6)
                    ''', user_id, username, melange_amount, admin_user_id, admin_username, f"Melange payment to {username}")

                await self._log_operation("update", "melange_payments", start_time, success=True,
                                        user_id=user_id, melange_amount=melange_amount, admin_user_id=admin_user_id)
                return melange_amount
            except Exception as e:
                await self._log_operation("update", "melange_payments", start_time, success=False,
                                        user_id=user_id, melange_amount=melange_amount, admin_user_id=admin_user_id, error=str(e))
                raise e

    async def pay_all_pending_melange(self, admin_user_id=None, admin_username=None):
        """Pay all users their pending melange"""
        start_time = time.time()
        async with self._get_connection() as conn:
            try:
                # Get all users with pending melange
                users_with_pending = await conn.fetch('''
                    SELECT user_id, username, total_melange, paid_melange,
                           (total_melange - paid_melange) as pending_melange
                    FROM users
                    WHERE total_melange > paid_melange
                ''')

                total_paid = 0
                users_paid = 0

                async with conn.transaction():
                    for user in users_with_pending:
                        pending = user['pending_melange']
                        if pending > 0:
                            # Update user's paid_melange
                            await conn.execute('''
                                UPDATE users
                                SET paid_melange = total_melange,
                                    last_updated = CURRENT_TIMESTAMP
                                WHERE user_id = $1
                            ''', user['user_id'])

                            # Record the payment
                            await conn.execute('''
                                INSERT INTO melange_payments (user_id, username, melange_amount, admin_user_id, admin_username, description)
                                VALUES ($1, $2, $3, $4, $5, $6)
                            ''', user['user_id'], user['username'], pending, admin_user_id, admin_username, f"Bulk melange payment to {user['username']}")

                            total_paid += pending
                            users_paid += 1

                await self._log_operation("update", "melange_payments", start_time, success=True,
                                        total_paid=total_paid, users_paid=users_paid, admin_user_id=admin_user_id)
                return {"total_paid": total_paid, "users_paid": users_paid}
            except Exception as e:
                await self._log_operation("update", "melange_payments", start_time, success=False,
                                        admin_user_id=admin_user_id, error=str(e))
                raise e

    async def get_user_pending_melange(self, user_id):
        """Get pending melange amount for a user"""
        start_time = time.time()
        async with self._get_connection() as conn:
            try:
                row = await conn.fetchrow('''
                    SELECT total_melange, paid_melange,
                           (total_melange - paid_melange) as pending_melange
                    FROM users
                    WHERE user_id = $1
                ''', user_id)

                if row:
                    result = {
                        'total_melange': row['total_melange'],
                        'paid_melange': row['paid_melange'],
                        'pending_melange': row['pending_melange']
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

    async def get_all_users_with_pending_melange(self):
        """Get all users with pending melange payments"""
        start_time = time.time()
        async with self._get_connection() as conn:
            try:
                rows = await conn.fetch('''
                    SELECT u.user_id, u.username, u.total_melange, u.paid_melange,
                           (u.total_melange - u.paid_melange) as pending_melange
                    FROM users u
                    WHERE u.total_melange > u.paid_melange
                    ORDER BY pending_melange DESC, u.username
                ''')

                users = []
                for row in rows:
                    users.append({
                        'user_id': row['user_id'],
                        'username': row['username'],
                        'total_melange': row['total_melange'],
                        'paid_melange': row['paid_melange'],
                        'pending_melange': row['pending_melange']
                    })

                await self._log_operation("select", "users", start_time, success=True,
                                        result_count=len(users))
                return users
            except Exception as e:
                await self._log_operation("select", "users", start_time, success=False, error=str(e))
                raise e

    async def cleanup_old_deposits(self, days=30):
        """Remove deposits older than specified days"""
        start_time = time.time()
        async with self._get_connection() as conn:
            try:
                cutoff_date = datetime.now() - timedelta(days=days)
                result = await conn.execute('''
                    DELETE FROM deposits
                    WHERE created_at < $1 AND paid = TRUE
                ''', cutoff_date)

                # Parse the result string to get the count of deleted rows
                if result:
                    try:
                        # Result format: "DELETE X" where X is the number of rows deleted
                        count_str = result.split()[-1]
                        deleted_count = int(count_str)
                    except (ValueError, IndexError):
                        deleted_count = 0
                else:
                    deleted_count = 0

                await self._log_operation("delete", "deposits", start_time, success=True,
                                        days=days, deleted_count=deleted_count)
                return deleted_count
            except Exception as e:
                await self._log_operation("delete", "deposits", start_time, success=False,
                                        days=days, error=str(e))
                raise e

    async def update_user_melange(self, user_id, melange_amount):
        """Update user melange amount"""
        start_time = time.time()
        async with self._get_connection() as conn:
            try:
                await conn.execute('''
                    UPDATE users
                    SET total_melange = total_melange + $1,
                        last_updated = CURRENT_TIMESTAMP
                    WHERE user_id = $2
                ''', melange_amount, user_id)

                await self._log_operation("update", "users", start_time, success=True,
                                        user_id=user_id, melange_amount=melange_amount)
            except Exception as e:
                await self._log_operation("update", "users", start_time, success=False,
                                        user_id=user_id, melange_amount=melange_amount, error=str(e))
                raise e



    async def get_leaderboard(self, limit=10):
        """Get leaderboard data from users table"""
        start_time = time.time()
        async with self._get_connection() as conn:
            try:
                rows = await conn.fetch('''
                    SELECT username, total_melange
                    FROM users
                    ORDER BY total_melange DESC, username ASC
                    LIMIT $1
                ''', limit)

                result = [dict(row) for row in rows]
                await self._log_operation("select_join", "users_deposits", start_time, success=True,
                                        limit=limit, result_count=len(result))
                return result
            except Exception as e:
                await self._log_operation("select_join", "users_deposits", start_time, success=False,
                                        limit=limit, error=str(e))
                raise e


    async def reset_all_stats(self):
        """Reset all user statistics and deposits (respects foreign key constraints)"""
        start_time = time.time()
        async with self._get_connection() as conn:
            try:
                # Delete in correct order to respect foreign key constraints
                # 1. Leaf tables first (no foreign key dependencies)
                result1 = await conn.execute('DELETE FROM melange_payments')
                result2 = await conn.execute('DELETE FROM guild_transactions')

                # 2. Tables that reference both expeditions and users
                result3 = await conn.execute('DELETE FROM expedition_participants')

                # 3. Tables that reference users or expeditions
                result4 = await conn.execute('DELETE FROM deposits')

                # 4. Expeditions table (references users)
                result5 = await conn.execute('DELETE FROM expeditions')

                # 5. Users table last (root table)
                result6 = await conn.execute('DELETE FROM users')

                # Parse the result strings to get the count of deleted rows
                def parse_delete_result(result):
                    if result:
                        try:
                            # Result format: "DELETE X" where X is the number of rows deleted
                            count_str = result.split()[-1]
                            return int(count_str)
                        except (ValueError, IndexError):
                            return 0
                    return 0

                deleted_count = (parse_delete_result(result1) + parse_delete_result(result2) +
                               parse_delete_result(result3) + parse_delete_result(result4) +
                               parse_delete_result(result5) + parse_delete_result(result6))

                await self._log_operation("delete_all", "all_tables", start_time, success=True,
                                        deleted_count=deleted_count)
                return deleted_count
            except Exception as e:
                await self._log_operation("delete_all", "all_tables", start_time, success=False,
                                        error=str(e))
                raise e

    async def get_all_unpaid_deposits(self):
        """Get all unpaid deposits across all users"""
        start_time = time.time()
        async with self._get_connection() as conn:
            try:
                rows = await conn.fetch('''
                    SELECT d.*, u.total_melange
                    FROM deposits d
                    JOIN users u ON d.user_id = u.user_id
                    WHERE d.paid = FALSE
                    ORDER BY d.created_at ASC
                ''')

                deposits = []
                for row in rows:
                    deposits.append({
                        'id': row['id'],
                        'user_id': row['user_id'],
                        'username': row['username'],
                        'sand_amount': row['sand_amount'],
                        'type': row.get('type', 'solo'),
                        'expedition_id': row.get('expedition_id'),
                        'paid': bool(row.get('paid', False)),
                        'created_at': row.get('created_at', datetime.now()),
                        'paid_at': row.get('paid_at'),
                        'total_melange': row.get('total_melange', 0)
                    })

                await self._log_operation("select_join", "deposits_users", start_time, success=True,
                                        result_count=len(deposits))
                return deposits
            except Exception as e:
                await self._log_operation("select_join", "deposits_users", start_time, success=False,
                                        error=str(e))
                raise e
