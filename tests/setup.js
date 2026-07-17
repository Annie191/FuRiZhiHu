import { readFileSync } from 'node:fs';
import path from 'node:path';
import Database from 'better-sqlite3';
import { afterEach } from 'vitest';

const databases = [];
const schemaPath = path.resolve('database/01_schema.sql');
const viewsPath = path.resolve('database/03_views_and_queries.sql');
const schema = readFileSync(schemaPath, 'utf8');
const views = readFileSync(viewsPath, 'utf8');

afterEach(() => {
  while (databases.length > 0) {
    const db = databases.pop();
    if (db.open) {
      db.close();
    }
  }
});

export function createTestDatabase() {
  const db = new Database(':memory:');
  db.exec(schema);
  db.exec(views);
  db.pragma('foreign_keys = ON');
  databases.push(db);
  return db;
}

export const testConfig = Object.freeze({
  nodeEnv: 'test',
  corsOrigin: 'http://localhost:5173',
  jwtSecret: 'test-jwt-secret-that-is-long-enough',
  jwtExpiresIn: '1h',
});
