import sys
import psycopg
from pathlib import Path

base_dir = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(base_dir / "src"))

from budget_provisioner.config import load_config

def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: migrate.py [up|rollback]")
        sys.exit(1)
        
    action = sys.argv[1]
    config = load_config()
    
    migrations_dir = base_dir / "database" / "migrations"
    lock_file = migrations_dir / "schema.lock"
    
    current_version = 0
    if lock_file.exists():
        content = lock_file.read_text().strip()
        if content:
            current_version = int(content)

    if action == "up":
        if current_version >= 1:
            print("Migration already applied.")
            return
        sql_file = migrations_dir / "0001_init.sql"
        sql = sql_file.read_text()
        with psycopg.connect(config.postgres_dsn) as conn:
            with conn.cursor() as cur:
                cur.execute(sql)
            conn.commit()
        lock_file.write_text("0001\n")
        print("Migration applied successfully.")
        
    elif action == "rollback":
        if current_version < 1:
            print("Nothing to rollback.")
            return
        sql_file = migrations_dir / "0001_init.rollback.sql"
        sql = sql_file.read_text()
        with psycopg.connect(config.postgres_dsn) as conn:
            with conn.cursor() as cur:
                cur.execute(sql)
            conn.commit()
        lock_file.write_text("0000\n")
        print("Migration rolled back successfully.")
        
    else:
        print(f"Unknown action: {action}")
        sys.exit(1)

if __name__ == "__main__":
    main()
