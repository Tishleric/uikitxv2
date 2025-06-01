import csv
import sqlite3
import sys
import types
from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def fake_pandas(monkeypatch):
    """Provide a lightweight pandas stub for csv_to_sqlite tests."""

    class FakeDataFrame:
        def __init__(self, rows, columns):
            self.rows = rows
            self.columns = columns

        def to_sql(self, name: str, conn: sqlite3.Connection, if_exists: str = "fail", index: bool = False) -> None:
            if if_exists == "replace":
                conn.execute(f"DROP TABLE IF EXISTS {name}")
            columns_def = ", ".join(f"{c} TEXT" for c in self.columns)
            conn.execute(f"CREATE TABLE {name} ({columns_def})")
            placeholders = ", ".join("?" for _ in self.columns)
            conn.executemany(
                f"INSERT INTO {name} VALUES ({placeholders})",
                self.rows,
            )
            conn.commit()

        def __len__(self) -> int:  # pragma: no cover - simple length
            return len(self.rows)

    fake_pd = types.ModuleType("pandas")

    def read_csv(path: str) -> FakeDataFrame:
        with open(path, newline="") as f:
            reader = csv.reader(f)
            columns = next(reader)
            rows = [tuple(row) for row in reader]
        return FakeDataFrame(rows, columns)

    def read_sql_query(query: str, conn: sqlite3.Connection) -> FakeDataFrame:
        cursor = conn.execute(query)
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        return FakeDataFrame(rows, columns)

    fake_pd.read_csv = read_csv
    fake_pd.read_sql_query = read_sql_query
    fake_pd.DataFrame = FakeDataFrame

    monkeypatch.setitem(sys.modules, "pandas", fake_pd)
    yield
    monkeypatch.delitem(sys.modules, "pandas", raising=False)


def _create_sample_csv(path: Path) -> None:
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "value"])
        writer.writerow(["1", "a"])
        writer.writerow(["2", "b"])


def test_csv_to_sqlite_table(tmp_path: Path) -> None:
    """CSV rows are loaded into a SQLite table."""
    csv_file = tmp_path / "data.csv"
    db_file = tmp_path / "db.sqlite"
    _create_sample_csv(csv_file)

    from trading.ladder.csv_to_sqlite import csv_to_sqlite_table

    result = csv_to_sqlite_table(str(csv_file), str(db_file), "items")
    assert result is True

    conn = sqlite3.connect(db_file)
    count = conn.execute("SELECT COUNT(*) FROM items").fetchone()[0]
    conn.close()
    assert count == 2


def test_get_table_schema(tmp_path: Path) -> None:
    """Schema is returned after table creation."""
    csv_file = tmp_path / "data.csv"
    db_file = tmp_path / "db.sqlite"
    _create_sample_csv(csv_file)
    from trading.ladder.csv_to_sqlite import csv_to_sqlite_table, get_table_schema

    assert csv_to_sqlite_table(str(csv_file), str(db_file), "items")

    schema = get_table_schema(str(db_file), "items")
    assert schema is not None
    assert "CREATE TABLE" in schema
    assert "items" in schema


def test_query_sqlite_table(tmp_path: Path) -> None:
    """Querying the table returns expected rows."""
    csv_file = tmp_path / "data.csv"
    db_file = tmp_path / "db.sqlite"
    _create_sample_csv(csv_file)
    from trading.ladder.csv_to_sqlite import csv_to_sqlite_table, query_sqlite_table

    assert csv_to_sqlite_table(str(csv_file), str(db_file), "items")

    df = query_sqlite_table(
        str(db_file),
        "items",
        columns=["value"],
        where_clause="id = '2'",
    )
    assert len(df) == 1
    assert df.rows[0][0] == "b"

    df_full = query_sqlite_table(str(db_file), "items", query="SELECT id FROM items WHERE value = 'a'")
    assert len(df_full) == 1
    assert df_full.rows[0][0] == "1"
