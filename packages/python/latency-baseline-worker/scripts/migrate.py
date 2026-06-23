import sys
import clickhouse_connect
from pathlib import Path
from worker.config import load_config

def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: migrate.py [up|rollback]")
        sys.exit(1)
        
    action = sys.argv[1]
    config = load_config()
    
    base_dir = Path(__file__).resolve().parents[1]
    migrations_dir = base_dir / "database" / "migrations"
    lock_file = migrations_dir / "schema.lock"
    
    current_version = 0
    if lock_file.exists():
        content = lock_file.read_text().strip()
        if content:
            current_version = int(content)

    ch_client = clickhouse_connect.get_client(
        host=config.clickhouse_host,
        port=config.clickhouse_port,
        username=config.clickhouse_username,
        password=config.clickhouse_password,
        database=config.clickhouse_database,
    )

    if action == "up":
        if current_version >= 1:
            print("Migration already applied.")
            return
            
        sql_file = migrations_dir / "0001_init.sql"
        ch_sql = sql_file.read_text()
        for statement in ch_sql.split(";"):
            statement = statement.strip()
            if statement:
                ch_client.command(statement)
        
        lock_file.write_text("0001\n")
        print("Migration applied successfully.")
        
    elif action == "rollback":
        if current_version < 1:
            print("Nothing to rollback.")
            return
            
        sql_file = migrations_dir / "0001_init.rollback.sql"
        ch_sql = sql_file.read_text()
        for statement in ch_sql.split(";"):
            statement = statement.strip()
            if statement:
                ch_client.command(statement)
        
        lock_file.write_text("0000\n")
        print("Migration rolled back successfully.")
        
    else:
        print(f"Unknown action: {action}")
        sys.exit(1)

if __name__ == "__main__":
    main()
