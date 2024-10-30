import sqlite3
import glob
import os
import importlib.util
import settings  # Import settings to access database configuration

# Use the database name from settings.py
DATABASE = settings.DATABASE_NAME
MIGRATIONS_PATH = 'migrations'

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_migration_table(conn):
    # Ensure that the schema_version table exists
    conn.execute('''
        CREATE TABLE IF NOT EXISTS schema_version (
            version INTEGER PRIMARY KEY,
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    ''')
    conn.commit()

def get_current_version(conn):
    # Get the highest version number in the schema_version table
    cursor = conn.execute("SELECT MAX(version) FROM schema_version")
    row = cursor.fetchone()
    return row[0] if row[0] is not None else 0

def apply_sql_migration(conn, migration_file, version):
    with open(migration_file, 'r') as f:
        sql_script = f.read()
        conn.executescript(sql_script)
        conn.execute("INSERT INTO schema_version (version) VALUES (?)", (version,))
        conn.commit()
    print(f"Applied SQL migration: {migration_file}")

def apply_python_migration(conn, migration_file, version):
    # Load and execute the Python migration file as a module
    spec = importlib.util.spec_from_file_location("migration_module", migration_file)
    migration_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration_module)
    
    # Check if the migration module has a 'migrate' function and execute it
    if hasattr(migration_module, 'migrate'):
        migration_module.migrate(conn)  # Pass the connection to the migration function

    # Update the schema_version after applying migration
    conn.execute("INSERT INTO schema_version (version) VALUES (?)", (version,))
    conn.commit()
    print(f"Applied Python migration: {migration_file}")

def run_migrations():
    conn = get_db()
    init_migration_table(conn)
    current_version = get_current_version(conn)

    # Process SQL and Python migrations in order
    migration_files = sorted(glob.glob(os.path.join(MIGRATIONS_PATH, '*.*')))
    for migration_file in migration_files:
        version = int(os.path.basename(migration_file).split('_')[0])

        if version > current_version:
            if migration_file.endswith('.sql'):
                apply_sql_migration(conn, migration_file, version)
            elif migration_file.endswith('.py'):
                apply_python_migration(conn, migration_file, version)

    conn.close()

if __name__ == "__main__":
    run_migrations()

