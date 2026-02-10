import datetime
import hashlib
import secrets
from typing import Optional, Dict, Any
import psycopg2
from psycopg2 import pool, extras
from config.settings import POSTGRES_DSN
_pool = None

def _get_pool():
    global _pool
    if _pool is None:
        _pool = psycopg2.pool.ThreadedConnectionPool(minconn=2, maxconn=10, dsn=POSTGRES_DSN)
        _ensure_tables()
    return _pool

def _ensure_tables():
    conn = _pool.getconn()
    try:
        with conn.cursor() as cur:
            cur.execute("\n                CREATE TABLE IF NOT EXISTS api_keys (\n                    id SERIAL PRIMARY KEY,\n                    key_hash VARCHAR(128) UNIQUE NOT NULL,\n                    client_id VARCHAR(255) NOT NULL,\n                    client_name VARCHAR(255) DEFAULT '',\n                    scopes TEXT[] DEFAULT '{}',\n                    active BOOLEAN DEFAULT TRUE,\n                    created_at TIMESTAMPTZ DEFAULT NOW(),\n                    last_used_at TIMESTAMPTZ\n                )\n            ")
            cur.execute('\n                CREATE TABLE IF NOT EXISTS rate_limits (\n                    id SERIAL PRIMARY KEY,\n                    client_id VARCHAR(255) NOT NULL,\n                    window_start TIMESTAMPTZ NOT NULL,\n                    request_count INTEGER DEFAULT 1,\n                    UNIQUE(client_id, window_start)\n                )\n            ')
            cur.execute('\n                CREATE INDEX IF NOT EXISTS idx_rate_limits_client_window\n                ON rate_limits(client_id, window_start)\n            ')
            cur.execute('\n                CREATE INDEX IF NOT EXISTS idx_api_keys_hash\n                ON api_keys(key_hash)\n            ')
        conn.commit()
    finally:
        _pool.putconn(conn)

def _hash_key(api_key: str) -> str:
    return hashlib.sha256(api_key.encode()).hexdigest()

class PostgresAuthStore:

    def __init__(self):
        self._pool = _get_pool()

    def validate_api_key(self, api_key: str) -> Optional[Dict[str, Any]]:
        key_hash = _hash_key(api_key)
        conn = self._pool.getconn()
        try:
            with conn.cursor(cursor_factory=extras.RealDictCursor) as cur:
                cur.execute('SELECT client_id, client_name, scopes, active FROM api_keys WHERE key_hash = %s', (key_hash,))
                row = cur.fetchone()
                if row and row['active']:
                    cur.execute('UPDATE api_keys SET last_used_at = NOW() WHERE key_hash = %s', (key_hash,))
                    conn.commit()
                    return dict(row)
                return None
        finally:
            self._pool.putconn(conn)

    def create_api_key(self, client_id: str, client_name: str='', scopes: list=None) -> str:
        raw_key = f'ak_{secrets.token_urlsafe(32)}'
        key_hash = _hash_key(raw_key)
        conn = self._pool.getconn()
        try:
            with conn.cursor() as cur:
                cur.execute('INSERT INTO api_keys (key_hash, client_id, client_name, scopes) VALUES (%s, %s, %s, %s)', (key_hash, client_id, client_name, scopes or []))
            conn.commit()
            return raw_key
        finally:
            self._pool.putconn(conn)

    def revoke_api_key(self, api_key: str) -> bool:
        key_hash = _hash_key(api_key)
        conn = self._pool.getconn()
        try:
            with conn.cursor() as cur:
                cur.execute('UPDATE api_keys SET active = FALSE WHERE key_hash = %s', (key_hash,))
                affected = cur.rowcount
            conn.commit()
            return affected > 0
        finally:
            self._pool.putconn(conn)

    def check_rate_limit(self, client_id: str, max_requests: int, window_seconds: int) -> Dict[str, Any]:
        now = datetime.datetime.now(datetime.timezone.utc)
        window_start = now.replace(second=now.second // window_seconds * window_seconds if window_seconds <= 60 else 0, microsecond=0)
        conn = self._pool.getconn()
        try:
            with conn.cursor(cursor_factory=extras.RealDictCursor) as cur:
                cur.execute('INSERT INTO rate_limits (client_id, window_start, request_count) VALUES (%s, %s, 1) ON CONFLICT (client_id, window_start) DO UPDATE SET request_count = rate_limits.request_count + 1 RETURNING request_count', (client_id, window_start))
                row = cur.fetchone()
                current_count = row['request_count']
                cur.execute('DELETE FROM rate_limits WHERE window_start < %s', (window_start - datetime.timedelta(seconds=window_seconds * 2),))
            conn.commit()
            remaining = max(0, max_requests - current_count)
            retry_after = window_seconds - (now - window_start).total_seconds()
            return {'allowed': current_count <= max_requests, 'current_count': current_count, 'max_requests': max_requests, 'remaining': remaining, 'retry_after': max(0, retry_after)}
        finally:
            self._pool.putconn(conn)

    def close(self):
        global _pool
        if _pool:
            _pool.closeall()
            _pool = None