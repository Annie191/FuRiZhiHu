import Database from 'better-sqlite3';

export function openDatabase({ databasePath }) {
  const db = new Database(databasePath);

  db.pragma('foreign_keys = ON');
  db.pragma('busy_timeout = 5000');

  if (databasePath !== ':memory:') {
    db.pragma('journal_mode = WAL');
  }

  return db;
}
