import sqlite3, json, os, pathlib

def list_db_files(root: str = '.'):
    db_files = []
    for dirpath, _dirnames, filenames in os.walk(root):
        for f in filenames:
            if f.endswith('.db'):
                full_path = os.path.join(dirpath, f)
                db_files.append(full_path)
    return db_files

def dump_schema(path: str):
    """Return dict of table -> {columns: list, foreign_keys: list}."""
    conn = sqlite3.connect(path)
    cur = conn.cursor()
    tables = [row[0] for row in cur.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()]
    schema = {}
    for t in tables:
        columns = cur.execute(f"PRAGMA table_info('{t}');").fetchall()
        fkeys = cur.execute(f"PRAGMA foreign_key_list('{t}');").fetchall()
        schema[t] = {
            'columns': columns,
            'foreign_keys': fkeys,
        }
    conn.close()
    return schema

def main():
    root = pathlib.Path('.').resolve()
    db_files = list_db_files(root)
    results = {}
    for db_path in db_files:
        try:
            schema = dump_schema(db_path)
            results[db_path] = schema
        except sqlite3.DatabaseError as e:
            results[db_path] = {'error': str(e)}
    print(json.dumps(results, indent=2))

if __name__ == '__main__':
    main() 