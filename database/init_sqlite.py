from pathlib import Path
import sqlite3
import sys


def main() -> None:
    base_dir = Path(__file__).resolve().parent
    db_path = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else base_dir / "furicare.db"
    script_paths = [
        base_dir / "01_schema.sql",
        base_dir / "02_seed.sql",
        base_dir / "03_views_and_queries.sql",
    ]

    with sqlite3.connect(db_path) as conn:
        conn.execute("PRAGMA foreign_keys = ON;")
        for script_path in script_paths:
            conn.executescript(script_path.read_text(encoding="utf-8"))

    print(f"SQLite database initialized: {db_path}")


if __name__ == "__main__":
    main()
