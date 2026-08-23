import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import pg from 'pg';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const connectionString =
  process.env.DATABASE_URL ||
  'postgresql://postgres:postgres@localhost:31412/observability_auth';

const pool = new pg.Pool({ connectionString });

async function runMigrations() {
  const client = await pool.connect();
  try {
    await client.query(`
      CREATE TABLE IF NOT EXISTS schema_migrations (
        name VARCHAR(255) PRIMARY KEY,
        applied_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
      );
    `);

    const { rows } = await client.query<{ name: string }>('SELECT name FROM schema_migrations');
    const appliedSet = new Set(rows.map((r) => r.name));

    const migrationsDir = path.join(__dirname, 'migrations');
    const files = fs
      .readdirSync(migrationsDir)
      .filter((f) => f.endsWith('.sql') && !f.endsWith('.rollback.sql'))
      .sort();

    console.log(`[db-migrate] Found ${files.length} migration file(s).`);

    for (const file of files) {
      if (appliedSet.has(file)) {
        console.log(`  - [SKIP] ${file} (already applied)`);
        continue;
      }

      console.log(`  - [APPLYING] ${file}...`);
      const filePath = path.join(migrationsDir, file);
      const sql = fs.readFileSync(filePath, 'utf8');

      await client.query('BEGIN');
      await client.query(sql);
      await client.query('INSERT INTO schema_migrations (name) VALUES ($1)', [file]);
      await client.query('COMMIT');

      console.log(`  - [DONE] ${file}`);
    }

    console.log('[db-migrate] ✓ All database migrations applied successfully.');
  } catch (error) {
    await client.query('ROLLBACK').catch(() => {});
    console.error('[db-migrate] ✗ Migration failed:', error);
    process.exit(1);
  } finally {
    client.release();
    await pool.end();
  }
}

runMigrations();
