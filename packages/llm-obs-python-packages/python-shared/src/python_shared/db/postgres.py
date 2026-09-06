import os
import psycopg
from psycopg.rows import dict_row
from typing import Optional

def get_postgres_connection(dsn: Optional[str] = None) -> psycopg.Connection:
    postgres_dsn = dsn or os.getenv("POSTGRES_DSN", "postgresql://postgres:postgres@localhost:5432/platform")
    return psycopg.connect(postgres_dsn, row_factory=dict_row)
