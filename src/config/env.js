import 'dotenv/config';
import { existsSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { z } from 'zod';

const projectRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');

const envSchema = z.object({
  NODE_ENV: z.enum(['development', 'test', 'production']).default('development'),
  HOST: z.string().min(1).default('127.0.0.1'),
  PORT: z.coerce.number().int().min(1).max(65535).default(3000),
  DATABASE_PATH: z.string().min(1).default('database/furicare.db'),
  JWT_SECRET: z.string().min(16, 'JWT_SECRET must be at least 16 characters.'),
  JWT_EXPIRES_IN: z.string().min(1).default('7d'),
  CORS_ORIGIN: z.string().url().default('http://localhost:5173'),
});

export function loadConfig(env = process.env) {
  const parsed = envSchema.safeParse(env);

  if (!parsed.success) {
    throw new Error(`Invalid environment configuration: ${parsed.error.issues.map((issue) => issue.message).join('; ')}`);
  }

  const databasePath = path.resolve(projectRoot, parsed.data.DATABASE_PATH);

  if (!existsSync(databasePath)) {
    throw new Error('Configured SQLite database file does not exist. Run "npm run db:init" first.');
  }

  if (parsed.data.NODE_ENV === 'production' && parsed.data.JWT_SECRET === 'replace-with-a-long-random-secret') {
    throw new Error('JWT_SECRET must be changed before running in production.');
  }

  return Object.freeze({
    nodeEnv: parsed.data.NODE_ENV,
    host: parsed.data.HOST,
    port: parsed.data.PORT,
    databasePath,
    jwtSecret: parsed.data.JWT_SECRET,
    jwtExpiresIn: parsed.data.JWT_EXPIRES_IN,
    corsOrigin: parsed.data.CORS_ORIGIN,
  });
}
